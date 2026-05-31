from __future__ import annotations

from airedteam.core.types import AttemptResult, Prompt
from airedteam.engine.input_limits import ensure_text_within_target_limit


class SingleTurnExecutor:
    name = "single_turn"

    async def run(self, prompt: Prompt, target, converters: list) -> AttemptResult:
        chain: list[str] = []
        cur = prompt
        for c in converters:
            cur = await c.convert(cur)
            chain.append(c.name)
        try:
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
            )
        except Exception as e:
            return AttemptResult(
                prompt=cur,
                response=None,
                status="failed",
                error=f"{type(e).__name__}: {e}",
                converter_chain=chain,
            )
