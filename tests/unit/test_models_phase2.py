from datetime import UTC, datetime

import pytest

from airedteam.storage import models
from airedteam.storage.db import make_engine, make_sessionmaker


@pytest.mark.asyncio
async def test_new_columns_roundtrip(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    SL = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    async with SL() as s:
        r = models.Run(name="m", runspec_yaml="{}", kind="manual")
        s.add(r)
        await s.commit()
        a = models.Attempt(run_id=r.id, target_id="t", target_name="t", prompt_text="p")
        s.add(a)
        await s.commit()
        now = datetime.now(UTC).replace(tzinfo=None)
        sc = models.Score(
            attempt_id=a.id,
            scorer="refusal",
            value_json={"label": True},
            reviewer_label=False,
            reviewer_notes="actually complied",
            reviewer_id="admin",
            reviewed_at=now,
        )
        s.add(sc)
        await s.commit()
        got = await s.get(models.Score, sc.id)
        assert got.reviewer_label is False
        assert got.reviewer_notes == "actually complied"
        assert got.reviewer_id == "admin"
        assert got.reviewed_at is not None
        run = await s.get(models.Run, r.id)
        assert run.kind == "manual"
