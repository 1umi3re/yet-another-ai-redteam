from __future__ import annotations
from typing import Literal
from airedteam.core.types import AttemptResult, ScoreResult


class SubstringScorer:
    name = "substring"
    def __init__(self, *, needles: list[str], match: Literal["any", "all"] = "any", case_sensitive: bool = False) -> None:
        self.needles = needles
        self.match = match
        self.case_sensitive = case_sensitive

    async def score(self, attempt: AttemptResult) -> ScoreResult:
        text = (attempt.response.text if attempt.response else "") or ""
        hay = text if self.case_sensitive else text.lower()
        needles = self.needles if self.case_sensitive else [n.lower() for n in self.needles]
        matched = [n for n in needles if n in hay]
        label = (len(matched) > 0) if self.match == "any" else (len(matched) == len(needles))
        return ScoreResult(scorer=self.name, value={"label": label, "matched": matched})
