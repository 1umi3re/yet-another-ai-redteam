from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

from airedteam.core.score_status import score_status
from airedteam.runspec.models import RunSpec
from airedteam.storage.models import Attempt, Run, Score

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


class DingTalkNotifier:
    def __init__(
        self,
        *,
        webhook_url: str | None,
        secret: str | None = None,
        timeout_seconds: float = 5.0,
        enabled: bool = True,
    ) -> None:
        self.webhook_url = (webhook_url or "").strip()
        self.secret = (secret or "").strip() or None
        self.timeout_seconds = timeout_seconds
        self.enabled = enabled and bool(self.webhook_url)

    def configure(
        self,
        *,
        webhook_url: str | None,
        secret: str | None,
        timeout_seconds: float,
        enabled: bool,
    ) -> None:
        self.webhook_url = (webhook_url or "").strip()
        self.secret = (secret or "").strip() or None
        self.timeout_seconds = timeout_seconds
        self.enabled = enabled and bool(self.webhook_url)

    def signed_url(self, *, timestamp_ms: int | None = None) -> str:
        if not self.webhook_url or not self.secret:
            return self.webhook_url
        timestamp = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
        string_to_sign = f"{timestamp}\n{self.secret}".encode()
        digest = hmac.new(self.secret.encode(), string_to_sign, hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(digest).decode())
        separator = "&" if urllib.parse.urlparse(self.webhook_url).query else "?"
        return f"{self.webhook_url}{separator}timestamp={timestamp}&sign={sign}"

    async def send_markdown(self, *, title: str, text: str) -> bool:
        if not self.enabled:
            return False
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {"isAtAll": False},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(self.signed_url(), json=payload)
                resp.raise_for_status()
                try:
                    body = resp.json()
                except ValueError:
                    body = {}
                if isinstance(body, dict) and body.get("errcode", 0) not in (0, "0"):
                    logger.warning("DingTalk notification rejected: %s", body)
                    return False
                return True
        except Exception:
            logger.exception("failed to send DingTalk notification")
            return False


@dataclass(frozen=True)
class RunSpecSummary:
    targets: list[str]
    methods: list[str]
    scorers: list[str]
    dataset: str
    estimated_total: int | None


@dataclass(frozen=True)
class RunMetrics:
    run_id: str
    run_name: str
    status: str
    progress_done: int
    progress_total: int
    started_at: datetime | None
    finished_at: datetime | None
    error: str | None
    attempts: int
    failed_attempts: int
    completed_attempts: int
    empty_responses: int
    scored_attempts: int
    unscored_attempts: int
    refused_attempts: int
    complied_attempts: int
    scores: int
    failed_scores: int
    unknown_scores: int
    tokens_in: int
    tokens_out: int
    latency_ms: int
    duration_ms: int
    by_target: list[dict[str, Any]]
    by_executor: list[dict[str, Any]]
    by_target_executor: list[dict[str, Any]]
    recent_errors: list[str]

    @property
    def attack_success_rate(self) -> float | None:
        return self.complied_attempts / self.scored_attempts if self.scored_attempts else None

    @property
    def failed_attempt_rate(self) -> float | None:
        return self.failed_attempts / self.attempts if self.attempts else None

    @property
    def empty_response_rate(self) -> float | None:
        return self.empty_responses / self.completed_attempts if self.completed_attempts else None

    @property
    def score_failure_rate(self) -> float | None:
        return self.failed_scores / self.scores if self.scores else None


