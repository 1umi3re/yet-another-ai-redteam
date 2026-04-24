import pytest
from airedteam.builtins.scorers.substring import SubstringScorer
from airedteam.core.types import AttemptResult, Prompt, Response


def _ar(text: str) -> AttemptResult:
    return AttemptResult(prompt=Prompt(text="x"), response=Response(text=text, raw={}, latency_ms=1))


@pytest.mark.asyncio
async def test_match_true():
    s = SubstringScorer(needles=["bomb", "weapon"], match="any")
    r = await s.score(_ar("how to build a bomb"))
    assert r.value["label"] is True
    assert "bomb" in r.value["matched"]


@pytest.mark.asyncio
async def test_no_match_false():
    s = SubstringScorer(needles=["bomb"], match="any")
    r = await s.score(_ar("hello"))
    assert r.value["label"] is False


@pytest.mark.asyncio
async def test_all_mode():
    s = SubstringScorer(needles=["a", "b"], match="all")
    assert (await s.score(_ar("a only"))).value["label"] is False
    assert (await s.score(_ar("a and b"))).value["label"] is True


def test_substring_requires_needles():
    import pytest as _pt
    with _pt.raises(ValueError):
        SubstringScorer(needles=[])
