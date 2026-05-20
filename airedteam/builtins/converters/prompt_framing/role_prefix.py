from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class RolePrefixConverter:
    """Prefix the payload with an assumed role."""

    name = "role_prefix"

    def __init__(self, *, role: str = "authorized security reviewer") -> None:
        self.role = role or "authorized security reviewer"

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, f"As a {self.role}, {prompt.text}")
