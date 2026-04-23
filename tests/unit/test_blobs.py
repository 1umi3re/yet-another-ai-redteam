import pytest
from airedteam.storage.blobs import LocalBlobStore


@pytest.mark.asyncio
async def test_put_get_roundtrip(tmp_path):
    s = LocalBlobStore(tmp_path)
    p = await s.put("datasets/x.json", b'{"a":1}')
    assert p.startswith("datasets/")
    data = await s.get(p)
    assert data == b'{"a":1}'


@pytest.mark.asyncio
async def test_put_creates_subdirs(tmp_path):
    s = LocalBlobStore(tmp_path)
    p = await s.put("a/b/c/d.bin", b"x")
    assert (tmp_path / p).exists()
