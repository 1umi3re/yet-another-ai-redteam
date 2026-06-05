from __future__ import annotations

import csv
import io
import json
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sse_starlette.sse import EventSourceResponse

from airedteam.api.deps import AppState, get_state, require_admin
from airedteam.core.score_status import score_retryable, score_status
from airedteam.storage.models import Attempt, Run, Score

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


class ResumeRun(BaseModel):
    retry_failed: bool = False


class RetryScores(BaseModel):
    failed_only: bool = True
    score_ids: list[str] | None = None
    attempt_ids: list[str] | None = None
    scorers: list[str] | None = None
    scorer_ref: dict[str, Any] | None = None


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
        raise HTTPException(400, f"invalid runspec: {e}") from e
    return await _run_to_out(row, state)


@router.post("/runs/{rid}/start", status_code=202)
async def start_run(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    try:
        await state.runs.start_run(rid)
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"started": True}


@router.post("/runs/{rid}/cancel", status_code=202)
async def cancel_run(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    try:
        await state.runs.cancel_run(rid)
    except KeyError:
        raise HTTPException(404) from None
    return {"cancelled": True}


@router.post("/runs/{rid}/pause", status_code=202)
async def pause_run(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    try:
        await state.runs.pause_run(rid)
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"paused": True}


@router.post("/runs/{rid}/resume", status_code=202)
async def resume_run(rid: str, req: ResumeRun, _=Depends(require_admin), state: AppState = Depends(get_state)):
    try:
        await state.runs.resume_run(rid, retry_failed=req.retry_failed)
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"resumed": True, "retry_failed": req.retry_failed}


