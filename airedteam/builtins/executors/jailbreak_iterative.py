from __future__ import annotations

from airedteam.builtins.executors.pair import PAIRExecutor
from airedteam.core.plugins import Target


class JailbreakIterativeExecutor(PAIRExecutor):
    """Promptfoo-style iterative jailbreak executor backed by the PAIR loop."""

    name = "jailbreak_iterative"

    def __init__(
        self,
        *,
        attacker: Target | None = None,
        judge: Target | None = None,
        goal: str = "",
        max_turns: int = 5,
        success_threshold: int = 8,
        prompt_assets=None,
        attacker_prompt_override_id: str | None = None,
        judge_prompt_override_id: str | None = None,
        use_builtin_prompt: bool = False,
    ) -> None:
        super().__init__(
            attacker=attacker,
            judge=judge,
            goal=goal,
            max_turns=max_turns,
            success_threshold=success_threshold,
            prompt_assets=prompt_assets,
            attacker_prompt_override_id=attacker_prompt_override_id,
            judge_prompt_override_id=judge_prompt_override_id,
            use_builtin_prompt=use_builtin_prompt,
        )
