from __future__ import annotations

from airedteam.core.types import AttemptResult, Message, Prompt, PromptArtifact
from airedteam.engine.input_limits import ensure_text_within_target_limit

RETEST_METADATA_KEY = "_airedteam_retest"


class RetestExecutor:
    """Dispatch one snapshotted source attempt without creating a method cross-product."""

    name = "retest"

    def __init__(self, *, mode: str, methods: dict[str, object] | None = None) -> None:
        self.mode = mode
        self._methods = methods or {}

    async def run(self, prompt: Prompt, target, converters: list) -> AttemptResult:
        item = dict(prompt.metadata.get(RETEST_METADATA_KEY) or {})
        if self.mode == "exact_replay":
            result = await self._exact_replay(prompt, item, target)
        else:
            method = self._methods.get(str(item.get("source_attempt_id")))
            if method is None:
                return AttemptResult(prompt=prompt, status="failed", error="Retest method is unavailable")
            result = await method.run(prompt, target, [])

        result.source_run_id = item.get("source_run_id")
        result.source_attempt_id = item.get("source_attempt_id")
        result.retest_mode = self.mode
        result.executor_ref = item.get("method_ref")
        if self.mode == "exact_replay":
            result.executor_name = "exact_replay"
            result.executor_kind = "retest"
        return result

    async def _exact_replay(self, prompt: Prompt, item: dict, target) -> AttemptResult:
        user_messages = item.get("user_messages") or []
        try:
            if len(user_messages) <= 1:
                sent = str(item.get("sent_prompt") or prompt.text)
                ensure_text_within_target_limit(sent, target, executor_name=self.name)
                artifacts = self._artifacts(user_messages[0]) if user_messages else prompt.artifacts
                exact_prompt = Prompt(text=sent, metadata=prompt.metadata, artifacts=artifacts)
                response = await target.generate(exact_prompt)
                return AttemptResult(prompt=exact_prompt, response=response)

            conversation: list[Message] = []
            response = None
            first_prompt = None
            for payload in user_messages:
                user = Message(
                    role="user",
                    text=str(payload.get("text") or ""),
                    metadata=dict(payload.get("metadata") or {}),
                    artifacts=self._artifacts(payload),
                )
                ensure_text_within_target_limit(user.text, target, executor_name=self.name)
                conversation.append(user)
                first_prompt = first_prompt or Prompt(text=user.text, metadata=user.metadata)
                response = await target.chat(list(conversation))
                conversation.append(Message(role="assistant", text=response.text))
            return AttemptResult(prompt=first_prompt or prompt, response=response, conversation=conversation)
        except Exception as exc:
            return AttemptResult(
                prompt=prompt,
                status="failed",
                error=f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _artifacts(payload: dict) -> list[PromptArtifact]:
        return [
            PromptArtifact(
                path=str(artifact["path"]),
                kind=artifact["kind"],
                media_type=str(artifact["media_type"]),
                name=artifact.get("name"),
                metadata=dict(artifact.get("metadata") or {}),
            )
            for artifact in payload.get("artifacts") or []
        ]