class RunMonitorService:
    def __init__(
        self,
        session_factory,
        notifier: DingTalkNotifier,
        *,
        enabled: bool = True,
        failure_rate_threshold: float = 0.2,
        empty_response_rate_threshold: float = 0.1,
        score_failure_rate_threshold: float = 0.2,
        min_samples: int = 20,
        no_progress_seconds: int = 600,
        alert_cooldown_seconds: int = 900,
    ) -> None:
        self._sf = session_factory
        self._notifier = notifier
        self._monitor_enabled = enabled
        self._failure_rate_threshold = failure_rate_threshold
        self._empty_response_rate_threshold = empty_response_rate_threshold
        self._score_failure_rate_threshold = score_failure_rate_threshold
        self._min_samples = max(1, min_samples)
        self._no_progress_seconds = max(1, no_progress_seconds)
        self._alert_cooldown_seconds = max(1, alert_cooldown_seconds)
        self._sent_alerts: dict[tuple[str, str], float] = {}
        self._progress_state: dict[str, tuple[int, float]] = {}

    @property
    def enabled(self) -> bool:
        return self._monitor_enabled and self._notifier.enabled

    def apply_config(self, config: dict[str, Any]) -> None:
        self._monitor_enabled = bool(config.get("monitor_enabled", True))
        self._failure_rate_threshold = float(config.get("monitor_failure_rate_threshold", 0.2))
        self._empty_response_rate_threshold = float(config.get("monitor_empty_response_rate_threshold", 0.1))
        self._score_failure_rate_threshold = float(config.get("monitor_score_failure_rate_threshold", 0.2))
        self._min_samples = max(1, int(config.get("monitor_min_samples", 20)))
        self._no_progress_seconds = max(1, int(config.get("monitor_no_progress_seconds", 600)))
        self._alert_cooldown_seconds = max(1, int(config.get("monitor_alert_cooldown_seconds", 900)))
        self._notifier.configure(
            webhook_url=config.get("dingtalk_webhook_url"),
            secret=config.get("dingtalk_secret"),
            timeout_seconds=float(config.get("dingtalk_timeout_seconds", 5.0)),
            enabled=self._monitor_enabled,
        )

    async def send_test_notification(self) -> bool:
        if not self.enabled:
            raise ValueError("monitoring delivery is not configured")
        return await self._notifier.send_markdown(
            title="airedteam 监控测试",
            text="### airedteam 监控测试\n- 钉钉机器人配置可用\n- 这是一条测试消息",
        )

    async def notify_created(self, run: Run, spec: RunSpec, summary: RunSpecSummary) -> None:
        await self._send_notice(
            "自动化测试任务创建",
            "\n".join(
                [
                    "### 自动化测试任务创建",
                    f"- 任务: {run.name}",
                    f"- Run ID: `{run.id}`",
                    f"- 测试目标: {_join(summary.targets)}",
                    f"- 测试方法: {_join(summary.methods)}",
                    f"- 评分器: {_join(summary.scorers)}",
                    f"- 数据集: {summary.dataset}",
                    f"- 预估测试条数: {_format_count(summary.estimated_total)}",
                    f"- 并发: {spec.concurrency}",
                    f"- 超时: {_format_timeout(spec.timeout_seconds)}",
                ]
            ),
        )

    async def notify_started(
        self,
        run_id: str,
        *,
        spec: RunSpec,
        summary: RunSpecSummary,
        progress_total: int,
        filtered_count: int,
    ) -> None:
        self._progress_state[run_id] = (0, time.monotonic())
        await self._send_notice(
            "自动化测试任务启动",
            "\n".join(
                [
                    "### 自动化测试任务启动",
                    f"- Run ID: `{run_id}`",
                    f"- 测试目标: {_join(summary.targets)}",
                    f"- 测试方法: {_join(summary.methods)}",
                    f"- 准确测试条数: {progress_total}",
                    f"- 语言过滤数: {filtered_count}",
                    f"- 评分器: {_join(summary.scorers)}",
                    f"- 并发: {spec.concurrency}",
                ]
            ),
        )
        if progress_total == 0:
            await self._send_alert(
                run_id,
                "zero_effective_work",
                "自动化测试有效测试量为 0",
                "\n".join(
                    [
                        "### 自动化测试有效测试量为 0",
                        f"- Run ID: `{run_id}`",
                        f"- 测试目标: {_join(summary.targets)}",
                        f"- 测试方法: {_join(summary.methods)}",
                        "- 可能原因: 数据集语言与所选测试方法不匹配，或运行规格未生成任何 work item",
                    ]
                ),
            )

    async def notify_finished(self, run_id: str) -> None:
        metrics = await self._metrics(run_id)
        if metrics is None:
            return
        title = "自动化测试任务结束" if metrics.status == "completed" else "自动化测试任务异常结束"
        average_latency_ms = metrics.latency_ms // metrics.completed_attempts if metrics.completed_attempts else None
        lines = [
            f"### {title}",
            f"- 任务: {metrics.run_name}",
            f"- Run ID: `{metrics.run_id}`",
            f"- 状态: {metrics.status}",
            f"- 进度: {metrics.progress_done}/{metrics.progress_total}",
            f"- 总测试数: {metrics.attempts}",
            f"- 攻击成功: {metrics.complied_attempts} ({_format_rate(metrics.attack_success_rate)})",
            f"- 运行失败: {metrics.failed_attempts} ({_format_rate(metrics.failed_attempt_rate)})",
            f"- 有效评分: {metrics.scored_attempts}",
            f"- 未评分: {metrics.unscored_attempts}",
            f"- 评分失败: {metrics.failed_scores} ({_format_rate(metrics.score_failure_rate)})",
            f"- 空响应: {metrics.empty_responses} ({_format_rate(metrics.empty_response_rate)})",
            f"- 耗时: {_format_ms(metrics.duration_ms)}",
            f"- 平均延迟: {_format_ms(average_latency_ms)}",
            f"- Token 输入/输出: {metrics.tokens_in}/{metrics.tokens_out}",
        ]
        if metrics.error:
            lines.append(f"- 错误: {_truncate(metrics.error, 300)}")
        lines.extend(_top_lines("高风险目标", metrics.by_target))
        lines.extend(_top_lines("高风险方法", metrics.by_executor))
        lines.extend(_top_lines("高风险组合", metrics.by_target_executor))
        if metrics.recent_errors:
            lines.append("- 最近错误:")
            lines.extend(f"  - {_truncate(item, 180)}" for item in metrics.recent_errors[:3])
        await self._send_notice(title, "\n".join(lines))
        if metrics.status == "failed":
            await self._send_alert(run_id, "run_failed", "自动化测试任务失败", "\n".join(lines))

    async def evaluate_running(self, run_id: str) -> None:
        metrics = await self._metrics(run_id)
        if metrics is None or metrics.status != "running":
            return
        await self._check_thresholds(metrics)
        await self._check_no_progress(metrics)

    async def watch_run(self, run_id: str) -> None:
        if not self.enabled:
            return
        interval = min(60.0, max(1.0, self._no_progress_seconds / 2))
        while True:
            await asyncio.sleep(interval)
            metrics = await self._metrics(run_id)
            if metrics is None or metrics.status in TERMINAL_STATUSES or metrics.status == "paused":
                return
            await self._check_no_progress(metrics)

    async def _check_thresholds(self, metrics: RunMetrics) -> None:
        if metrics.attempts >= self._min_samples and (metrics.failed_attempt_rate or 0) >= self._failure_rate_threshold:
            await self._send_metric_alert(
                metrics,
                "attempt_failure_rate",
                "自动化测试运行失败率过高",
                "运行失败率",
                metrics.failed_attempt_rate,
                self._failure_rate_threshold,
            )
        if (
            metrics.completed_attempts >= self._min_samples
            and (metrics.empty_response_rate or 0) >= self._empty_response_rate_threshold
        ):
            await self._send_metric_alert(
                metrics,
                "empty_response_rate",
                "自动化测试空响应率过高",
                "空响应率",
                metrics.empty_response_rate,
                self._empty_response_rate_threshold,
            )
        if (
            metrics.scores >= self._min_samples
            and (metrics.score_failure_rate or 0) >= self._score_failure_rate_threshold
        ):
            await self._send_metric_alert(
                metrics,
                "score_failure_rate",
                "自动化测试评分失败率过高",
                "评分失败率",
                metrics.score_failure_rate,
                self._score_failure_rate_threshold,
            )
        if metrics.progress_total == 0 and metrics.status == "running":
            await self._send_alert(
                metrics.run_id,
                "zero_effective_work",
                "自动化测试有效测试量为 0",
                "\n".join(
                    [
                        "### 自动化测试有效测试量为 0",
                        f"- 任务: {metrics.run_name}",
                        f"- Run ID: `{metrics.run_id}`",
                        "- 可能原因: 数据集语言与所选测试方法不匹配，或运行规格未生成任何 work item",
                    ]
                ),
            )

    async def _check_no_progress(self, metrics: RunMetrics) -> None:
        if metrics.status != "running":
            return
        now = time.monotonic()
        previous = self._progress_state.get(metrics.run_id)
        if previous is None or previous[0] != metrics.progress_done:
            self._progress_state[metrics.run_id] = (metrics.progress_done, now)
            return
        if metrics.progress_done >= metrics.progress_total and metrics.progress_total > 0:
            return
        if now - previous[1] < self._no_progress_seconds:
            return
        await self._send_alert(
            metrics.run_id,
            "no_progress",
            "自动化测试长时间无进展",
            "\n".join(
                [
                    "### 自动化测试长时间无进展",
                    f"- 任务: {metrics.run_name}",
                    f"- Run ID: `{metrics.run_id}`",
                    f"- 当前进度: {metrics.progress_done}/{metrics.progress_total}",
                    f"- 无进展时长: >= {self._no_progress_seconds}s",
                ]
            ),
        )

    async def _send_metric_alert(
        self,
        metrics: RunMetrics,
        alert_type: str,
        title: str,
        label: str,
        value: float | None,
        threshold: float,
    ) -> None:
        lines = [
            f"### {title}",
            f"- 任务: {metrics.run_name}",
            f"- Run ID: `{metrics.run_id}`",
            f"- {label}: {_format_rate(value)}",
            f"- 阈值: {_format_rate(threshold)}",
            f"- 进度: {metrics.progress_done}/{metrics.progress_total}",
            f"- 运行失败/空响应/评分失败: {metrics.failed_attempts}/{metrics.empty_responses}/{metrics.failed_scores}",
        ]
        if metrics.recent_errors:
            lines.append("- 最近错误:")
            lines.extend(f"  - {_truncate(item, 180)}" for item in metrics.recent_errors[:3])
        await self._send_alert(metrics.run_id, alert_type, title, "\n".join(lines))

    async def _send_notice(self, title: str, text: str) -> None:
        if not self.enabled:
            return
        await self._notifier.send_markdown(title=title, text=text)

    async def _send_alert(self, run_id: str, alert_type: str, title: str, text: str) -> None:
        if not self.enabled:
            return
        now = time.monotonic()
        key = (run_id, alert_type)
        last_sent = self._sent_alerts.get(key)
        if last_sent is not None and now - last_sent < self._alert_cooldown_seconds:
            return
        if await self._notifier.send_markdown(title=title, text=text):
            self._sent_alerts[key] = now

    async def _metrics(self, run_id: str) -> RunMetrics | None:
        async with self._sf() as s:
            run = await s.get(Run, run_id)
            if run is None:
                return None
            attempts = (
                (await s.execute(select(Attempt).where(Attempt.run_id == run_id).order_by(Attempt.created_at)))
                .scalars()
                .all()
            )
            scores = (
                (
                    await s.execute(
                        select(Score).join(Attempt, Score.attempt_id == Attempt.id).where(Attempt.run_id == run_id)
                    )
                )
                .scalars()
                .all()
            )

        scores_by_attempt = _scores_by_attempt(scores)
        by_target: dict[str, dict[str, Any]] = {}
        by_executor: dict[str, dict[str, Any]] = {}
        by_target_executor: dict[str, dict[str, Any]] = {}
        failed_attempts = 0
        completed_attempts = 0
        empty_responses = 0
        scored_attempts = 0
        refused_attempts = 0
        complied_attempts = 0
        tokens_in = 0
        tokens_out = 0
        latency_ms = 0
        recent_errors: list[str] = []

        for attempt in attempts:
            if attempt.status == "failed":
                failed_attempts += 1
                if attempt.error:
                    recent_errors.append(f"{_attempt_label(attempt)}: {attempt.error}")
            if attempt.status == "completed":
                completed_attempts += 1
                if _is_empty_response(attempt):
                    empty_responses += 1
            tokens_in += attempt.tokens_in or 0
            tokens_out += attempt.tokens_out or 0
            latency_ms += attempt.latency_ms or 0
            verdict = _attempt_verdict(scores_by_attempt.get(attempt.id, []))
            if verdict == "refused":
                scored_attempts += 1
                refused_attempts += 1
            elif verdict == "complied":
                scored_attempts += 1
                complied_attempts += 1

            target_key = attempt.target_name or attempt.target_id or "(unknown)"
            executor_key = _attempt_executor_name(attempt)
            _add_bucket(by_target.setdefault(target_key, _empty_bucket(target_key)), attempt, verdict)
            _add_bucket(by_executor.setdefault(executor_key, _empty_bucket(executor_key)), attempt, verdict)
            _add_bucket(
                by_target_executor.setdefault(
                    f"{target_key} x {executor_key}",
                    _empty_bucket(f"{target_key} x {executor_key}"),
                ),
                attempt,
                verdict,
            )

        failed_scores = 0
        unknown_scores = 0
        for score in scores:
            if score_status(score.value_json) == "failed":
                failed_scores += 1
                value = score.value_json or {}
                if isinstance(value, dict) and value.get("error"):
                    recent_errors.append(f"score {score.scorer}: {value['error']}")
                continue
            if _score_verdict(score) is None:
                unknown_scores += 1

        duration_ms = _duration_ms(run.started_at, run.finished_at)
        return RunMetrics(
            run_id=run.id,
            run_name=run.name,
            status=run.status,
            progress_done=run.progress_done,
            progress_total=run.progress_total,
            started_at=run.started_at,
            finished_at=run.finished_at,
            error=run.error,
            attempts=len(attempts),
            failed_attempts=failed_attempts,
            completed_attempts=completed_attempts,
            empty_responses=empty_responses,
            scored_attempts=scored_attempts,
            unscored_attempts=max(0, len(attempts) - scored_attempts),
            refused_attempts=refused_attempts,
            complied_attempts=complied_attempts,
            scores=len(scores),
            failed_scores=failed_scores,
            unknown_scores=unknown_scores,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            duration_ms=duration_ms or 0,
            by_target=_finish_buckets(by_target),
            by_executor=_finish_buckets(by_executor),
            by_target_executor=_finish_buckets(by_target_executor),
            recent_errors=recent_errors[-5:],
        )


