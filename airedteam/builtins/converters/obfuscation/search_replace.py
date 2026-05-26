from __future__ import annotations

import re

from airedteam.core.types import Prompt


class SearchReplaceConverter:
    """Replace literal or regex matches in prompt text."""

    name = "search_replace"

    def __init__(
        self,
        *,
        search: str = "__AIREDTEAM_NO_MATCH__",
        replace: str = "",
        use_regex: bool = False,
        case_sensitive: bool = True,
    ) -> None:
        if not search:
            raise ValueError("search_replace requires a non-empty 'search' param")
        self.search = search
        self.replace = replace
        self.use_regex = use_regex
        self.case_sensitive = case_sensitive

    async def convert(self, prompt: Prompt) -> Prompt:
        if self.use_regex or not self.case_sensitive:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            pattern = self.search if self.use_regex else re.escape(self.search)
            text = re.sub(pattern, self.replace, prompt.text, flags=flags)
        else:
            text = prompt.text.replace(self.search, self.replace)
        return Prompt(text=text, metadata=prompt.metadata)
