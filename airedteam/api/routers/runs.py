from __future__ import annotations
import asyncio, json
from typing import Any
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
    error: str | None = None


def _run_to_out(r: Run) -> RunOut:
    return RunOut(
        id=r.id,
        name=r.name,
        kind=r.kind,
        status=r.status,
        progress_done=r.progress_done,
        progress_total=r.progress_total,
        error=r.error,
    )


@router.post("/runs", status_code=201, response_model=RunOut)
async def create_run(req: CreateRun, _=Depends(require_admin), state: AppState = Depends(get_state)):
    try:
        row = await state.runs.create_run(name=req.name, runspec_dict=req.runspec)
    except Exception as e:
        raise HTTPException(400, f"invalid runspec: {e}")
    return _run_to_out(row)


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
        return [_run_to_out(r) for r in rs]


@router.get("/runs/{rid}", response_model=RunOut)
async def get_run(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        r = await s.get(Run, rid)
        if r is None: raise HTTPException(404)
        return _run_to_out(r)


@router.get("/runs/{rid}/attempts")
async def list_attempts(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        rows = (await s.execute(select(Attempt).where(Attempt.run_id == rid).order_by(Attempt.created_at))).scalars().all()
        return [{
            "id": a.id, "run_id": a.run_id, "target_id": a.target_id, "target_name": a.target_name, "dataset_item_id": a.dataset_item_id,
            "prompt": a.prompt_text, "response": a.response_text, "response_blob_path": a.response_blob_path,
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
            "reviewer_label": sc.reviewer_label,
            "reviewer_notes": sc.reviewer_notes,
            "reviewer_id": sc.reviewer_id,
            "reviewed_at": sc.reviewed_at.isoformat() if sc.reviewed_at else None,
        } for sc, a in rows]


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
