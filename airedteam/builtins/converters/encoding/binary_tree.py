from __future__ import annotations

import json
from typing import Any

from airedteam.core.types import Prompt


class BinaryTreeConverter:
    """Encode words as a balanced binary tree in JSON form."""

    name = "binary_tree"

    async def convert(self, prompt: Prompt) -> Prompt:
        words = prompt.text.split()
        tree = self._build_tree(words, 0, len(words) - 1)
        return Prompt(text=json.dumps(tree), metadata=prompt.metadata)

    def _build_tree(self, words: list[str], start: int, end: int) -> dict[str, Any] | None:
        if start > end:
            return None
        mid = (start + end) // 2
        return {
            "value": words[mid],
            "left": self._build_tree(words, start, mid - 1),
            "right": self._build_tree(words, mid + 1, end),
        }
