from __future__ import annotations
import uuid
import yaml
from datetime import datetime
from sqlalchemy import update
from airedteam.storage.models import Run, Attempt, Score
from airedteam.engine.run_engine import RunEngine
from airedteam.engine.orchestrator import DefaultOrchestrator
from airedteam.engine.factory import build_converter, build_scorer, build_executor, build_target, build_dataset
from airedteam.runspec.models import RunSpec


class RunService:
    def __init__(self, session_factory, blob_store, secret_box, target_configs, datasets, progress_bus, *, response_inline_max_bytes: int = 8192, max_concurrency: int = 8) -> None:
        self._sf = session_factory
        self._blob = blob_store
        self._box = secret_box
        self._targets = target_configs
        self._datasets = datasets
        self._bus = progress_bus
        self._inline_max = response_inline_max_bytes
        self._max_conc = max_concurrency

    async def create_run(self, *, name: str, runspec_dict: dict) -> Run:
        RunSpec.model_validate(runspec_dict)  # validate early
        async with self._sf() as s:
            row = Run(name=name, runspec_yaml=yaml.safe_dump(runspec_dict), status="pending")
            s.add(row); await s.commit(); await s.refresh(row); return row

    async def _resolve_plugin_ref(self, ref, kind: str) -> dict:
        if ref.config_id is not None:
            if kind == "target":
                return await self._targets.resolve_for_runtime(ref.config_id)
            if kind == "dataset":
                return await self._datasets.resolve_for_runtime(ref.config_id)
        return {"plugin": ref.plugin, "params": ref.params}

    async def execute_run(self, run_id: str) -> None:
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            if run is None:
                raise KeyError(run_id)
            spec = RunSpec.model_validate(yaml.safe_load(run.runspec_yaml))
            run.status = "running"
            run.started_at = datetime.utcnow()
            await s.commit()

        target_refs = [await self._resolve_plugin_ref(t, "target") for t in spec.targets]
        ds_ref = await self._resolve_plugin_ref(spec.dataset, "dataset")

        targets = [build_target(r) for r in target_refs]
        dataset = build_dataset(ds_ref, blob_store=self._blob)
        converters = [build_converter(c.model_dump()) for c in spec.converters]
        executor = build_executor(spec.executor.model_dump())
        scorers = [build_scorer(sc.model_dump()) for sc in spec.scorers]

        attempt_id_by_index: dict[int, str] = {}

        async def on_attempt(ar, target_name, dataset_item_id):
            text = ar.response.text if ar.response else None
            blob_path = None
            if text and len(text.encode("utf-8", errors="ignore")) > self._inline_max:
                blob_path = f"responses/{run_id}/{uuid.uuid4()}.txt"
                await self._blob.put(blob_path, text.encode())
                stored_text = None
            else:
                stored_text = text
            async with self._sf() as s:
                a = Attempt(
                    run_id=run_id,
                    target_id=target_name,
                    target_name=target_name,
                    dataset_item_id=dataset_item_id,
                    prompt_text=ar.prompt.text,
                    converter_chain=ar.converter_chain,
                    response_text=stored_text,
                    response_blob_path=blob_path,
                    latency_ms=(ar.response.latency_ms if ar.response else None),
                    tokens_in=(ar.response.tokens_in if ar.response else None),
                    tokens_out=(ar.response.tokens_out if ar.response else None),
                    status=ar.status,
                    error=ar.error,
                )
                s.add(a); await s.commit(); await s.refresh(a)
                idx = len(attempt_id_by_index)
                attempt_id_by_index[idx] = a.id
                await s.execute(update(Run).where(Run.id == run_id).values(progress_done=Run.progress_done + 1))
                await s.commit()

        async def on_score(idx, sr):
            attempt_id = attempt_id_by_index.get(idx)
            if attempt_id is None:
                return
            value = sr.value if isinstance(sr.value, dict) else {"value": sr.value}
            async with self._sf() as s:
                s.add(Score(attempt_id=attempt_id, scorer=sr.scorer, value_json=value, rationale=sr.rationale))
                await s.commit()

        try:
            total = (await dataset.size()) or 0
        except Exception:
            total = 0
        async with self._sf() as s:
            await s.execute(update(Run).where(Run.id == run_id).values(progress_total=total * len(targets)))
            await s.commit()

        engine = RunEngine(progress_bus=self._bus, on_attempt=on_attempt, on_score=on_score)
        try:
            await engine.run(
                run_id=run_id, dataset=dataset, targets=targets, converters=converters,
                executor=executor, scorers=scorers,
                concurrency=min(spec.concurrency, self._max_conc),
                orchestrator=DefaultOrchestrator(),
            )
            async with self._sf() as s:
                await s.execute(update(Run).where(Run.id == run_id).values(status="completed", finished_at=datetime.utcnow()))
                await s.commit()
        except Exception as e:
            async with self._sf() as s:
                await s.execute(update(Run).where(Run.id == run_id).values(status="failed", finished_at=datetime.utcnow(), error=str(e)))
                await s.commit()
            raise
