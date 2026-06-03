from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import asdict
from datetime import UTC, datetime

import yaml
from sqlalchemy import delete, func, select, update

from airedteam.builtins.executors.general_multi_turn import GeneralMultiTurnExecutor
from airedteam.core.registry import default_registry
from airedteam.core.score_status import failed_score_value, is_failed_score_value
from airedteam.core.types import AttemptResult, Message, Prompt, Response, ScoreResult
from airedteam.engine.factory import (
    build_converter,
    build_dataset,
    build_executor,
    build_scorer,
    build_target,
)
from airedteam.engine.input_limits import apply_target_input_limit
from airedteam.engine.orchestrator import DefaultOrchestrator
from airedteam.engine.run_engine import RunEngine
from airedteam.engine.sampling import SampledDataset
from airedteam.runspec.models import RunSpec
from airedteam.services.prompt_assets import PromptAssetService
from airedteam.storage.models import Attempt, Run, Score

TERMINAL_RUN_STATUSES = {"completed", "failed", "cancelled"}
STOP_REQUEST_STATUSES = {"pausing", "paused", "cancelled"}


def _message_payload(message) -> dict:
    payload = {
        "role": message.role,
        "text": message.text,
        "metadata": dict(message.metadata),
    }
    if getattr(message, "artifacts", None):
        payload["artifacts"] = [asdict(artifact) for artifact in message.artifacts]
    return payload


def _message_from_payload(payload: dict) -> Message:
    return Message(
        role=payload.get("role", "user"),
        text=payload.get("text", ""),
        metadata=dict(payload.get("metadata") or {}),
    )


_LLM_CONVERTERS = {
    "llm_variation",
    "llm_tone",
    "llm_persuasion",
    "llm_generic",
    "tense",
    "llm_malicious_question",
    "llm_toxic_sentence",
    "llm_random_translation",
    "llm_scientific_translation",
    "paraphrase_fast",
    "paraphrase_pegasus",
    "meta_agent",
}

_TRANSLATION_CONVERTERS = {
    "translation_llm",
    "low_resource_language",
    "multilingual",
}


def _is_general_multi_turn_executor(cls) -> bool:
    try:
        return issubclass(cls, GeneralMultiTurnExecutor)
    except TypeError:
        return False


def _target_max_concurrency(runtime_cfg: dict) -> int | None:
    raw = (runtime_cfg.get("params") or {}).get("max_concurrency")
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"target max_concurrency must be a positive integer: {raw!r}") from None
    if value < 1:
        raise ValueError(f"target max_concurrency must be a positive integer: {raw!r}")
    return value


