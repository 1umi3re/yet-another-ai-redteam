import json

import pytest

from airedteam.builtins.datasets.json_upload import JsonUploadDataset
from airedteam.storage.blobs import LocalBlobStore


@pytest.mark.asyncio
async def test_loads_prompts(tmp_path):
    blob = LocalBlobStore(tmp_path)
    payload = json.dumps({"items": [{"id": "a", "prompt": "hi"}, {"id": "b", "prompt": "yo"}]})
    key = await blob.put("ds/x.json", payload.encode())
    ds = JsonUploadDataset(blob_store=blob, blob_path=key)
    items = [p async for p in ds]
    assert [i.text for i in items] == ["hi", "yo"]
    assert items[0].metadata["id"] == "a"
    assert await ds.size() == 2


@pytest.mark.asyncio
async def test_supports_plain_string_array(tmp_path):
    blob = LocalBlobStore(tmp_path)
    key = await blob.put("ds/y.json", json.dumps(["one", "two"]).encode())
    ds = JsonUploadDataset(blob_store=blob, blob_path=key)
    items = [p async for p in ds]
    assert [i.text for i in items] == ["one", "two"]
