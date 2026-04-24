import pytest
from airedteam.engine.sampling import SampledDataset
from airedteam.core.types import Prompt


class FakeDataset:
    """Fake dataset for testing."""
    name = "fake_dataset"
    
    def __init__(self, items: list[str]):
        self._items = items
    
    async def __aiter__(self):
        for item in self._items:
            yield Prompt(text=item)
    
    async def size(self) -> int:
        return len(self._items)


@pytest.mark.asyncio
async def test_sampled_dataset_limit():
    """Test limiting the number of items."""
    ds = FakeDataset([f"item-{i}" for i in range(10)])
    sampled = SampledDataset(ds, limit=3)
    
    items = []
    async for p in sampled:
        items.append(p.text)
    
    assert len(items) == 3
    assert items == ["item-0", "item-1", "item-2"]
    
    # Check size estimation
    assert await sampled.size() == 3


@pytest.mark.asyncio
async def test_sampled_dataset_shuffle_deterministic():
    """Test shuffle is deterministic with same seed."""
    ds1 = FakeDataset([f"item-{i}" for i in range(10)])
    sampled1 = SampledDataset(ds1, shuffle=True, seed=42)
    
    items1 = []
    async for p in sampled1:
        items1.append(p.text)
    
    # Run again with same seed
    ds2 = FakeDataset([f"item-{i}" for i in range(10)])
    sampled2 = SampledDataset(ds2, shuffle=True, seed=42)
    
    items2 = []
    async for p in sampled2:
        items2.append(p.text)
    
    assert items1 == items2
    assert len(items1) == 10
    # Verify it's actually shuffled (not the original order)
    original = [f"item-{i}" for i in range(10)]
    assert items1 != original


@pytest.mark.asyncio
async def test_sampled_dataset_limit_and_shuffle():
    """Test combining limit and shuffle."""
    ds = FakeDataset([f"item-{i}" for i in range(10)])
    sampled = SampledDataset(ds, limit=3, shuffle=True, seed=0)
    
    items = []
    async for p in sampled:
        items.append(p.text)
    
    # Should return exactly 3 items
    assert len(items) == 3
    # Items should be a subset of the original
    original = [f"item-{i}" for i in range(10)]
    for item in items:
        assert item in original


@pytest.mark.asyncio
async def test_sampled_dataset_no_limit_no_shuffle():
    """Test passthrough behavior when no sampling configured."""
    ds = FakeDataset([f"item-{i}" for i in range(5)])
    sampled = SampledDataset(ds)
    
    items = []
    async for p in sampled:
        items.append(p.text)
    
    assert len(items) == 5
    assert items == [f"item-{i}" for i in range(5)]


@pytest.mark.asyncio
async def test_sampled_dataset_limit_exceeds_size():
    """Test when limit is greater than dataset size."""
    ds = FakeDataset([f"item-{i}" for i in range(3)])
    sampled = SampledDataset(ds, limit=10)
    
    items = []
    async for p in sampled:
        items.append(p.text)
    
    # Should return all 3 items
    assert len(items) == 3
    assert await sampled.size() == 3


@pytest.mark.asyncio
async def test_sampled_dataset_different_seeds():
    """Test that different seeds produce different shuffles."""
    ds1 = FakeDataset([f"item-{i}" for i in range(10)])
    sampled1 = SampledDataset(ds1, shuffle=True, seed=42)
    
    items1 = []
    async for p in sampled1:
        items1.append(p.text)
    
    ds2 = FakeDataset([f"item-{i}" for i in range(10)])
    sampled2 = SampledDataset(ds2, shuffle=True, seed=99)
    
    items2 = []
    async for p in sampled2:
        items2.append(p.text)
    
    # Both should have all 10 items but in different order
    assert len(items1) == 10
    assert len(items2) == 10
    assert sorted(items1) == sorted(items2)
    assert items1 != items2  # Different shuffle
