from __future__ import annotations

from airedteam.core.types import AttemptResult, Prompt
from airedteam.engine.input_limits import ensure_text_within_target_limit


class ConverterMethodExecutor:
    def __init__(self, *, method_name: str, converter) -> None:
        self.name = method_name
        self._converter = converter

    async def run(self, prompt: Prompt, target, converters: list) -> AttemptResult:
        cur = prompt
        chain: list[str] = []
        try:
            cur = await self._converter.convert(cur)
            chain.append(self.name)
            ensure_text_within_target_limit(
                cur.text,
                target,
                executor_name=self.name,
            )
            resp = await target.generate(cur)
            return AttemptResult(
                prompt=cur,
                response=resp,
                status="completed",
                converter_chain=chain,
                executor_name=self.name,
                executor_kind="converter_method",
            )
        except Exception as e:
            return AttemptResult(
                prompt=cur,
                response=None,
                status="failed",
                error=f"{type(e).__name__}: {e}",
                converter_chain=chain,
                executor_name=self.name,
                executor_kind="converter_method",
            )
