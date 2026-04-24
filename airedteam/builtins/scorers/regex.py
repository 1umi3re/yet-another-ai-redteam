from __future__ import annotations
import re
from airedteam.core.types import AttemptResult, ScoreResult


_FLAG_MAP = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL}


class RegexScorer:
    """Label true when the response matches the given regex pattern.

    Required: ``pattern`` (non-empty regex). Optional: ``flags`` like ``"ims"``."""
    name = "regex"

    def __init__(self, *, pattern: str | None = None, flags: str = "") -> None:
        if not pattern:
            raise ValueError("regex scorer requires a non-empty 'pattern' param")
        f = 0
        for c in flags:
            f |= _FLAG_MAP.get(c.lower(), 0)
        self._re = re.compile(pattern, f)

    async def score(self, attempt: AttemptResult) -> ScoreResult:
        text = (attempt.response.text if attempt.response else "") or ""
        m = self._re.search(text)
        label = bool(m)
        return ScoreResult(
            scorer=self.name,
            value={"label": label, "attack_success": label, "match": m.group(0) if m else None},
        )
