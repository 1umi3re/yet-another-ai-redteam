from __future__ import annotations

from airedteam.core.types import AttemptResult, Message, Prompt, Response
from airedteam.engine.input_limits import (
    chunk_message,
    prompt_with_input_limit_metadata,
    split_text_by_chars,
    target_max_input_chars,
)


class SplitExecutor:
    """Decompose one converted prompt into limit-sized chat turns."""

    name = "split_executor"

    async def run(self, prompt: Prompt, target, converters: list) -> AttemptResult:
        chain: list[str] = []
        cur = prompt
        for converter in converters:
            cur = await converter.convert(cur)
            chain.append(converter.name)

        max_chars = target_max_input_chars(target)
        if max_chars is None:
            return AttemptResult(
                prompt=cur,
                response=None,
                status="failed",
                error="split_executor requires target max_input_chars to be configured",
                converter_chain=chain,
            )
        if not callable(getattr(target, "chat", None)):
            return AttemptResult(
                prompt=cur,
                response=None,
                status="failed",
                error="split_executor requires a target with chat support",
                converter_chain=chain,
            )

        chunks = split_text_by_chars(cur.text, max_chars)
        out_prompt = prompt_with_input_limit_metadata(
            cur,
            original_length=len(prompt.text),
            chunk_count=len(chunks),
            split_strategy="word_boundary",
        )
        conversation: list[Message] = []
        last_response: Response | None = None
        try:
            for idx, chunk in enumerate(chunks, start=1):
                user = chunk_message(
                    text=chunk,
                    base_metadata=cur.metadata,
                    index=idx,
                    count=len(chunks),
                    original_length=len(cur.text),
                    max_chars=max_chars,
                    split_strategy="word_boundary",
                    artifacts=(cur.artifacts if idx == 1 else []),
                )
                conversation.append(user)
                last_response = await target.chat(list(conversation))
                conversation.append(Message(role="assistant", text=last_response.text))
            return AttemptResult(
                prompt=out_prompt,
                response=last_response,
                status="completed",
                converter_chain=chain,
                conversation=list(conversation),
            )
        except Exception as exc:
            return AttemptResult(
                prompt=out_prompt,
                response=last_response,
                status="failed",
                error=f"{type(exc).__name__}: {exc}",
                converter_chain=chain,
                conversation=list(conversation),
            )
