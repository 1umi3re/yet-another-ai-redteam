from __future__ import annotations
import asyncio, json
from typing import Any
import yaml
from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from sqlalchemy import select
from airedteam.api.deps import AppState, get_state, require_admin
from airedteam.storage.models import Run, Attempt, Score


router = APIRouter()


class CreateRun(BaseModel):
    name: str
    runspec: dict[str, Any]


class RunOut(BaseModel):
    id: str
    name: str
    kind: str
    status: str
    progress_done: int
    progress_total: int
    target_ids: list[str] = []
    target_names: list[str] = []
    error: str | None = None


async def _run_to_out(r: Run, state: AppState) -> RunOut:
    target_ids = _target_ids_for_run(r)
    target_names = []
    for target_id in target_ids:
        target = await state.targets.get(target_id)
        target_names.append(target.name if target is not None else target_id)
    return RunOut(
        id=r.id,
        name=r.name,
        kind=r.kind,
        status=r.status,
        progress_done=r.progress_done,
        progress_total=r.progress_total,
        target_ids=target_ids,
        target_names=target_names,
        error=r.error,
    )


def _target_ids_for_run(r: Run) -> list[str]:
    try:
        spec = json.loads(r.runspec_yaml or "{}") if r.kind == "manual" else yaml.safe_load(r.runspec_yaml or "{}")
    except Exception:
        return []
    if not isinstance(spec, dict):
        return []
    if r.kind == "manual":
        target_id = spec.get("target_id")
        return [target_id] if isinstance(target_id, str) and target_id else []
    ids: list[str] = []
    for target in spec.get("targets") or []:
        if isinstance(target, dict) and isinstance(target.get("config_id"), str):
            ids.append(target["config_id"])
    return ids


@router.post("/runs", status_code=201, response_model=RunOut)
async def create_run(req: CreateRun, _=Depends(require_admin), state: AppState = Depends(get_state)):
    try:
        row = await state.runs.create_run(name=req.name, runspec_dict=req.runspec)
    except Exception as e:
        raise HTTPException(400, f"invalid runspec: {e}")
    return await _run_to_out(row, state)