@router.post("/runs/{rid}/scores/retry", status_code=202)
async def retry_scores(rid: str, req: RetryScores, _=Depends(require_admin), state: AppState = Depends(get_state)):
    try:
        return await state.runs.retry_scores(
            rid,
            failed_only=req.failed_only,
            score_ids=req.score_ids,
            attempt_ids=req.attempt_ids,
            scorers=req.scorers,
            scorer_ref=req.scorer_ref,
        )
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/runs", response_model=list[RunOut])
async def list_runs(_=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        rs = (await s.execute(select(Run).order_by(Run.created_at.desc()))).scalars().all()
        return [await _run_to_out(r, state) for r in rs]


@router.get("/runs/{rid}", response_model=RunOut)
async def get_run(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        r = await s.get(Run, rid)
        if r is None:
            raise HTTPException(404)
        return await _run_to_out(r, state)


@router.get("/runs/{rid}/attempts")
async def list_attempts(
    rid: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
    target_id: str | None = None,
    status: str | None = None,
    verdict: str | None = Query(default=None, pattern="^(refused|complied|unscored)$"),
    dataset_item_id: str | None = None,
    converter: str | None = None,
    reviewed: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    paged: bool = False,
):
    async with state.session_factory() as s:
        rows = (
            (await s.execute(select(Attempt).where(Attempt.run_id == rid).order_by(Attempt.created_at))).scalars().all()
        )
        scores = (
            (await s.execute(select(Score).join(Attempt, Score.attempt_id == Attempt.id).where(Attempt.run_id == rid)))
            .scalars()
            .all()
        )
        scores_by_attempt = _scores_by_attempt(scores)
        items = [
            {
                "id": a.id,
                "run_id": a.run_id,
                "target_id": a.target_id,
                "target_name": a.target_name,
                "dataset_item_id": a.dataset_item_id,
                "original_prompt": a.original_prompt_text or a.prompt_text,
                "transformed_prompt": a.prompt_text,
                "prompt": a.prompt_text,
                "response": a.response_text,
                "response_blob_path": a.response_blob_path,
                "prompt_snapshot_blob_path": a.prompt_snapshot_blob_path,
                "converter_chain": a.converter_chain,
                "status": a.status,
                "error": a.error,
                "latency_ms": a.latency_ms,
                "tokens_in": a.tokens_in,
                "tokens_out": a.tokens_out,
                "final_verdict": _attempt_verdict(scores_by_attempt.get(a.id, [])),
                "reviewed": any(sc.reviewer_label is not None for sc in scores_by_attempt.get(a.id, [])),
            }
            for a in rows
        ]
        if target_id:
            items = [a for a in items if a["target_id"] == target_id or a["target_name"] == target_id]
        if status:
            items = [a for a in items if a["status"] == status]
        if verdict:
            items = [a for a in items if a["final_verdict"] == verdict]
        if dataset_item_id:
            items = [a for a in items if a["dataset_item_id"] == dataset_item_id]
        if converter:
            items = [a for a in items if converter in (a["converter_chain"] or [])]
        if reviewed is not None:
            items = [a for a in items if a["reviewed"] is reviewed]
        if not paged:
            return items
        total = len(items)
        return {
            "items": items[offset : offset + limit],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/runs/{rid}/scores")
async def list_scores(
    rid: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
    attempt_id: str | None = None,
    scorer: str | None = None,
    verdict: str | None = Query(default=None, pattern="^(refused|complied)$"),
    reviewed: bool | None = None,
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    paged: bool = False,
):
    async with state.session_factory() as s:
        rows = (
            await s.execute(
                select(Score, Attempt)
                .join(Attempt, Score.attempt_id == Attempt.id)
                .where(Attempt.run_id == rid)
                .order_by(Score.created_at)
            )
        ).all()
        items = [
            {
                "id": sc.id,
                "attempt_id": a.id,
                "scorer": sc.scorer,
                "value": sc.value_json,
                "status": score_status(sc.value_json),
                "retryable": score_retryable(sc.value_json),
                "rationale": sc.rationale,
                "prompt_snapshot_blob_path": sc.prompt_snapshot_blob_path,
                "reviewer_label": sc.reviewer_label,
                "reviewer_notes": sc.reviewer_notes,
                "reviewer_id": sc.reviewer_id,
                "reviewed_at": sc.reviewed_at.isoformat() if sc.reviewed_at else None,
                "final_verdict": _score_verdict(sc),
            }
            for sc, a in rows
        ]
        if attempt_id:
            items = [s for s in items if s["attempt_id"] == attempt_id]
        if scorer:
            items = [s for s in items if s["scorer"] == scorer]
        if verdict:
            items = [s for s in items if s["final_verdict"] == verdict]
        if reviewed is not None:
            items = [s for s in items if (s["reviewer_label"] is not None) is reviewed]
        if not paged:
            return items
        total = len(items)
        return {
            "items": items[offset : offset + limit],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/runs/{rid}/report")
async def get_run_report(rid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    async with state.session_factory() as s:
        run = await s.get(Run, rid)
        if run is None:
            raise HTTPException(404)
        attempts = (
            (await s.execute(select(Attempt).where(Attempt.run_id == rid).order_by(Attempt.created_at))).scalars().all()
        )
        scores = (
            (await s.execute(select(Score).join(Attempt, Score.attempt_id == Attempt.id).where(Attempt.run_id == rid)))
            .scalars()
            .all()
        )
    return _run_report(run, attempts, scores)


@router.get("/runs/{rid}/export")
async def export_run(
    rid: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
    format: str = Query(default="json", pattern="^(json|csv)$"),
):
    async with state.session_factory() as s:
        run = await s.get(Run, rid)
        if run is None:
            raise HTTPException(404)
        attempts = (
            (await s.execute(select(Attempt).where(Attempt.run_id == rid).order_by(Attempt.created_at))).scalars().all()
        )
        scores = (
            (await s.execute(select(Score).join(Attempt, Score.attempt_id == Attempt.id).where(Attempt.run_id == rid)))
            .scalars()
            .all()
        )
    if format == "csv":
        return Response(
            content=_run_export_csv(run, attempts, scores),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="run-{rid}.csv"'},
        )
    return Response(
        content=json.dumps(_run_export_json(run, attempts, scores), ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="run-{rid}.json"'},
    )


@router.get("/runs/{rid}/attempts/{aid}/prompt-snapshot")
async def get_attempt_prompt_snapshot(
    rid: str, aid: str, _=Depends(require_admin), state: AppState = Depends(get_state)
):
    async with state.session_factory() as s:
        a = await s.get(Attempt, aid)
        if a is None or a.run_id != rid or not a.prompt_snapshot_blob_path:
            raise HTTPException(404)
        raw = await state.blob_store.get(a.prompt_snapshot_blob_path)
        return json.loads(raw.decode("utf-8"))


@router.get("/runs/{rid}/scores/{sid}/prompt-snapshot")
async def get_score_prompt_snapshot(rid: str, sid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
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
        raise HTTPException(401) from None
    queue = state.bus.subscribe(rid)

    async def event_gen():
        try:
            while True:
                evt = await queue.get()
                yield {"event": evt.get("event", "message"), "data": json.dumps(evt)}
                if evt.get("event") in ("run.finished", "run.failed", "run.cancelled", "run.paused"):
                    break
        finally:
            state.bus.unsubscribe(rid, queue)

    return EventSourceResponse(event_gen())


@router.get("/runs/{rid}/attempts/{aid}/conversation")
async def get_attempt_conversation(rid: str, aid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
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
async def annotate_score(
    rid: str, sid: str, ann: AnnotationIn, admin=Depends(require_admin), state: AppState = Depends(get_state)
):
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


def _scores_by_attempt(scores: list[Score]) -> dict[str, list[Score]]:
    out: dict[str, list[Score]] = {}
    for score in scores:
        out.setdefault(score.attempt_id, []).append(score)
    for items in out.values():
        items.sort(key=lambda s: s.created_at)
    return out


def _score_verdict(score: Score) -> str | None:
    if score.reviewer_label is not None:
        return "refused" if score.reviewer_label else "complied"
    value = score.value_json or {}
    if score_status(value) == "failed":
        return None
    if isinstance(value.get("attack_success"), bool):
        return "complied" if value["attack_success"] else "refused"
    if isinstance(value.get("label"), bool):
        if score.scorer == "refusal":
            return "refused" if value["label"] else "complied"
        return "complied" if value["label"] else "refused"
    return None


def _attempt_verdict(scores: list[Score]) -> str:
    if not scores:
        return "unscored"
    reviewed = [s for s in scores if s.reviewer_label is not None]
    scored = [s for s in scores if _score_verdict(s) is not None]
    chosen = reviewed[0] if reviewed else scored[0] if scored else scores[0]
    return _score_verdict(chosen) or "unscored"


def _empty_bucket(key: str | None = None) -> dict[str, Any]:
    out = {
        "attempts": 0,
        "scored": 0,
        "unscored": 0,
        "refused": 0,
        "complied": 0,
        "failed": 0,
        "latency_ms": 0,
        "tokens_in": 0,
        "tokens_out": 0,
    }
    if key is not None:
        out["key"] = key
    return out


def _add_attempt(bucket: dict[str, Any], attempt: Attempt, verdict: str) -> None:
    bucket["attempts"] += 1
    bucket["latency_ms"] += attempt.latency_ms or 0
    bucket["tokens_in"] += attempt.tokens_in or 0
    bucket["tokens_out"] += attempt.tokens_out or 0
    if attempt.status == "failed":
        bucket["failed"] += 1
    if verdict == "refused":
        bucket["scored"] += 1
        bucket["refused"] += 1
    elif verdict == "complied":
        bucket["scored"] += 1
        bucket["complied"] += 1
    else:
        bucket["unscored"] += 1


def _finish_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    scored = bucket["scored"]
    bucket["success_rate"] = bucket["complied"] / scored if scored else None
    bucket["refusal_rate"] = bucket["refused"] / scored if scored else None
    return bucket


def _run_report(run: Run, attempts: list[Attempt], scores: list[Score]) -> dict[str, Any]:
    scores_by_attempt = _scores_by_attempt(scores)
    totals = _empty_bucket()
    by_target: dict[str, dict[str, Any]] = {}
    by_chain: dict[str, dict[str, Any]] = {}
    by_target_chain: dict[tuple[str, str], dict[str, Any]] = {}
    by_dataset_item: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        verdict = _attempt_verdict(scores_by_attempt.get(attempt.id, []))
        _add_attempt(totals, attempt, verdict)
        target_key = attempt.target_id or attempt.target_name
        target_bucket = by_target.setdefault(target_key, _empty_bucket(target_key))
        target_bucket["target_id"] = attempt.target_id
        target_bucket["target_name"] = attempt.target_name
        _add_attempt(target_bucket, attempt, verdict)
        chain = attempt.converter_chain or []
        chain_key = " -> ".join(chain) if chain else "(none)"
        chain_bucket = by_chain.setdefault(chain_key, _empty_bucket(chain_key))
        chain_bucket["converter_chain"] = chain
        _add_attempt(chain_bucket, attempt, verdict)
        target_chain_bucket = by_target_chain.setdefault(
            (target_key, chain_key),
            _empty_bucket(f"{target_key}|{chain_key}"),
        )
        target_chain_bucket["target_id"] = attempt.target_id
        target_chain_bucket["target_name"] = attempt.target_name
        target_chain_bucket["converter_chain"] = chain
        _add_attempt(target_chain_bucket, attempt, verdict)
        dataset_key = attempt.dataset_item_id or "(none)"
        dataset_bucket = by_dataset_item.setdefault(dataset_key, _empty_bucket(dataset_key))
        dataset_bucket["dataset_item_id"] = attempt.dataset_item_id
        _add_attempt(dataset_bucket, attempt, verdict)

    by_scorer: dict[str, dict[str, Any]] = {}
    for score in scores:
        bucket = by_scorer.setdefault(
            score.scorer,
            {
                "scorer": score.scorer,
                "scores": 0,
                "refused": 0,
                "complied": 0,
                "unknown": 0,
                "failed": 0,
                "reviewer_overrides": 0,
            },
        )
        bucket["scores"] += 1
        if score.reviewer_label is not None:
            bucket["reviewer_overrides"] += 1
        if score_status(score.value_json) == "failed":
            bucket["failed"] += 1
            continue
        verdict = _score_verdict(score)
        if verdict in ("refused", "complied"):
            bucket[verdict] += 1
        else:
            bucket["unknown"] += 1

    return {
        "run": {
            "id": run.id,
            "name": run.name,
            "kind": run.kind,
            "status": run.status,
            "error": run.error,
        },
        "totals": _finish_bucket(totals),
        "by_target": [_finish_bucket(v) for v in by_target.values()],
        "by_converter_chain": [_finish_bucket(v) for v in by_chain.values()],
        "by_target_chain": [_finish_bucket(v) for v in by_target_chain.values()],
        "by_dataset_item": [_finish_bucket(v) for v in by_dataset_item.values()],
        "by_scorer": list(by_scorer.values()),
    }


def _run_export_json(run: Run, attempts: list[Attempt], scores: list[Score]) -> dict[str, Any]:
    scores_by_attempt = _scores_by_attempt(scores)
    return {
        "run": {
            "id": run.id,
            "name": run.name,
            "kind": run.kind,
            "status": run.status,
            "error": run.error,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        },
        "attempts": [
            {
                "id": a.id,
                "target_id": a.target_id,
                "target_name": a.target_name,
                "dataset_item_id": a.dataset_item_id,
                "original_prompt": a.original_prompt_text or a.prompt_text,
                "transformed_prompt": a.prompt_text,
                "prompt": a.prompt_text,
                "response": a.response_text,
                "response_blob_path": a.response_blob_path,
                "conversation_blob_path": a.conversation_blob_path,
                "prompt_snapshot_blob_path": a.prompt_snapshot_blob_path,
                "converter_chain": a.converter_chain,
                "status": a.status,
                "error": a.error,
                "latency_ms": a.latency_ms,
                "tokens_in": a.tokens_in,
                "tokens_out": a.tokens_out,
                "final_verdict": _attempt_verdict(scores_by_attempt.get(a.id, [])),
                "scores": [_score_export(s) for s in scores_by_attempt.get(a.id, [])],
            }
            for a in attempts
        ],
    }


def _score_export(score: Score) -> dict[str, Any]:
    return {
        "id": score.id,
        "scorer": score.scorer,
        "value": score.value_json,
        "status": score_status(score.value_json),
        "retryable": score_retryable(score.value_json),
        "rationale": score.rationale,
        "prompt_snapshot_blob_path": score.prompt_snapshot_blob_path,
        "reviewer_label": score.reviewer_label,
        "reviewer_notes": score.reviewer_notes,
        "reviewer_id": score.reviewer_id,
        "reviewed_at": score.reviewed_at.isoformat() if score.reviewed_at else None,
        "final_verdict": _score_verdict(score),
    }


def _run_export_csv(run: Run, attempts: list[Attempt], scores: list[Score]) -> str:
    scores_by_attempt = _scores_by_attempt(scores)
    buf = io.StringIO()
    fieldnames = [
        "run_id",
        "run_name",
        "attempt_id",
        "target_id",
        "target_name",
        "dataset_item_id",
        "status",
        "final_verdict",
        "converter_chain",
        "original_prompt",
        "transformed_prompt",
        "response",
        "response_blob_path",
        "conversation_blob_path",
        "prompt_snapshot_blob_path",
        "latency_ms",
        "tokens_in",
        "tokens_out",
        "primary_scorer",
        "primary_score_status",
        "primary_score_value",
        "primary_score_rationale",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for attempt in attempts:
        attempt_scores = scores_by_attempt.get(attempt.id, [])
        primary = next((s for s in attempt_scores if s.reviewer_label is not None), None)
        primary = primary or (attempt_scores[0] if attempt_scores else None)
        writer.writerow(
            {
                "run_id": run.id,
                "run_name": run.name,
                "attempt_id": attempt.id,
                "target_id": attempt.target_id,
                "target_name": attempt.target_name,
                "dataset_item_id": attempt.dataset_item_id,
                "status": attempt.status,
                "final_verdict": _attempt_verdict(attempt_scores),
                "converter_chain": " -> ".join(attempt.converter_chain or []),
                "original_prompt": attempt.original_prompt_text or attempt.prompt_text,
                "transformed_prompt": attempt.prompt_text,
                "response": attempt.response_text,
                "response_blob_path": attempt.response_blob_path,
                "conversation_blob_path": attempt.conversation_blob_path,
                "prompt_snapshot_blob_path": attempt.prompt_snapshot_blob_path,
                "latency_ms": attempt.latency_ms,
                "tokens_in": attempt.tokens_in,
                "tokens_out": attempt.tokens_out,
                "primary_scorer": primary.scorer if primary else "",
                "primary_score_status": score_status(primary.value_json) if primary else "",
                "primary_score_value": json.dumps(primary.value_json, ensure_ascii=False) if primary else "",
                "primary_score_rationale": primary.rationale if primary else "",
            }
        )
    return buf.getvalue()
