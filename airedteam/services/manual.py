from __future__ import annotations
import json
from datetime import datetime
from airedteam.storage import models
from airedteam.core.types import Message
from airedteam.engine.factory import build_target


class ManualService:
    def __init__(self, session_factory, blob_store, targets):
        self._sf = session_factory
        self._blobs = blob_store
        self._targets = targets

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

            import uuid
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
                response_text=(seed_messages[-1]["text"]
                               if seed_messages and seed_messages[-1]["role"] == "assistant"
                               else None),
                conversation_blob_path=blob_path,
            )
            s.add(att)
            await s.commit()
            return attempt_id, seed_messages

    async def append_turn(self, run_id: str, attempt_id: str, text: str):
        async with self._sf() as s:
            att = await s.get(models.Attempt, attempt_id)
            if att is None or att.run_id != run_id:
                raise ValueError("attempt not found in run")
            messages = await self._read_conversation(att)
            messages.append({"role": "user", "text": text, "metadata": {}})

        cfg = await self._targets.resolve_for_runtime(att.target_id)
        target = build_target(cfg)
        try:
            resp = await target.chat([Message(role=m["role"], text=m["text"],
                                               metadata=m.get("metadata")) for m in messages])
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
                att.prompt_text = text
            att.conversation_blob_path = blob_path
            await s.commit()
        return messages

    async def finish(self, run_id: str):
        async with self._sf() as s:
            run = await s.get(models.Run, run_id)
            if run is not None:
                run.status = "completed"
                run.finished_at = datetime.utcnow()
                await s.commit()

    async def _read_conversation(self, att) -> list[dict]:
        if not att.conversation_blob_path:
            return []
        raw = await self._blobs.get(att.conversation_blob_path)
        return json.loads(raw)["messages"]
