from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from html import escape as html_escape
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
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
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
        started_at=_isoformat(r.started_at),
        finished_at=_isoformat(r.finished_at),
        duration_ms=_duration_ms(r.started_at, r.finished_at),
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
async def list_runs(
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
    target_id: str | None = None,
):
    async with state.session_factory() as s:
        rs = (await s.execute(select(Run).order_by(Run.created_at.desc()))).scalars().all()
        if target_id:
            rs = [r for r in rs if target_id in _target_ids_for_run(r)]
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
    executor: str | None = None,
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
        filtered_rows = _filter_attempts(
            rows,
            scores_by_attempt,
            target_id=target_id,
            status=status,
            verdict=verdict,
            dataset_item_id=dataset_item_id,
            converter=converter,
            executor=executor,
            reviewed=reviewed,
        )
        items = [_attempt_item(a, scores_by_attempt) for a in filtered_rows]
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


@router.get("/runs/{rid}/report.html")
async def get_run_html_report(
    rid: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
    lang: str = Query(default="en", pattern="^(en|zh)$"),
):
    async with state.session_factory() as s:
        run = await s.get(Run, rid)
        if run is None:
            raise HTTPException(404)
        if run.kind != "automated":
            raise HTTPException(400, "HTML report export is only available for automated runs")
        attempts = (
            (await s.execute(select(Attempt).where(Attempt.run_id == rid).order_by(Attempt.created_at))).scalars().all()
        )
        scores = (
            (await s.execute(select(Score).join(Attempt, Score.attempt_id == Attempt.id).where(Attempt.run_id == rid)))
            .scalars()
            .all()
        )
    messages_by_attempt = await _messages_by_attempt(state.blob_store, attempts)
    return Response(
        content=_run_report_html(run, attempts, scores, messages_by_attempt, lang=lang),
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="run-{rid}-report.html"'},
    )


