import json, pytest
from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.services.datasets import DatasetService


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
    listed = await svc.list()
    assert len(listed) == 1
