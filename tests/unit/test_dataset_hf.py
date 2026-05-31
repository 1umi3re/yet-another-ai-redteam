import pytest

from airedteam.builtins.datasets.hf import HuggingFaceDataset


@pytest.mark.asyncio
async def test_iterates_with_fake_loader(monkeypatch):
    fake_rows = [{"prompt": "p1"}, {"prompt": "p2"}, {"prompt": "p3"}]

    async def fake_load(self):
        for i, r in enumerate(fake_rows):
            yield i, r

    monkeypatch.setattr(HuggingFaceDataset, "_iter_rows", fake_load)
    ds = HuggingFaceDataset(repo="walledai/AdvBench", split="train", prompt_field="prompt", limit=2)
    items = [p async for p in ds]
    assert [i.text for i in items] == ["p1", "p2"]