@router.get("/runs/{rid}/export")
async def export_run(
    rid: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
    format: str = Query(default="json", pattern="^(json|csv)$"),
    target_id: str | None = None,
    status: str | None = None,
    verdict: str | None = Query(default=None, pattern="^(refused|complied|unscored)$"),
    dataset_item_id: str | None = None,
    converter: str | None = None,
    executor: str | None = None,
    reviewed: bool | None = None,
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
    attempts = _filter_attempts(
        attempts,
        _scores_by_attempt(scores),
        target_id=target_id,
        status=status,
        verdict=verdict,
        dataset_item_id=dataset_item_id,
        converter=converter,
        executor=executor,
        reviewed=reviewed,
    )
    messages_by_attempt = await _messages_by_attempt(state.blob_store, attempts)
    if format == "csv":
        return Response(
            content=_run_export_csv(run, attempts, scores, messages_by_attempt),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="run-{rid}.csv"'},
        )
    return Response(
        content=json.dumps(_run_export_json(run, attempts, scores, messages_by_attempt), ensure_ascii=False),
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


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _duration_ms(started_at: datetime | None, finished_at: datetime | None) -> int | None:
    if started_at is None or finished_at is None:
        return None
    return max(0, int((finished_at - started_at).total_seconds() * 1000))


def _attempt_duration_ms(attempt: Attempt) -> int | None:
    if attempt.duration_ms is not None:
        return attempt.duration_ms
    return _duration_ms(attempt.started_at, attempt.finished_at)


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


def _attempt_item(attempt: Attempt, scores_by_attempt: dict[str, list[Score]]) -> dict[str, Any]:
    scores = scores_by_attempt.get(attempt.id, [])
    return {
        "id": attempt.id,
        "run_id": attempt.run_id,
        "target_id": attempt.target_id,
        "target_name": attempt.target_name,
        "dataset_item_id": attempt.dataset_item_id,
        "original_prompt": attempt.original_prompt_text or attempt.prompt_text,
        "transformed_prompt": attempt.prompt_text,
        "prompt": attempt.prompt_text,
        "response": attempt.response_text,
        "response_blob_path": attempt.response_blob_path,
        "prompt_snapshot_blob_path": attempt.prompt_snapshot_blob_path,
        "converter_chain": attempt.converter_chain,
        "executor_name": _attempt_executor_name(attempt),
        "executor_kind": _attempt_executor_kind(attempt),
        "dataset_item_language": attempt.dataset_item_language,
        "status": attempt.status,
        "error": attempt.error,
        "started_at": _isoformat(attempt.started_at),
        "finished_at": _isoformat(attempt.finished_at),
        "duration_ms": _attempt_duration_ms(attempt),
        "latency_ms": attempt.latency_ms,
        "tokens_in": attempt.tokens_in,
        "tokens_out": attempt.tokens_out,
        "final_verdict": _attempt_verdict(scores),
        "reviewed": any(score.reviewer_label is not None for score in scores),
    }


def _filter_attempts(
    attempts: list[Attempt],
    scores_by_attempt: dict[str, list[Score]],
    *,
    target_id: str | None = None,
    status: str | None = None,
    verdict: str | None = None,
    dataset_item_id: str | None = None,
    converter: str | None = None,
    executor: str | None = None,
    reviewed: bool | None = None,
) -> list[Attempt]:
    return [
        attempt
        for attempt in attempts
        if _attempt_matches_filters(
            attempt,
            scores_by_attempt.get(attempt.id, []),
            target_id=target_id,
            status=status,
            verdict=verdict,
            dataset_item_id=dataset_item_id,
            converter=converter,
            executor=executor,
            reviewed=reviewed,
        )
    ]


def _attempt_matches_filters(
    attempt: Attempt,
    scores: list[Score],
    *,
    target_id: str | None,
    status: str | None,
    verdict: str | None,
    dataset_item_id: str | None,
    converter: str | None,
    executor: str | None,
    reviewed: bool | None,
) -> bool:
    if target_id and attempt.target_id != target_id and attempt.target_name != target_id:
        return False
    if status and attempt.status != status:
        return False
    if verdict and _attempt_verdict(scores) != verdict:
        return False
    if dataset_item_id and attempt.dataset_item_id != dataset_item_id:
        return False
    if converter:
        chain = attempt.converter_chain or []
        if not (converter == "(none)" and not chain or converter in chain or converter == " -> ".join(chain)):
            return False
    if executor and _attempt_executor_name(attempt) != executor:
        return False
    if reviewed is not None and any(score.reviewer_label is not None for score in scores) is not reviewed:
        return False
    return True


def _empty_bucket(key: str | None = None) -> dict[str, Any]:
    out = {
        "attempts": 0,
        "scored": 0,
        "unscored": 0,
        "refused": 0,
        "complied": 0,
        "failed": 0,
        "duration_ms": 0,
        "latency_ms": 0,
        "tokens_in": 0,
        "tokens_out": 0,
    }
    if key is not None:
        out["key"] = key
    return out


def _attempt_executor_name(attempt: Attempt) -> str:
    if attempt.executor_name:
        return attempt.executor_name
    chain = attempt.converter_chain or []
    if chain:
        return " -> ".join(chain)
    return "single_turn"


def _attempt_executor_kind(attempt: Attempt) -> str:
    if attempt.executor_kind:
        return attempt.executor_kind
    return "converter_method" if attempt.converter_chain else "executor"


def _add_attempt(bucket: dict[str, Any], attempt: Attempt, verdict: str) -> None:
    bucket["attempts"] += 1
    bucket["latency_ms"] += attempt.latency_ms or 0
    bucket["tokens_in"] += attempt.tokens_in or 0
    bucket["tokens_out"] += attempt.tokens_out or 0
    if attempt.status == "failed":
        bucket["failed"] += 1
    bucket["duration_ms"] += _attempt_duration_ms(attempt) or 0
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
    by_executor: dict[str, dict[str, Any]] = {}
    by_target_executor: dict[tuple[str, str], dict[str, Any]] = {}
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
        executor_name = _attempt_executor_name(attempt)
        executor_bucket = by_executor.setdefault(executor_name, _empty_bucket(executor_name))
        executor_bucket["executor_name"] = executor_name
        executor_bucket["executor_kind"] = _attempt_executor_kind(attempt)
        _add_attempt(executor_bucket, attempt, verdict)
        target_executor_bucket = by_target_executor.setdefault(
            (target_key, executor_name),
            _empty_bucket(f"{target_key}|{executor_name}"),
        )
        target_executor_bucket["target_id"] = attempt.target_id
        target_executor_bucket["target_name"] = attempt.target_name
        target_executor_bucket["executor_name"] = executor_name
        target_executor_bucket["executor_kind"] = _attempt_executor_kind(attempt)
        _add_attempt(target_executor_bucket, attempt, verdict)
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

    filtered_items = []
    if isinstance(run.filtered_json, dict):
        filtered_items = list(run.filtered_json.get("by_language") or [])
    filtered_summary: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in filtered_items:
        key = (
            str(item.get("target_name") or ""),
            str(item.get("executor_name") or ""),
            str(item.get("language") or ""),
        )
        bucket = filtered_summary.setdefault(
            key,
            {
                "target_name": key[0],
                "executor_name": key[1],
                "executor_kind": item.get("executor_kind"),
                "language": key[2],
                "filtered": 0,
            },
        )
        bucket["filtered"] += 1

    return {
        "run": {
            "id": run.id,
            "name": run.name,
            "kind": run.kind,
            "status": run.status,
            "error": run.error,
            "started_at": _isoformat(run.started_at),
            "finished_at": _isoformat(run.finished_at),
            "duration_ms": _duration_ms(run.started_at, run.finished_at),
        },
        "totals": _finish_bucket(totals),
        "by_target": [_finish_bucket(v) for v in by_target.values()],
        "by_converter_chain": [_finish_bucket(v) for v in by_chain.values()],
        "by_target_chain": [_finish_bucket(v) for v in by_target_chain.values()],
        "by_executor": [_finish_bucket(v) for v in by_executor.values()],
        "by_target_executor": [_finish_bucket(v) for v in by_target_executor.values()],
        "by_dataset_item": [_finish_bucket(v) for v in by_dataset_item.values()],
        "by_scorer": list(by_scorer.values()),
        "filtered_by_language": list(filtered_summary.values()),
    }


_HTML_REPORT_TEXT = {
    "en": {
        "title": "Automated Test Report",
        "summary": "Summary",
        "run": "Run",
        "status": "Status",
        "started": "Started",
        "finished": "Finished",
        "duration": "Duration",
        "attempts": "Attempts",
        "effective_scores": "Effective scores",
        "attack_success_rate": "Attack success rate",
        "attack_successes": "Attack successes",
        "refused": "Refused",
        "failed": "Failed",
        "unscored": "Unscored",
        "target_ranking": "Target Risk Ranking",
        "method_ranking": "Attack Method Risk Ranking",
        "combination_ranking": "Target x Attack Method Ranking",
        "scorer_summary": "Scorer Summary",
        "filtered_summary": "Filtered Language Summary",
        "representative_samples": "Representative Samples",
        "attention_records": "Records Needing Attention",
        "target": "Target",
        "method": "Attack method",
        "success_rate": "Success rate",
        "scored": "Scored",
        "scorer": "Scorer",
        "scores": "Scores",
        "unknown": "Unknown",
        "reviewer_overrides": "Reviewer overrides",
        "language": "Language",
        "filtered": "Filtered",
        "attempt_id": "Attempt ID",
        "verdict": "Verdict",
        "original_prompt": "Original prompt",
        "transformed_prompt": "Transformed prompt",
        "response": "Response",
        "conversation": "Conversation",
        "message": "Message",
        "rationale": "Rationale",
        "no_data": "No data.",
    },
    "zh": {
        "title": "自动化测试报告",
        "summary": "概览",
        "run": "任务",
        "status": "状态",
        "started": "开始时间",
        "finished": "结束时间",
        "duration": "耗时",
        "attempts": "尝试次数",
        "effective_scores": "有效评分",
        "attack_success_rate": "攻击成功率",
        "attack_successes": "攻击成功数",
        "refused": "拒答数",
        "failed": "失败数",
        "unscored": "未评分数",
        "target_ranking": "目标风险排行",
        "method_ranking": "攻击方法风险排行",
        "combination_ranking": "目标 x 攻击方法排行",
        "scorer_summary": "评分器概况",
        "filtered_summary": "语言过滤摘要",
        "representative_samples": "代表性样例",
        "attention_records": "需关注记录",
        "target": "目标",
        "method": "攻击方法",
        "success_rate": "成功率",
        "scored": "已评分",
        "scorer": "评分器",
        "scores": "评分数",
        "unknown": "未知",
        "reviewer_overrides": "人工复核",
        "language": "语言",
        "filtered": "过滤数",
        "attempt_id": "尝试 ID",
        "verdict": "结论",
        "original_prompt": "原始提示词",
        "transformed_prompt": "变换后提示词",
        "response": "模型响应",
        "conversation": "完整对话",
        "message": "消息",
        "rationale": "评分理由",
        "no_data": "暂无数据。",
    },
}


def _run_report_html(
    run: Run,
    attempts: list[Attempt],
    scores: list[Score],
    messages_by_attempt: dict[str, list[dict[str, Any]]],
    *,
    lang: str,
) -> str:
    labels = _HTML_REPORT_TEXT.get(lang, _HTML_REPORT_TEXT["en"])
    report = _run_report(run, attempts, scores)
    scores_by_attempt = _scores_by_attempt(scores)
    samples = _representative_html_samples(report, attempts, scores_by_attempt)
    attention = _attention_html_samples(attempts, scores_by_attempt)
    lang_attr = "zh-Hans" if lang == "zh" else "en"
    body = "\n".join(
        [
            _html_report_header(labels, report),
            _html_report_summary(labels, report),
            _html_bucket_table(
                labels["target_ranking"],
                report["by_target"],
                [
                    (labels["target"], lambda row: row.get("target_name") or row.get("key")),
                    (labels["success_rate"], lambda row: _format_rate(row.get("success_rate"))),
                    (labels["attack_successes"], lambda row: row.get("complied")),
                    (labels["refused"], lambda row: row.get("refused")),
                    (labels["failed"], lambda row: row.get("failed")),
                    (labels["unscored"], lambda row: row.get("unscored")),
                ],
                labels,
            ),
            _html_bucket_table(
                labels["method_ranking"],
                report["by_executor"],
                [
                    (labels["method"], lambda row: row.get("executor_name") or row.get("key")),
                    (labels["success_rate"], lambda row: _format_rate(row.get("success_rate"))),
                    (labels["attack_successes"], lambda row: row.get("complied")),
                    (labels["refused"], lambda row: row.get("refused")),
                    (labels["failed"], lambda row: row.get("failed")),
                    (labels["unscored"], lambda row: row.get("unscored")),
                ],
                labels,
            ),
            _html_bucket_table(
                labels["combination_ranking"],
                report["by_target_executor"],
                [
                    (labels["target"], lambda row: row.get("target_name") or row.get("key")),
                    (labels["method"], lambda row: row.get("executor_name")),
                    (labels["success_rate"], lambda row: _format_rate(row.get("success_rate"))),
                    (labels["scored"], lambda row: row.get("scored")),
                    (labels["attack_successes"], lambda row: row.get("complied")),
                    (labels["failed"], lambda row: row.get("failed")),
                    (labels["unscored"], lambda row: row.get("unscored")),
                ],
                labels,
            ),
            _html_scorer_table(labels, report["by_scorer"]),
            _html_filtered_table(labels, report["filtered_by_language"]),
            _html_samples_section(
                labels["representative_samples"],
                samples,
                scores_by_attempt,
                messages_by_attempt,
                labels,
            ),
            _html_samples_section(
                labels["attention_records"],
                attention,
                scores_by_attempt,
                messages_by_attempt,
                labels,
            ),
        ]
    )
    return f"""<!doctype html>
<html lang="{lang_attr}">
<head>
  <meta charset="utf-8">
  <title>{_h(labels["title"])} - {_h(run.name)}</title>
  <style>
    :root {{
      color-scheme: light;
      --text: #17202a;
      --muted: #667085;
      --line: #d8dee8;
      --soft: #f6f8fb;
      --risk: #b42318;
      --ok: #067647;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: #fff;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px 24px 56px; }}
    header {{ border-bottom: 2px solid var(--text); padding-bottom: 18px; margin-bottom: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.15; }}
    h2 {{ margin: 30px 0 12px; font-size: 20px; }}
    h3 {{ margin: 18px 0 8px; font-size: 16px; }}
    h4 {{ margin: 0 0 8px; font-size: 14px; }}
    .muted {{ color: var(--muted); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: var(--soft); }}
    .metric .label {{ color: var(--muted); font-size: 12px; }}
    .metric .value {{ margin-top: 4px; font-size: 22px; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: var(--soft); color: var(--muted); font-weight: 700; }}
    .sample {{
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 12px 0;
      padding: 14px;
      page-break-inside: avoid;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 14px;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 10px;
    }}
    .field {{ margin: 10px 0; }}
    .field-title {{ color: var(--muted); font-size: 12px; font-weight: 700; margin-bottom: 4px; }}
    pre {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      margin: 0;
      padding: 10px;
      border-radius: 6px;
      background: #f2f4f7;
      font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}
    .badge-risk {{ color: var(--risk); font-weight: 700; }}
    .badge-ok {{ color: var(--ok); font-weight: 700; }}
    @media print {{ main {{ max-width: none; padding: 18px; }} .sample {{ break-inside: avoid; }} }}
  </style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def _representative_html_samples(
    report: dict[str, Any],
    attempts: list[Attempt],
    scores_by_attempt: dict[str, list[Score]],
) -> list[Attempt]:
    out: list[Attempt] = []
    selected_groups = 0
    rows = sorted(report["by_target_executor"], key=_risk_row_sort_key)
    sorted_attempts = sorted(attempts, key=_attempt_time_sort_key)
    for row in rows:
        if (row.get("complied") or 0) <= 0:
            continue
        group = [
            attempt
            for attempt in sorted_attempts
            if _attempt_matches_target_executor_row(attempt, row)
            and _attempt_verdict(scores_by_attempt.get(attempt.id, [])) == "complied"
        ][:3]
        if not group:
            continue
        out.extend(group)
        selected_groups += 1
        if selected_groups >= 10:
            break
    return out


def _attention_html_samples(attempts: list[Attempt], scores_by_attempt: dict[str, list[Score]]) -> list[Attempt]:
    return [
        attempt
        for attempt in sorted(attempts, key=_attempt_time_sort_key)
        if attempt.status == "failed" or _attempt_verdict(scores_by_attempt.get(attempt.id, [])) == "unscored"
    ][:10]


def _risk_row_sort_key(row: dict[str, Any]) -> tuple[float, int, int, str, str]:
    rate = row.get("success_rate")
    rate_key = rate if isinstance(rate, int | float) else -1
    return (
        -float(rate_key),
        -(row.get("scored") or 0),
        -(row.get("complied") or 0),
        str(row.get("target_name") or row.get("key") or ""),
        str(row.get("executor_name") or ""),
    )


def _attempt_time_sort_key(attempt: Attempt) -> tuple[datetime, str]:
    return (attempt.started_at or attempt.created_at or datetime.min, attempt.id)


def _attempt_matches_target_executor_row(attempt: Attempt, row: dict[str, Any]) -> bool:
    if row.get("target_id") is not None and attempt.target_id != row.get("target_id"):
        return False
    if (
        row.get("target_id") is None
        and row.get("target_name") is not None
        and attempt.target_name != row.get("target_name")
    ):
        return False
    return _attempt_executor_name(attempt) == row.get("executor_name")


def _html_report_header(labels: dict[str, str], report: dict[str, Any]) -> str:
    run = report["run"]
    return f"""<header>
  <h1>{_h(labels["title"])}</h1>
  <div class="muted">{_h(labels["run"])}: {_h(run["name"])} · {_h(run["id"])}</div>
  <div class="muted">
    {_h(labels["status"])}: {_h(run["status"])} ·
    {_h(labels["started"])}: {_h(run["started_at"] or "-")} ·
    {_h(labels["finished"])}: {_h(run["finished_at"] or "-")} ·
    {_h(labels["duration"])}: {_h(_format_duration(run["duration_ms"]))}
  </div>
</header>"""


def _html_report_summary(labels: dict[str, str], report: dict[str, Any]) -> str:
    totals = report["totals"]
    cards = [
        (labels["attack_success_rate"], _format_rate(totals.get("success_rate"))),
        (labels["attack_successes"], totals.get("complied")),
        (labels["refused"], totals.get("refused")),
        (labels["effective_scores"], f"{totals.get('scored', 0)}/{totals.get('attempts', 0)}"),
        (labels["failed"], totals.get("failed")),
        (labels["unscored"], totals.get("unscored")),
    ]
    return "<section><h2>{}</h2><div class=\"grid\">{}</div></section>".format(
        _h(labels["summary"]),
        "\n".join(
            f'<div class="metric"><div class="label">{_h(label)}</div><div class="value">{_h(value)}</div></div>'
            for label, value in cards
        ),
    )


def _html_bucket_table(
    title: str,
    rows: list[dict[str, Any]],
    columns: list[tuple[str, Any]],
    labels: dict[str, str],
) -> str:
    sorted_rows = sorted(rows, key=_risk_row_sort_key)[:20]
    if not sorted_rows:
        return f'<section><h2>{_h(title)}</h2><p class="muted">{_h(labels["no_data"])}</p></section>'
    head = "".join(f"<th>{_h(label)}</th>" for label, _getter in columns)
    body = "\n".join(
        "<tr>{}</tr>".format("".join(f"<td>{_h(getter(row))}</td>" for _label, getter in columns))
        for row in sorted_rows
    )
    return f"<section><h2>{_h(title)}</h2><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></section>"


def _html_scorer_table(labels: dict[str, str], rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f'<section><h2>{_h(labels["scorer_summary"])}</h2><p class="muted">{_h(labels["no_data"])}</p></section>'
    columns = [
        (labels["scorer"], lambda row: row.get("scorer")),
        (labels["scores"], lambda row: row.get("scores")),
        (labels["refused"], lambda row: row.get("refused")),
        (labels["attack_successes"], lambda row: row.get("complied")),
        (labels["failed"], lambda row: row.get("failed")),
        (labels["unknown"], lambda row: row.get("unknown")),
        (labels["reviewer_overrides"], lambda row: row.get("reviewer_overrides")),
    ]
    head = "".join(f"<th>{_h(label)}</th>" for label, _getter in columns)
    body = "\n".join(
        "<tr>{}</tr>".format("".join(f"<td>{_h(getter(row))}</td>" for _label, getter in columns))
        for row in sorted(rows, key=lambda item: str(item.get("scorer") or ""))
    )
    return (
        f'<section><h2>{_h(labels["scorer_summary"])}</h2>'
        f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></section>"
    )


def _html_filtered_table(labels: dict[str, str], rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    columns = [
        (labels["target"], lambda row: row.get("target_name")),
        (labels["method"], lambda row: row.get("executor_name")),
        (labels["language"], lambda row: row.get("language")),
        (labels["filtered"], lambda row: row.get("filtered")),
    ]
    head = "".join(f"<th>{_h(label)}</th>" for label, _getter in columns)
    body = "\n".join(
        "<tr>{}</tr>".format("".join(f"<td>{_h(getter(row))}</td>" for _label, getter in columns))
        for row in rows
    )
    return (
        f'<section><h2>{_h(labels["filtered_summary"])}</h2>'
        f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></section>"
    )


def _html_samples_section(
    title: str,
    attempts: list[Attempt],
    scores_by_attempt: dict[str, list[Score]],
    messages_by_attempt: dict[str, list[dict[str, Any]]],
    labels: dict[str, str],
) -> str:
    if not attempts:
        return f'<section><h2>{_h(title)}</h2><p class="muted">{_h(labels["no_data"])}</p></section>'
    items = "\n".join(
        _html_attempt_sample(
            attempt,
            scores_by_attempt.get(attempt.id, []),
            messages_by_attempt.get(attempt.id, []),
            labels,
        )
        for attempt in attempts
    )
    return f"<section><h2>{_h(title)}</h2>{items}</section>"


def _html_attempt_sample(
    attempt: Attempt,
    scores: list[Score],
    messages: list[dict[str, Any]],
    labels: dict[str, str],
) -> str:
    verdict = _attempt_verdict(scores)
    verdict_class = "badge-risk" if verdict == "complied" else "badge-ok" if verdict == "refused" else ""
    score = next((item for item in scores if item.reviewer_label is not None), None) or (scores[0] if scores else None)
    score_html = ""
    if score is not None:
        score_html = _html_text_block(
            f'{labels["scorer"]}: {score.scorer} · {labels["rationale"]}',
            score.rationale or json.dumps(score.value_json, ensure_ascii=False),
        )
    if messages:
        body = "\n".join(
            _html_text_block(
                f'{labels["message"]}: {message.get("role", "")}',
                str(message.get("text", "")),
            )
            for message in messages
            if isinstance(message, dict)
        )
    else:
        body = "\n".join(
            [
                _html_text_block(labels["original_prompt"], attempt.original_prompt_text or attempt.prompt_text),
                _html_text_block(labels["transformed_prompt"], attempt.prompt_text),
                _html_text_block(labels["response"], attempt.response_text or ""),
            ]
        )
    return f"""<article class="sample">
  <h3>{_h(attempt.target_name or attempt.target_id)} · {_h(_attempt_executor_name(attempt))}</h3>
  <div class="meta">
    <span>{_h(labels["attempt_id"])}: {_h(attempt.id)}</span>
    <span>{_h(labels["status"])}: {_h(attempt.status)}</span>
    <span>{_h(labels["verdict"])}: <strong class="{verdict_class}">{_h(verdict)}</strong></span>
  </div>
  {body}
  {score_html}
</article>"""


def _html_text_block(title: str, text: str) -> str:
    return f'<div class="field"><div class="field-title">{_h(title)}</div><pre>{_h(text)}</pre></div>'


def _format_rate(value: Any) -> str:
    if not isinstance(value, int | float):
        return "-"
    return f"{round(float(value) * 100)}%"


def _format_duration(value: Any) -> str:
    if not isinstance(value, int | float):
        return "-"
    if value < 1000:
        return f"{int(value)} ms"
    seconds = float(value) / 1000
    if seconds < 60:
        return f"{seconds:.1f} s" if seconds < 10 else f"{seconds:.0f} s"
    minutes = int(seconds // 60)
    return f"{minutes}m {round(seconds % 60)}s"


def _h(value: Any) -> str:
    return html_escape("" if value is None else str(value), quote=True)


async def _messages_by_attempt(blob_store, attempts: list[Attempt]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempts:
        messages: list[dict[str, Any]] = []
        if attempt.conversation_blob_path:
            raw = await blob_store.get(attempt.conversation_blob_path)
            payload = json.loads(raw.decode("utf-8"))
            raw_messages = payload.get("messages") if isinstance(payload, dict) else None
            if isinstance(raw_messages, list):
                messages = [message for message in raw_messages if isinstance(message, dict)]
        out[attempt.id] = messages
    return out


def _run_export_json(
    run: Run,
    attempts: list[Attempt],
    scores: list[Score],
    messages_by_attempt: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    scores_by_attempt = _scores_by_attempt(scores)
    return {
        "run": {
            "id": run.id,
            "name": run.name,
            "kind": run.kind,
            "status": run.status,
            "error": run.error,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": _isoformat(run.started_at),
            "finished_at": _isoformat(run.finished_at),
            "duration_ms": _duration_ms(run.started_at, run.finished_at),
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
                "messages": messages_by_attempt.get(a.id, []),
                "response_blob_path": a.response_blob_path,
                "conversation_blob_path": a.conversation_blob_path,
                "prompt_snapshot_blob_path": a.prompt_snapshot_blob_path,
                "converter_chain": a.converter_chain,
                "executor_name": _attempt_executor_name(a),
                "executor_kind": _attempt_executor_kind(a),
                "dataset_item_language": a.dataset_item_language,
                "status": a.status,
                "error": a.error,
                "started_at": _isoformat(a.started_at),
                "finished_at": _isoformat(a.finished_at),
                "duration_ms": _attempt_duration_ms(a),
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


def _run_export_csv(
    run: Run,
    attempts: list[Attempt],
    scores: list[Score],
    messages_by_attempt: dict[str, list[dict[str, Any]]],
) -> str:
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
        "started_at",
        "finished_at",
        "duration_ms",
        "executor_name",
        "executor_kind",
        "dataset_item_language",
        "converter_chain",
        "original_prompt",
        "transformed_prompt",
        "response",
        "messages",
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
                "started_at": _isoformat(attempt.started_at),
                "finished_at": _isoformat(attempt.finished_at),
                "duration_ms": _attempt_duration_ms(attempt),
                "executor_name": _attempt_executor_name(attempt),
                "executor_kind": _attempt_executor_kind(attempt),
                "dataset_item_language": attempt.dataset_item_language,
                "converter_chain": " -> ".join(attempt.converter_chain or []),
                "original_prompt": attempt.original_prompt_text or attempt.prompt_text,
                "transformed_prompt": attempt.prompt_text,
                "response": attempt.response_text,
                "messages": json.dumps(messages_by_attempt.get(attempt.id, []), ensure_ascii=False),
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