class RunService:
    def __init__(
        self,
        session_factory,
        blob_store,
        secret_box,
        target_configs,
        datasets,
        progress_bus,
        *,
        prompt_assets=None,
        response_inline_max_bytes: int = 8192,
        max_concurrency: int = 8,
    ) -> None:
        self._sf = session_factory
        self._blob = blob_store
        self._box = secret_box
        self._targets = target_configs
        self._datasets = datasets
        self._bus = progress_bus
        self._prompt_assets = prompt_assets or PromptAssetService(session_factory, blob_store)
        self._inline_max = response_inline_max_bytes
        self._max_conc = max_concurrency
        self._tasks: dict[str, asyncio.Task] = {}

    async def create_run(self, *, name: str, runspec_dict: dict) -> Run:
        RunSpec.model_validate(runspec_dict)  # validate early
        async with self._sf() as s:
            row = Run(name=name, runspec_yaml=yaml.safe_dump(runspec_dict), status="pending")
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return row

    async def start_run(self, run_id: str) -> None:
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            if run is None:
                raise KeyError(run_id)
            if run.status == "running" and run_id in self._tasks:
                return
            if run.status == "paused":
                raise ValueError("run is paused; use resume")
            if run.status == "pausing":
                raise ValueError("run is pausing")
            if run.status in TERMINAL_RUN_STATUSES:
                raise ValueError(f"run is already {run.status}")
        task = asyncio.create_task(self.execute_run(run_id))
        self._tasks[run_id] = task
        task.add_done_callback(lambda finished: self._forget_task(run_id, finished))

    async def cancel_run(self, run_id: str) -> None:
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            if run is None:
                raise KeyError(run_id)
            if run.status in TERMINAL_RUN_STATUSES:
                return
            run.status = "cancelled"
            run.finished_at = datetime.now(UTC).replace(tzinfo=None)
            await s.commit()
        task = self._tasks.get(run_id)
        if task is not None and not task.done():
            task.cancel()
        await self._bus.publish(run_id, {"event": "run.cancelled", "status": "cancelled"})

    async def pause_run(self, run_id: str) -> None:
        task = self._tasks.get(run_id)
        has_active_task = task is not None and not task.done()
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            if run is None:
                raise KeyError(run_id)
            if run.status in TERMINAL_RUN_STATUSES:
                raise ValueError(f"run is already {run.status}")
            if run.status == "pending":
                raise ValueError("run has not started")
            if run.status == "paused":
                return
            if run.status == "pausing":
                return
            if run.status != "running":
                raise ValueError(f"run cannot be paused from {run.status}")
            if has_active_task:
                run.status = "pausing"
                event = {"event": "run.pausing", "status": "pausing"}
            else:
                run.status = "paused"
                event = {"event": "run.paused", "status": "paused"}
            await s.commit()
        await self._bus.publish(run_id, event)

    async def resume_run(self, run_id: str, *, retry_failed: bool = False) -> None:
        task = self._tasks.get(run_id)
        has_active_task = task is not None and not task.done()
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            if run is None:
                raise KeyError(run_id)
            can_resume_failed_run = run.kind == "automated" and run.status == "failed"
            if run.status in TERMINAL_RUN_STATUSES and not can_resume_failed_run:
                raise ValueError(f"run is already {run.status}")
            if run.status == "pending":
                raise ValueError("run has not started")
            if can_resume_failed_run and has_active_task:
                raise ValueError("run is still failing")
            if run.status == "pausing" and has_active_task:
                raise ValueError("run is pausing")
            if run.status == "running" and has_active_task:
                return
        task = asyncio.create_task(self.execute_run(run_id, retry_failed=retry_failed))
        self._tasks[run_id] = task
        task.add_done_callback(lambda finished: self._forget_task(run_id, finished))
        await self._bus.publish(run_id, {"event": "run.resumed", "status": "running", "retry_failed": retry_failed})

    async def _resolve_plugin_ref(self, ref, kind: str) -> dict:
        if ref.config_id is not None:
            if kind == "target":
                return await self._targets.resolve_for_runtime(ref.config_id)
            if kind == "dataset":
                return await self._datasets.resolve_for_runtime(ref.config_id)
        return {"plugin": ref.plugin, "params": ref.params}

    def _build_target_from_cfg(self, runtime_cfg: dict):
        """Build a Target instance from a resolved target-config dict
        (as returned by TargetConfigService.resolve_for_runtime).
        """
        target = build_target(runtime_cfg)
        max_concurrency = _target_max_concurrency(runtime_cfg)
        if max_concurrency is not None:
            target._airedteam_max_concurrency = max_concurrency
        apply_target_input_limit(target, runtime_cfg)
        return target

    async def _build_scorers(self, spec: RunSpec) -> tuple[list, list]:
        closeables = []
        scorers = []
        for sc in spec.scorers:
            scorer, scorer_closeables, _metadata = await self._build_scorer_from_ref(sc.model_dump())
            closeables.extend(scorer_closeables)
            scorers.append(scorer)
        return scorers, closeables

    async def _build_scorer_from_ref(self, ref: dict) -> tuple[object, list, dict]:
        closeables = []
        metadata = {}
        params = dict(ref.get("params") or {})
        if ref.get("plugin") == "llm_judge":
            judge_cfg_id = params.pop("judge_config_id", None)
            if not judge_cfg_id:
                raise ValueError(
                    "llm_judge scorer requires params.judge_config_id "
                    "(id of a configured target to use as the judge)"
                )
            judge_cfg = await self._targets.get(judge_cfg_id)
            judge_ref = await self._targets.resolve_for_runtime(judge_cfg_id)
            params["judge"] = self._build_target_from_cfg(judge_ref)
            closeables.append(params["judge"])
            params["prompt_assets"] = self._prompt_assets
            metadata["judge_config_id"] = judge_cfg_id
            metadata["judge_name"] = judge_cfg.name if judge_cfg is not None else judge_cfg_id
        scorer = build_scorer({"plugin": ref["plugin"], "params": params})
        return scorer, closeables, metadata

    async def _attempt_result_from_row(self, attempt: Attempt) -> AttemptResult:
        response_text = attempt.response_text
        if response_text is None and attempt.response_blob_path:
            response_text = (await self._blob.get(attempt.response_blob_path)).decode("utf-8")
        response = None
        if response_text is not None:
            response = Response(
                text=response_text,
                raw={},
                latency_ms=attempt.latency_ms or 0,
                tokens_in=attempt.tokens_in,
                tokens_out=attempt.tokens_out,
            )

        conversation = None
        if attempt.conversation_blob_path:
            raw = await self._blob.get(attempt.conversation_blob_path)
            payload = json.loads(raw.decode("utf-8"))
            conversation = [_message_from_payload(item) for item in payload.get("messages", [])]

        metadata = {}
        if attempt.dataset_item_id:
            metadata["id"] = attempt.dataset_item_id
        return AttemptResult(
            prompt=Prompt(text=attempt.prompt_text, metadata=metadata),
            response=response,
            status=attempt.status,
            error=attempt.error,
            converter_chain=list(attempt.converter_chain or []),
            conversation=conversation,
        )

    async def _write_score(self, run_id: str, attempt_id: str, sr: ScoreResult) -> None:
        value = sr.value if isinstance(sr.value, dict) else {"value": sr.value}
        score_id = str(uuid.uuid4())
        prompt_snapshot_path = None
        if sr.prompt_snapshot:
            prompt_snapshot_path = await self._prompt_assets.write_snapshot(
                run_id, f"score-{score_id}", sr.prompt_snapshot
            )
        async with self._sf() as s:
            s.add(
                Score(
                    id=score_id,
                    attempt_id=attempt_id,
                    scorer=sr.scorer,
                    value_json=value,
                    rationale=sr.rationale,
                    prompt_snapshot_blob_path=prompt_snapshot_path,
                )
            )
            await s.commit()

    async def retry_scores(
        self,
        run_id: str,
        *,
        failed_only: bool = True,
        score_ids: list[str] | None = None,
        attempt_ids: list[str] | None = None,
        scorers: list[str] | None = None,
        scorer_ref: dict | None = None,
    ) -> dict[str, int]:
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            if run is None:
                raise KeyError(run_id)
            if run.kind != "automated":
                raise ValueError("score retry is only available for automated runs")
            spec = RunSpec.model_validate(yaml.safe_load(run.runspec_yaml))

        if scorer_ref is not None:
            return await self._score_attempts_with_new_scorer(
                run_id,
                scorer_ref=scorer_ref,
                attempt_ids=attempt_ids,
            )

        scorer_instances, closeables = await self._build_scorers(spec)
        scorer_by_name = {getattr(sc, "name", "?"): sc for sc in scorer_instances}
        score_filter = set(score_ids or [])
        attempt_filter = set(attempt_ids or [])
        scorer_filter = set(scorers or [])
        try:
            async with self._sf() as s:
                rows = (
                    await s.execute(
                        select(Attempt, Score)
                        .join(Score, Score.attempt_id == Attempt.id)
                        .where(Attempt.run_id == run_id)
                        .order_by(Score.created_at)
                    )
                ).all()
                candidates = []
                for attempt, score in rows:
                    if score_filter and score.id not in score_filter:
                        continue
                    if attempt_filter and attempt.id not in attempt_filter:
                        continue
                    if scorer_filter and score.scorer not in scorer_filter:
                        continue
                    if failed_only and not is_failed_score_value(score.value_json):
                        continue
                    candidates.append((attempt, score))

            retried = 0
            completed = 0
            failed = 0
            skipped = 0
            for attempt, score in candidates:
                scorer = scorer_by_name.get(score.scorer)
                if scorer is None:
                    skipped += 1
                    continue
                attempt_result = await self._attempt_result_from_row(attempt)
                try:
                    score_result = await scorer.score(attempt_result)
                except Exception as exc:
                    score_result = ScoreResult(scorer=score.scorer, value=failed_score_value(exc), rationale=None)
                async with self._sf() as s:
                    await s.execute(delete(Score).where(Score.id == score.id))
                    await s.commit()
                await self._write_score(run_id, attempt.id, score_result)
                retried += 1
                if is_failed_score_value(score_result.value):
                    failed += 1
                else:
                    completed += 1

            return {
                "matched": len(candidates),
                "retried": retried,
                "completed": completed,
                "failed": failed,
                "skipped": skipped,
            }
        finally:
            for obj in closeables:
                try:
                    await obj.aclose()
                except Exception:
                    pass

    async def _score_attempts_with_new_scorer(
        self,
        run_id: str,
        *,
        scorer_ref: dict,
        attempt_ids: list[str] | None = None,
    ) -> dict[str, int]:
        scorer, closeables, metadata = await self._build_scorer_from_ref(scorer_ref)
        attempt_filter = set(attempt_ids or [])
        try:
            async with self._sf() as s:
                query = select(Attempt).where(Attempt.run_id == run_id).order_by(Attempt.created_at)
                if attempt_filter:
                    query = query.where(Attempt.id.in_(attempt_filter))
                attempts = list((await s.execute(query)).scalars().all())

            retried = 0
            completed = 0
            failed = 0
            for attempt in attempts:
                attempt_result = await self._attempt_result_from_row(attempt)
                try:
                    score_result = await scorer.score(attempt_result)
                except Exception as exc:
                    score_result = ScoreResult(
                        scorer=getattr(scorer, "name", scorer_ref.get("plugin", "?")),
                        value=failed_score_value(exc),
                        rationale=None,
                    )

                if isinstance(score_result.value, dict) and metadata:
                    score_result = ScoreResult(
                        scorer=score_result.scorer,
                        value={**score_result.value, **metadata},
                        rationale=score_result.rationale,
                        prompt_snapshot=score_result.prompt_snapshot,
                    )

                await self._write_score(run_id, attempt.id, score_result)
                retried += 1
                if is_failed_score_value(score_result.value):
                    failed += 1
                else:
                    completed += 1

            return {
                "matched": len(attempts),
                "retried": retried,
                "completed": completed,
                "failed": failed,
                "skipped": 0,
            }
        finally:
            for obj in closeables:
                try:
                    await obj.aclose()
                except Exception:
                    pass

    async def _is_cancelled(self, run_id: str) -> bool:
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            return run is not None and run.status == "cancelled"

    async def _should_stop_run(self, run_id: str) -> bool:
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            return run is None or run.status in STOP_REQUEST_STATUSES

    async def _run_status(self, run_id: str) -> str | None:
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            return run.status if run is not None else None

    async def _existing_work_statuses(self, run_id: str) -> dict[str, str]:
        async with self._sf() as s:
            rows = await s.execute(
                select(Attempt.work_key, Attempt.status).where(
                    Attempt.run_id == run_id,
                    Attempt.work_key.is_not(None),
                )
            )
            return {work_key: status for work_key, status in rows if work_key}

    async def _existing_work_count(self, run_id: str) -> int:
        async with self._sf() as s:
            return (
                await s.execute(
                    select(func.count(func.distinct(Attempt.work_key))).where(
                        Attempt.run_id == run_id,
                        Attempt.work_key.is_not(None),
                    )
                )
            ).scalar_one()

    def _forget_task(self, run_id: str, task: asyncio.Task) -> None:
        self._tasks.pop(run_id, None)
        try:
            task.exception()
        except asyncio.CancelledError:
            pass

    async def execute_run(self, run_id: str, *, retry_failed: bool = False) -> None:
        closeables = []
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            if run is None:
                raise KeyError(run_id)
            if run.status == "cancelled":
                return
            spec = RunSpec.model_validate(yaml.safe_load(run.runspec_yaml))
            run.status = "running"
            run.started_at = run.started_at or datetime.now(UTC).replace(tzinfo=None)
            run.finished_at = None
            run.error = None
            await s.commit()

        try:
            target_refs = [await self._resolve_plugin_ref(t, "target") for t in spec.targets]
            ds_ref = await self._resolve_plugin_ref(spec.dataset, "dataset")

            targets = [self._build_target_from_cfg(r) for r in target_refs]
            closeables.extend(targets)
            dataset = build_dataset(ds_ref, blob_store=self._blob)

            # Apply sampling if configured
            if spec.sampling is not None:
                dataset = SampledDataset(
                    dataset, limit=spec.sampling.limit, shuffle=spec.sampling.shuffle, seed=spec.sampling.seed
                )

            # Resolve converter-level target references before building.
            converter_refs = []
            for conv in spec.converters:
                ref = conv.model_dump()
                converter_plugin = ref.get("plugin")
                params = dict(ref.get("params") or {})
                if converter_plugin in _TRANSLATION_CONVERTERS and "translator_config_id" in params:
                    tcid = params.pop("translator_config_id")
                    tgt_cfg = await self._targets.resolve_for_runtime(tcid)
                    params["translator"] = self._build_target_from_cfg(tgt_cfg)
                    closeables.append(params["translator"])
                if converter_plugin in _LLM_CONVERTERS and "converter_config_id" in params:
                    cid = params.pop("converter_config_id")
                    tgt_cfg = await self._targets.resolve_for_runtime(cid)
                    params["converter"] = self._build_target_from_cfg(tgt_cfg)
                    closeables.append(params["converter"])
                if converter_plugin in _LLM_CONVERTERS or converter_plugin in _TRANSLATION_CONVERTERS:
                    params["prompt_assets"] = self._prompt_assets
                if converter_plugin == "template_jailbreak" and params.get("attack_template_asset_id"):
                    asset_id = params.pop("attack_template_asset_id")
                    asset = await self._prompt_assets.get_asset(asset_id)
                    if asset.get("purpose") != "attack_template":
                        raise ValueError(f"prompt asset is not an attack template: {asset_id}")
                    active_override = asset.get("active_override")
                    params["template"] = (
                        active_override.get("template")
                        if isinstance(active_override, dict) and active_override.get("template")
                        else asset["template"]
                    )
                converter_refs.append({"plugin": ref["plugin"], "params": params})
            converters = [build_converter(r) for r in converter_refs]

            # Resolve executor-level target references before building.
            executor_ref = spec.executor.model_dump()
            executor_params = dict(executor_ref.get("params") or {})
            plugin_name = executor_ref.get("plugin")
            executor_cls = default_registry().get("executors", plugin_name)
            is_general_multi_turn = _is_general_multi_turn_executor(executor_cls)
            needs_attacker = (
                plugin_name
                in {
                    "crescendo",
                    "pair",
                    "jailbreak_iterative",
                }
                or is_general_multi_turn
            )
            needs_evaluator = is_general_multi_turn
            needs_judge = plugin_name in {"pair", "jailbreak_iterative"} or is_general_multi_turn
            uses_prompt_assets = needs_attacker or needs_judge or needs_evaluator

            if needs_attacker and "attacker_config_id" in executor_params:
                aid = executor_params.pop("attacker_config_id")
                tgt_cfg = await self._targets.resolve_for_runtime(aid)
                executor_params["attacker"] = self._build_target_from_cfg(tgt_cfg)
                closeables.append(executor_params["attacker"])
            if needs_evaluator and "evaluator_config_id" in executor_params:
                eid = executor_params.pop("evaluator_config_id")
                ecfg = await self._targets.resolve_for_runtime(eid)
                executor_params["evaluator"] = self._build_target_from_cfg(ecfg)
                closeables.append(executor_params["evaluator"])
            if needs_judge and "judge_config_id" in executor_params:
                jid = executor_params.pop("judge_config_id")
                jcfg = await self._targets.resolve_for_runtime(jid)
                executor_params["judge"] = self._build_target_from_cfg(jcfg)
                closeables.append(executor_params["judge"])
            if uses_prompt_assets:
                executor_params["prompt_assets"] = self._prompt_assets
            executor = build_executor({"plugin": plugin_name, "params": executor_params})

            scorers, scorer_closeables = await self._build_scorers(spec)
            closeables.extend(scorer_closeables)

            existing_work_statuses = await self._existing_work_statuses(run_id)

            async def should_skip_work(work_key: str) -> bool:
                status = existing_work_statuses.get(work_key)
                if status is None:
                    return False
                return not (retry_failed and status == "failed")

            attempt_id_by_index: dict[int, str] = {}

            async def on_attempt(ar, target_name, dataset_item_id, work_key, original_prompt):
                text = ar.response.text if ar.response else None
                blob_path = None
                if text and len(text.encode("utf-8", errors="ignore")) > self._inline_max:
                    blob_path = f"responses/{run_id}/{uuid.uuid4()}.txt"
                    await self._blob.put(blob_path, text.encode())
                    stored_text = None
                else:
                    stored_text = text

                attempt_id = str(uuid.uuid4())
                conv_path: str | None = None
                if ar.conversation:
                    conv_path = f"runs/{run_id}/conversations/{attempt_id}.json"
                    payload = json.dumps({"messages": [_message_payload(m) for m in ar.conversation]}).encode("utf-8")
                    await self._blob.put(conv_path, payload)
                prompt_snapshot_path: str | None = None
                if ar.prompt_snapshots:
                    prompt_snapshot_path = await self._prompt_assets.write_snapshot(
                        run_id, f"attempt-{attempt_id}", {"snapshots": ar.prompt_snapshots}
                    )

                async with self._sf() as s:
                    existing = (
                        (
                            await s.execute(
                                select(Attempt).where(
                                    Attempt.run_id == run_id,
                                    Attempt.work_key == work_key,
                                )
                            )
                        )
                        .scalars()
                        .first()
                    )
                    created = existing is None
                    if existing is None:
                        a = Attempt(id=attempt_id, run_id=run_id, work_key=work_key)
                        s.add(a)
                    else:
                        a = existing
                        attempt_id = a.id
                        await s.execute(delete(Score).where(Score.attempt_id == a.id))
                    a.target_id = target_name
                    a.target_name = target_name
                    a.dataset_item_id = dataset_item_id
                    a.original_prompt_text = original_prompt.text
                    a.prompt_text = ar.prompt.text
                    a.converter_chain = ar.converter_chain
                    a.response_text = stored_text
                    a.response_blob_path = blob_path
                    a.conversation_blob_path = conv_path
                    a.prompt_snapshot_blob_path = prompt_snapshot_path
                    a.latency_ms = ar.response.latency_ms if ar.response else None
                    a.tokens_in = ar.response.tokens_in if ar.response else None
                    a.tokens_out = ar.response.tokens_out if ar.response else None
                    a.status = ar.status
                    a.error = ar.error
                    if created:
                        await s.execute(update(Run).where(Run.id == run_id).values(progress_done=Run.progress_done + 1))
                    await s.commit()
                    existing_work_statuses[work_key] = ar.status
                    idx = len(attempt_id_by_index)
                    attempt_id_by_index[idx] = attempt_id

            async def on_score(idx, sr):
                attempt_id = attempt_id_by_index.get(idx)
                if attempt_id is None:
                    return
                await self._write_score(run_id, attempt_id, sr)

            try:
                total = (await dataset.size()) or 0
            except Exception:
                total = 0
            converter_variant_count = max(1, len(converters))
            existing_work_count = await self._existing_work_count(run_id)
            async with self._sf() as s:
                await s.execute(
                    update(Run)
                    .where(Run.id == run_id)
                    .values(
                        progress_total=total * len(targets) * converter_variant_count,
                        progress_done=existing_work_count,
                    )
                )
                await s.commit()

            engine = RunEngine(progress_bus=self._bus, on_attempt=on_attempt, on_score=on_score)
            run_coro = engine.run(
                run_id=run_id,
                dataset=dataset,
                targets=targets,
                converters=converters,
                executor=executor,
                scorers=scorers,
                concurrency=min(spec.concurrency, self._max_conc),
                orchestrator=DefaultOrchestrator(),
                should_stop=lambda: self._should_stop_run(run_id),
                should_skip_work=should_skip_work,
            )
            if spec.timeout_seconds is not None and spec.timeout_seconds > 0:
                engine_result = await asyncio.wait_for(run_coro, timeout=spec.timeout_seconds)
            else:
                engine_result = await run_coro
            if await self._is_cancelled(run_id):
                return
            current_status = await self._run_status(run_id)
            if engine_result.stopped and current_status in {"pausing", "paused"}:
                async with self._sf() as s:
                    await s.execute(
                        update(Run)
                        .where(Run.id == run_id)
                        .values(status="paused", finished_at=None)
                    )
                    await s.commit()
                await self._bus.publish(run_id, {"event": "run.paused", "status": "paused"})
                return
            async with self._sf() as s:
                await s.execute(
                    update(Run)
                    .where(Run.id == run_id)
                    .values(status="completed", finished_at=datetime.now(UTC).replace(tzinfo=None))
                )
                await s.commit()
            await self._bus.publish(run_id, {"event": "run.finished", "status": "completed"})
        except asyncio.CancelledError:
            async with self._sf() as s:
                await s.execute(
                    update(Run)
                    .where(Run.id == run_id)
                    .values(status="cancelled", finished_at=datetime.now(UTC).replace(tzinfo=None))
                )
                await s.commit()
            await self._bus.publish(run_id, {"event": "run.cancelled", "status": "cancelled"})
            return
        except TimeoutError:
            async with self._sf() as s:
                await s.execute(
                    update(Run)
                    .where(Run.id == run_id)
                    .values(
                        status="failed",
                        finished_at=datetime.now(UTC).replace(tzinfo=None),
                        error=f"run timed out after {spec.timeout_seconds} seconds",
                    )
                )
                await s.commit()
            await self._bus.publish(run_id, {"event": "run.failed", "status": "failed"})
            raise
        except Exception as e:
            async with self._sf() as s:
                await s.execute(
                    update(Run)
                    .where(Run.id == run_id)
                    .values(status="failed", finished_at=datetime.now(UTC).replace(tzinfo=None), error=str(e))
                )
                await s.commit()
            await self._bus.publish(run_id, {"event": "run.failed", "status": "failed"})
            raise
        finally:
            for obj in closeables:
                try:
                    await obj.aclose()
                except Exception:
                    pass