@router.post("/runs/{rid}/start", status_code=202)
async def start_run(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        if await s.get(Run, rid) is None:
            raise HTTPException(404)
    asyncio.create_task(state.runs.execute_run(rid))
    return {"started": True}


@router.get("/runs", response_model=list[RunOut])
async def list_runs(_=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        rs = (await s.execute(select(Run).order_by(Run.created_at.desc()))).scalars().all()
        return [await _run_to_out(r, state) for r in rs]


@router.get("/runs/{rid}", response_model=RunOut)
async def get_run(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        r = await s.get(Run, rid)
        if r is None: raise HTTPException(404)
        return await _run_to_out(r, state)


@router.get("/runs/{rid}/attempts")
async def list_attempts(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        rows = (await s.execute(select(Attempt).where(Attempt.run_id == rid).order_by(Attempt.created_at))).scalars().all()
        return [{
            "id": a.id, "run_id": a.run_id, "target_id": a.target_id, "target_name": a.target_name, "dataset_item_id": a.dataset_item_id,
            "prompt": a.prompt_text, "response": a.response_text, "response_blob_path": a.response_blob_path,
            "prompt_snapshot_blob_path": a.prompt_snapshot_blob_path,
            "converter_chain": a.converter_chain, "status": a.status, "error": a.error,
            "latency_ms": a.latency_ms, "tokens_in": a.tokens_in, "tokens_out": a.tokens_out,
        } for a in rows]


@router.get("/runs/{rid}/scores")
async def list_scores(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        rows = (await s.execute(
            select(Score, Attempt).join(Attempt, Score.attempt_id == Attempt.id).where(Attempt.run_id == rid)
        )).all()
        return [{
            "id": sc.id,
            "attempt_id": a.id,
            "scorer": sc.scorer,
            "value": sc.value_json,
            "rationale": sc.rationale,
            "prompt_snapshot_blob_path": sc.prompt_snapshot_blob_path,
            "reviewer_label": sc.reviewer_label,
            "reviewer_notes": sc.reviewer_notes,
            "reviewer_id": sc.reviewer_id,
            "reviewed_at": sc.reviewed_at.isoformat() if sc.reviewed_at else None,
        } for sc, a in rows]


@router.get("/runs/{rid}/attempts/{aid}/prompt-snapshot")
async def get_attempt_prompt_snapshot(rid: str, aid: str, _=Depends(require_admin),
                                      state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        a = await s.get(Attempt, aid)
        if a is None or a.run_id != rid or not a.prompt_snapshot_blob_path:
            raise HTTPException(404)
        raw = await state.blob_store.get(a.prompt_snapshot_blob_path)
        return json.loads(raw.decode("utf-8"))


@router.get("/runs/{rid}/scores/{sid}/prompt-snapshot")
async def get_score_prompt_snapshot(rid: str, sid: str, _=Depends(require_admin),
                                    state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        sc = await s.get(Score, sid)
        if sc is None or not sc.prompt_snapshot_blob_path:
            raise HTTPException(404)
        att = await s.get(Attempt, sc.attempt_id)
        if att is None or att.run_id != rid:
            raise HTTPException(404)
        raw = await state.blob_store.get(sc.prompt_snapshot_blob_path)
        return json.loads(raw.decode("utf-8"))


@router.get("/runs/{rid}/events")
async def sse(rid: str, state: AppState = Depends(get_state), token: str = ""):
    from airedteam.api.auth import verify_token
    try:
        verify_token(token, secret=state.settings.jwt_secret)
    except Exception:
        raise HTTPException(401)
    queue = state.bus.subscribe(rid)

    async def event_gen():
        try:
            while True:
                evt = await queue.get()
                yield {"event": evt.get("event", "message"), "data": json.dumps(evt)}
                if evt.get("event") in ("run.finished", "run.failed"):
                    break
        finally:
            state.bus.unsubscribe(rid, queue)

    return EventSourceResponse(event_gen())


@router.get("/runs/{rid}/attempts/{aid}/conversation")
async def get_attempt_conversation(rid: str, aid: str, _=Depends(require_admin),
                                   state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        a = await s.get(Attempt, aid)
        if a is None or a.run_id != rid:
            raise HTTPException(404)
        if not a.conversation_blob_path:
            return {"messages": []}
        raw = await state.blob_store.get(a.conversation_blob_path)
        return json.loads(raw.decode("utf-8"))


class AnnotationIn(BaseModel):
    reviewer_label: bool | None = None
    reviewer_notes: str | None = None


@router.patch("/runs/{rid}/scores/{sid}")
async def annotate_score(rid: str, sid: str, ann: AnnotationIn,
                         admin=Depends(require_admin), state: AppState = Depends(get_state)):
    from datetime import UTC, datetime
    async with state.session_factory() as s:
        sc = await s.get(Score, sid)
        if sc is None:
            raise HTTPException(404)
        att = await s.get(Attempt, sc.attempt_id)
        if att is None or att.run_id != rid:
            raise HTTPException(404)
        sc.reviewer_label = ann.reviewer_label
        sc.reviewer_notes = ann.reviewer_notes
        sc.reviewer_id = admin if isinstance(admin, str) else getattr(admin, "id", "admin")
        sc.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
        await s.commit()
        return {
            "id": sc.id,
            "attempt_id": sc.attempt_id,
            "scorer": sc.scorer,
            "value": sc.value_json,
            "rationale": sc.rationale,
            "reviewer_label": sc.reviewer_label,
            "reviewer_notes": sc.reviewer_notes,
            "reviewer_id": sc.reviewer_id,
            "reviewed_at": sc.reviewed_at.isoformat() if sc.reviewed_at else None,
        }
