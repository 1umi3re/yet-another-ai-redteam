import asyncio
import pytest
from airedteam.engine.progress import ProgressBus


@pytest.mark.asyncio
async def test_publish_delivers_to_subscribers():
    bus = ProgressBus()
    q = bus.subscribe("r1")
    await bus.publish("r1", {"type": "hello"})
    evt = await asyncio.wait_for(q.get(), timeout=1.0)
    assert evt == {"type": "hello"}
    bus.unsubscribe("r1", q)


@pytest.mark.asyncio
async def test_publish_no_subscribers_noop():
    bus = ProgressBus()
    await bus.publish("nobody", {"x": 1})
