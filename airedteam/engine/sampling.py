from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from airedteam.core.plugins import Dataset


class SampledDataset:
    """Wrapper that applies sampling (limit, shuffle) to a dataset."""
    
    def __init__(self, inner: Dataset, *, limit: int | None = None, shuffle: bool = False, seed: int | None = None):
        self._inner = inner
        self._limit = limit
        self._shuffle = shuffle
        self._seed = seed
        self.name = getattr(inner, "name", "sampled_dataset")

    async def __aiter__(self):
        items = []
        async for p in self._inner:
            items.append(p)
            # If not shuffling and we've hit the limit, stop early
            if not self._shuffle and self._limit is not None and len(items) >= self._limit:
                break
        
        if self._shuffle:
            import random
            rng = random.Random(self._seed)
            rng.shuffle(items)
        
        if self._limit is not None:
            items = items[: self._limit]
        
        for p in items:
            yield p

    async def size(self) -> int | None:
        """Best-effort size estimate."""
        inner_size = await self._inner.size() if hasattr(self._inner, "size") else None
        if self._limit is None:
            return inner_size
        return self._limit if inner_size is None else min(inner_size, self._limit)
