import json
from datetime import UTC, datetime

import httpx
import pytest
import respx

from airedteam.services.run_monitor import DingTalkNotifier, RunMonitorService
from airedteam.storage import models
from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage.models import Attempt, Run, Score


class FakeNotifier:
    enabled = True

    def __init__(self):
        self.sent = []

    async def send_markdown(self, *, title: str, text: str) -> bool:
        self.sent.append({"title": title, "text": text})
        return True


@pytest.fixture
async def session_factory(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/monitor.db")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    return make_sessionmaker(engine)


@pytest.mark.asyncio
@respx.mock
async def test_dingtalk_notifier_sends_markdown_payload():
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=test"
    route = respx.post(webhook).mock(return_value=httpx.Response(200, json={"errcode": 0}))
    notifier = DingTalkNotifier(webhook_url=webhook, timeout_seconds=1)

    assert await notifier.send_markdown(title="title", text="### body") is True
    assert route.called
    payload = json.loads(route.calls[0].request.content.decode("utf-8"))
    assert payload["msgtype"] == "markdown"
    assert payload["markdown"] == {"title": "title", "text": "### body"}


def test_dingtalk_signed_url_adds_timestamp_and_signature():
    notifier = DingTalkNotifier(webhook_url="https://example.com/send?access_token=x", secret="secret")

    signed = notifier.signed_url(timestamp_ms=123)

    assert signed.startswith("https://example.com/send?access_token=x&timestamp=123&sign=")


@pytest.mark.asyncio
async def test_monitor_alerts_on_attempt_failure_rate_and_respects_cooldown(session_factory):
    async with session_factory() as s:
        s.add(
            Run(
                id="run-1",
                name="run",
                runspec_yaml="name: run",
                status="running",
                progress_total=2,
                progress_done=2,
                started_at=datetime.now(UTC).replace(tzinfo=None),
            )
        )
        s.add_all(
            [
                Attempt(
                    id="attempt-1",
                    run_id="run-1",
                    target_id="target",
                    target_name="target",
                    prompt_text="p1",
                    converter_chain=[],
                    status="failed",
                    error="target unavailable",
                ),
                Attempt(
                    id="attempt-2",
                    run_id="run-1",
                    target_id="target",
                    target_name="target",
                    prompt_text="p2",
                    response_text="ok",
                    converter_chain=[],
                    status="completed",
                ),
            ]
        )
        await s.commit()
    notifier = FakeNotifier()
    monitor = RunMonitorService(
        session_factory,
        notifier,
        min_samples=2,
        failure_rate_threshold=0.5,
        alert_cooldown_seconds=999,
    )

    await monitor.evaluate_running("run-1")
    await monitor.evaluate_running("run-1")

    assert len(notifier.sent) == 1
    assert notifier.sent[0]["title"] == "自动化测试运行失败率过高"
    assert "运行失败率: 50.0%" in notifier.sent[0]["text"]


@pytest.mark.asyncio
async def test_monitor_alerts_on_empty_responses_and_score_failures(session_factory):
    async with session_factory() as s:
        s.add(
            Run(
                id="run-2",
                name="run",
                runspec_yaml="name: run",
                status="running",
                progress_total=2,
                progress_done=2,
                started_at=datetime.now(UTC).replace(tzinfo=None),
            )
        )
        s.add_all(
            [
                Attempt(
                    id="attempt-1",
                    run_id="run-2",
                    target_id="target",
                    target_name="target",
                    prompt_text="p1",
                    response_text="",
                    converter_chain=[],
                    status="completed",
                ),
                Attempt(
                    id="attempt-2",
                    run_id="run-2",
                    target_id="target",
                    target_name="target",
                    prompt_text="p2",
                    response_text=" ",
                    converter_chain=[],
                    status="completed",
                ),
                Score(
                    id="score-1",
                    attempt_id="attempt-1",
                    scorer="llm_judge",
                    value_json={"status": "failed", "error": "judge unavailable"},
                ),
                Score(
                    id="score-2",
                    attempt_id="attempt-2",
                    scorer="llm_judge",
                    value_json={"status": "failed", "error": "judge unavailable"},
                ),
            ]
        )
        await s.commit()
    notifier = FakeNotifier()
    monitor = RunMonitorService(
        session_factory,
        notifier,
        min_samples=2,
        empty_response_rate_threshold=0.5,
        score_failure_rate_threshold=0.5,
    )

    await monitor.evaluate_running("run-2")

    titles = {item["title"] for item in notifier.sent}
    assert "自动化测试空响应率过高" in titles
    assert "自动化测试评分失败率过高" in titles
