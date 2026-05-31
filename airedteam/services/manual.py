from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from airedteam.core.types import AttemptResult, Message, Prompt, Response
from airedteam.engine.factory import build_scorer, build_target
from airedteam.engine.input_limits import (
    apply_target_input_limit,
    ensure_text_within_target_limit,
)
from airedteam.storage import models


class ManualService:
    def __init__(self, session_factory, blob_store, targets, converters, prompt_assets=None):
        self._sf = session_factory
        self._blobs = blob_store
        self._targets = targets
        self._converters = converters
        self._prompt_assets = prompt_assets

    async def create_run(self, *, name: str, target_id: str) -> str:
        async with self._sf() as s:
            run = models.Run(
                name=name,
                runspec_yaml=json.dumps({"target_id": target_id}),
                status="running",
                kind="manual",
            )
            s.add(run)
            await s.commit()
            return run.id

    async def create_conversation(self, run_id: str, *, seed_attempt_id: str | None = None):
        async with self._sf() as s:
            run = await s.get(models.Run, run_id)
            if run is None or run.kind != "manual":
                raise ValueError("not a manual run")
            if run.status == "completed":
                raise ValueError("manual run is already completed")
            target_id = json.loads(run.runspec_yaml or "{}").get("target_id", "")
            tgt_cfg = await self._targets.get(target_id)
            if tgt_cfg is None:
                raise ValueError(f"target_id {target_id!r} not found")

            seed_messages: list[dict] = []
            if seed_attempt_id:
                src = await s.get(models.Attempt, seed_attempt_id)
                if src and src.conversation_blob_path:
                    raw = await self._blobs.get(src.conversation_blob_path)
                    seed_messages = json.loads(raw)["messages"]
                elif src:
                    seed_messages = [
                        {"role": "user", "text": src.prompt_text, "metadata": {}},
                        {"role": "assistant", "text": src.response_text or "", "metadata": {}},
                    ]

            attempt_id = str(uuid.uuid4())
            blob_path = None
            if seed_messages:
                blob_path = f"runs/{run.id}/conversations/{attempt_id}.json"
                await self._blobs.put(blob_path, json.dumps({"messages": seed_messages}).encode())

            att = models.Attempt(
                id=attempt_id,
                run_id=run.id,
                target_id=target_id,
                target_name=tgt_cfg.name,
                prompt_text=(seed_messages[0]["text"] if seed_messages else ""),
                response_text=(
                    seed_messages[-1]["text"] if seed_messages and seed_messages[-1]["role"] == "assistant" else None
                ),
                conversation_blob_path=blob_path,
            )
            s.add(att)
            await s.commit()
            return attempt_id, seed_messages

    async def get_session(self, run_id: str):
        async with self._sf() as s:
            run = await s.get(models.Run, run_id)
            if run is None or run.kind != "manual":
                raise ValueError("not a manual run")
            target_id = json.loads(run.runspec_yaml or "{}").get("target_id", "")
            tgt_cfg = await self._targets.get(target_id)
            if tgt_cfg is None:
                raise ValueError(f"target_id {target_id!r} not found")
            attempt = (
                await s.execute(
                    select(models.Attempt)
                    .where(models.Attempt.run_id == run.id)
                    .order_by(models.Attempt.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if attempt is None:
                attempt_id, messages = await self.create_conversation(run_id)
            else:
                attempt_id = attempt.id
                messages = await self._read_conversation(attempt)
                if not messages and attempt.prompt_text:
                    messages = [{"role": "user", "text": attempt.prompt_text, "metadata": {}}]
                    if attempt.response_text:
                        messages.append(
                            {
                                "role": "assistant",
                                "text": attempt.response_text,
                                "metadata": {},
                            }
                        )
            return {
                "run_id": run.id,
                "attempt_id": attempt_id,
                "status": run.status,
                "target_id": target_id,
                "target_name": tgt_cfg.name,
                "conversation": messages,
                "evaluated": bool(await self.scores_for_attempt(attempt_id)),
                "scores": await self.scores_for_attempt(attempt_id),
            }

    async def append_turn(
        self,
        run_id: str,
        attempt_id: str,
        text: str,
        converters: list[dict] | None = None,
    ):
        preview = await self._converters.apply(text, converters)
        metadata = {}
        if converters:
            metadata = {
                "original_text": preview.original_text,
                "transformed_text": preview.transformed_text,
                "converter_chain": preview.converter_chain,
                "converters": preview.converters,
            }
        async with self._sf() as s:
            att = await s.get(models.Attempt, attempt_id)
            if att is None or att.run_id != run_id:
                raise ValueError("attempt not found in run")
            run = await s.get(models.Run, run_id)
            if run is None or run.status == "completed":
                raise ValueError("manual run is already completed")
            messages = await self._read_conversation(att)
            messages.append({"role": "user", "text": preview.transformed_text, "metadata": metadata})

        cfg = await self._targets.resolve_for_runtime(att.target_id)
        target = build_target(cfg)
        apply_target_input_limit(target, cfg)
        try:
            ensure_text_within_target_limit(
                preview.transformed_text,
                target,
                executor_name="manual",
            )
            resp = await target.chat(
                [Message(role=m["role"], text=m["text"], metadata=m.get("metadata")) for m in messages]
            )
        finally:
            await target.aclose()

        messages.append({"role": "assistant", "text": resp.text, "metadata": {}})
        blob_path = f"runs/{run_id}/conversations/{attempt_id}.json"
        await self._blobs.put(blob_path, json.dumps({"messages": messages}).encode())

        async with self._sf() as s:
            att = await s.get(models.Attempt, attempt_id)
            att.response_text = resp.text
            att.latency_ms = resp.latency_ms
            if resp.tokens_in is not None:
                att.tokens_in = resp.tokens_in
            if resp.tokens_out is not None:
                att.tokens_out = resp.tokens_out
            if att.prompt_text == "":
                att.prompt_text = preview.transformed_text
            att.conversation_blob_path = blob_path
            await s.commit()
        return messages

    async def evaluate_attempt(
        self,
        run_id: str,
        attempt_id: str,
        scorer_ref: dict,
    ) -> dict:
        async with self._sf() as s:
            att = await s.get(models.Attempt, attempt_id)
            if att is None or att.run_id != run_id:
                raise ValueError("attempt not found in run")
            messages_raw = await self._read_conversation(att)

        scorer, closeables = await self._build_scorer(scorer_ref)
        try:
            attempt = self._attempt_result_from_row(att, messages_raw)
            score_result = await scorer.score(attempt)
        finally:
            for target in closeables:
                await target.aclose()

        score_id = str(uuid.uuid4())
        prompt_snapshot_path = None
        if score_result.prompt_snapshot and self._prompt_assets is not None:
            prompt_snapshot_path = await self._prompt_assets.write_snapshot(
                run_id, f"score-{score_id}", score_result.prompt_snapshot
            )
        value = score_result.value if isinstance(score_result.value, dict) else {"value": score_result.value}
        async with self._sf() as s:
            row = models.Score(
                id=score_id,
                attempt_id=attempt_id,
                scorer=score_result.scorer,
                value_json=value,
                rationale=score_result.rationale,
                prompt_snapshot_blob_path=prompt_snapshot_path,
            )
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return _score_public(row)

    async def finish(self, run_id: str):
        async with self._sf() as s:
            run = await s.get(models.Run, run_id)
            if run is not None:
                run.status = "completed"
                run.finished_at = datetime.now(UTC).replace(tzinfo=None)
                await s.commit()

    async def _read_conversation(self, att) -> list[dict]:
        if not att.conversation_blob_path:
            return []
        raw = await self._blobs.get(att.conversation_blob_path)
        return json.loads(raw)["messages"]

    async def scores_for_attempt(self, attempt_id: str) -> list[dict]:
        async with self._sf() as s:
            rows = (
                (
                    await s.execute(
                        select(models.Score)
                        .where(models.Score.attempt_id == attempt_id)
                        .order_by(models.Score.created_at.desc())
                    )
                )
                .scalars()
                .all()
            )
            return [_score_public(row) for row in rows]

    async def _build_scorer(self, scorer_ref: dict):
        plugin = scorer_ref.get("plugin")
        params = dict(scorer_ref.get("params") or {})
        closeables = []
        if plugin == "llm_judge":
            judge_cfg_id = params.pop("judge_config_id", None)
            if not judge_cfg_id:
                raise ValueError("llm_judge scorer requires params.judge_config_id")
            judge_ref = await self._targets.resolve_for_runtime(judge_cfg_id)
            judge = build_target(judge_ref)
            apply_target_input_limit(judge, judge_ref)
            closeables.append(judge)
            params["judge"] = judge
            if self._prompt_assets is not None:
                params["prompt_assets"] = self._prompt_assets
        return build_scorer({"plugin": plugin, "params": params}), closeables

    @staticmethod
    def _attempt_result_from_row(att, messages_raw: list[dict]) -> AttemptResult:
        messages = [Message(role=m["role"], text=m["text"], metadata=m.get("metadata") or {}) for m in messages_raw]
        response_text = att.response_text or ""
        for msg in reversed(messages):
            if msg.role == "assistant":
                response_text = msg.text
                break
        return AttemptResult(
            prompt=Prompt(text=att.prompt_text),
            response=Response(text=response_text, raw={}, latency_ms=att.latency_ms or 0),
            conversation=messages or None,
            converter_chain=att.converter_chain or [],
            status=att.status,
            error=att.error,
        )


def _score_public(row: models.Score) -> dict:
    return {
        "id": row.id,
        "attempt_id": row.attempt_id,
        "scorer": row.scorer,
        "value": row.value_json,
        "rationale": row.rationale,
        "prompt_snapshot_blob_path": row.prompt_snapshot_blob_path,
        "reviewer_label": row.reviewer_label,
        "reviewer_notes": row.reviewer_notes,
        "reviewer_id": row.reviewer_id,
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
