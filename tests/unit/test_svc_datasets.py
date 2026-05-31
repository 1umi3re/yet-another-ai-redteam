import json

import pytest

from airedteam.services.datasets import DatasetService
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.db import make_engine, make_sessionmaker


@pytest.mark.asyncio
async def test_create_from_json_upload(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine)
    async with engine.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    blob = LocalBlobStore(tmp_path / "blobs")
    svc = DatasetService(SessionLocal, blob)
    payload = json.dumps({"items": [{"prompt": "a"}, {"prompt": "b"}]}).encode()
    ds = await svc.create_json_upload(name="ds1", file_bytes=payload)
    assert ds.item_count == 2
    assert ds.blob_path
    assert ds.current_version == 1
    listed = await svc.list()
    assert len(listed) == 1

    content = await svc.content(ds.id)
    assert content["items"] == [{"prompt": "a"}, {"prompt": "b"}]

    versions = await svc.list_versions(ds.id)
    assert [v["version"] for v in versions] == [1]
    assert versions[0]["is_current"] is True

    updated = await svc.update_items(
        ds.id,
        items=[{"id": "next", "prompt": "c"}],
        note="replace fixture",
    )
    assert updated.current_version == 2
    assert updated.item_count == 1

    versions = await svc.list_versions(ds.id)
    assert [v["version"] for v in versions] == [2, 1]
    assert versions[0]["note"] == "replace fixture"
    assert versions[0]["is_current"] is True
    assert versions[1]["is_current"] is False

    restored = await svc.restore_version(ds.id, 1)
    assert restored.current_version == 1
    restored_content = await svc.content(ds.id)
    assert restored_content["items"] == [{"prompt": "a"}, {"prompt": "b"}]