class MonitoringConfigStore:
    _CONFIG_KEY = Path("settings") / "monitoring.json"

    def __init__(self, *, settings, monitor: RunMonitorService, root: Path) -> None:
        self._monitor = monitor
        self._path = Path(root) / self._CONFIG_KEY
        self._config = self._defaults(settings)
        self._config.update(self._load())
        self._monitor.apply_config(self._config)

    async def get_public(self) -> dict[str, Any]:
        return self._public_config()

    async def update(self, patch: dict[str, Any]) -> dict[str, Any]:
        config = dict(self._config)
        for key in (
            "monitor_enabled",
            "dingtalk_timeout_seconds",
            "monitor_failure_rate_threshold",
            "monitor_empty_response_rate_threshold",
            "monitor_score_failure_rate_threshold",
            "monitor_min_samples",
            "monitor_no_progress_seconds",
            "monitor_alert_cooldown_seconds",
        ):
            if key in patch and patch[key] is not None:
                config[key] = patch[key]

        if patch.get("clear_dingtalk_webhook_url"):
            config["dingtalk_webhook_url"] = None
        elif "dingtalk_webhook_url" in patch and patch["dingtalk_webhook_url"] is not None:
            config["dingtalk_webhook_url"] = _blank_to_none(patch["dingtalk_webhook_url"])

        if patch.get("clear_dingtalk_secret"):
            config["dingtalk_secret"] = None
        elif "dingtalk_secret" in patch and patch["dingtalk_secret"] is not None:
            config["dingtalk_secret"] = _blank_to_none(patch["dingtalk_secret"])

        self._config = config
        self._monitor.apply_config(self._config)
        await self._write()
        return self._public_config()

    def _defaults(self, settings) -> dict[str, Any]:
        return {
            "monitor_enabled": settings.monitor_enabled,
            "dingtalk_webhook_url": settings.dingtalk_webhook_url,
            "dingtalk_secret": settings.dingtalk_secret,
            "dingtalk_timeout_seconds": settings.dingtalk_timeout_seconds,
            "monitor_failure_rate_threshold": settings.monitor_failure_rate_threshold,
            "monitor_empty_response_rate_threshold": settings.monitor_empty_response_rate_threshold,
            "monitor_score_failure_rate_threshold": settings.monitor_score_failure_rate_threshold,
            "monitor_min_samples": settings.monitor_min_samples,
            "monitor_no_progress_seconds": settings.monitor_no_progress_seconds,
            "monitor_alert_cooldown_seconds": settings.monitor_alert_cooldown_seconds,
        }

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("failed to read monitoring config")
            return {}
        return raw if isinstance(raw, dict) else {}

    async def _write(self) -> None:
        payload = json.dumps(self._config, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        await asyncio.to_thread(self._path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(self._path.write_bytes, payload)

    def _public_config(self) -> dict[str, Any]:
        webhook_url = self._config.get("dingtalk_webhook_url")
        secret = self._config.get("dingtalk_secret")
        monitor_enabled = bool(self._config.get("monitor_enabled"))
        return {
            "monitor_enabled": monitor_enabled,
            "delivery_enabled": self._monitor.enabled,
            "dingtalk_webhook_configured": bool(webhook_url),
            "dingtalk_webhook_url_display": _mask_url(webhook_url),
            "dingtalk_secret_configured": bool(secret),
            "dingtalk_timeout_seconds": self._config.get("dingtalk_timeout_seconds"),
            "monitor_failure_rate_threshold": self._config.get("monitor_failure_rate_threshold"),
            "monitor_empty_response_rate_threshold": self._config.get("monitor_empty_response_rate_threshold"),
            "monitor_score_failure_rate_threshold": self._config.get("monitor_score_failure_rate_threshold"),
            "monitor_min_samples": self._config.get("monitor_min_samples"),
            "monitor_no_progress_seconds": self._config.get("monitor_no_progress_seconds"),
            "monitor_alert_cooldown_seconds": self._config.get("monitor_alert_cooldown_seconds"),
        }


def _scores_by_attempt(scores: list[Score]) -> dict[str, list[Score]]:
    out: dict[str, list[Score]] = {}
    for score in scores:
        out.setdefault(score.attempt_id, []).append(score)
    for items in out.values():
        items.sort(key=lambda s: s.created_at)
    return out


def _score_verdict(score: Score) -> str | None:
    if score.reviewer_label is not None:
        return "refused" if score.reviewer_label else "complied"
    value = score.value_json or {}
    if score_status(value) == "failed":
        return None
    if isinstance(value.get("attack_success"), bool):
        return "complied" if value["attack_success"] else "refused"
    if isinstance(value.get("label"), bool):
        if score.scorer == "refusal":
            return "refused" if value["label"] else "complied"
        return "complied" if value["label"] else "refused"
    return None


def _attempt_verdict(scores: list[Score]) -> str:
    if not scores:
        return "unscored"
    reviewed = [s for s in scores if s.reviewer_label is not None]
    scored = [s for s in scores if _score_verdict(s) is not None]
    chosen = reviewed[0] if reviewed else scored[0] if scored else scores[0]
    return _score_verdict(chosen) or "unscored"


def _attempt_executor_name(attempt: Attempt) -> str:
    if attempt.executor_name:
        return attempt.executor_name
    chain = attempt.converter_chain or []
    if chain:
        return " -> ".join(chain)
    return "single_turn"


def _attempt_label(attempt: Attempt) -> str:
    return f"{attempt.target_name or attempt.target_id}/{_attempt_executor_name(attempt)}/{attempt.id}"


def _is_empty_response(attempt: Attempt) -> bool:
    if attempt.status != "completed":
        return False
    if attempt.response_blob_path:
        return False
    return attempt.response_text is None or not attempt.response_text.strip()


def _empty_bucket(key: str) -> dict[str, Any]:
    return {
        "key": key,
        "attempts": 0,
        "scored": 0,
        "complied": 0,
        "refused": 0,
        "failed": 0,
        "unscored": 0,
    }


def _add_bucket(bucket: dict[str, Any], attempt: Attempt, verdict: str) -> None:
    bucket["attempts"] += 1
    if attempt.status == "failed":
        bucket["failed"] += 1
    if verdict == "complied":
        bucket["scored"] += 1
        bucket["complied"] += 1
    elif verdict == "refused":
        bucket["scored"] += 1
        bucket["refused"] += 1
    else:
        bucket["unscored"] += 1


def _finish_buckets(buckets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for bucket in buckets.values():
        scored = bucket["scored"]
        bucket["success_rate"] = bucket["complied"] / scored if scored else None
        rows.append(bucket)
    rows.sort(
        key=lambda row: (
            row.get("success_rate") is not None,
            row.get("success_rate") or 0,
            row.get("scored") or 0,
        ),
        reverse=True,
    )
    return rows


def _duration_ms(started_at: datetime | None, finished_at: datetime | None) -> int | None:
    if started_at is None or finished_at is None:
        return None
    return max(0, int((finished_at - started_at).total_seconds() * 1000))


def _top_lines(label: str, rows: list[dict[str, Any]]) -> list[str]:
    top = [row for row in rows if row.get("scored", 0) > 0][:3]
    if not top:
        return []
    lines = [f"- {label}:"]
    for row in top:
        lines.append(
            f"  - {row['key']}: {_format_rate(row.get('success_rate'))} "
            f"({row.get('complied', 0)}/{row.get('scored', 0)})"
        )
    return lines


def _join(values: list[str]) -> str:
    return ", ".join(values) if values else "(none)"


def _format_count(value: int | None) -> str:
    return str(value) if value is not None else "未知"


def _format_timeout(value: float | None) -> str:
    return "未设置" if value is None else f"{value:g}s"


def _format_rate(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def _format_ms(value: int | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1000:
        return f"{value / 1000:.1f}s"
    return f"{value}ms"


def _truncate(value: str, limit: int) -> str:
    text = str(value).strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _blank_to_none(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mask_url(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    parsed = urllib.parse.urlsplit(text)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    masked_query = urllib.parse.urlencode(
        [(key, "***" if "token" in key.lower() or "key" in key.lower() else val) for key, val in query]
    )
    masked = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, masked_query, parsed.fragment))
    if len(masked) <= 100:
        return masked
    return masked[:60] + "..." + masked[-25:]
