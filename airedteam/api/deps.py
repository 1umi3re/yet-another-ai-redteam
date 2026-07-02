from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

from airedteam.config import Settings, get_settings
from airedteam.engine.progress import ProgressBus
from airedteam.services.attack_method_categories import AttackMethodCategoryService
from airedteam.services.converters import ConverterChainService
from airedteam.services.custom_scenarios import CustomScenarioService
from airedteam.services.datasets import DatasetService
from airedteam.services.manual import ManualService
from airedteam.services.prompt_assets import PromptAssetService
from airedteam.services.run_monitor import DingTalkNotifier, MonitoringConfigStore, RunMonitorService
from airedteam.services.runs import RunService
from airedteam.services.target_configs import TargetConfigService
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage.secretbox import SecretBox

from .auth import verify_token


@dataclass
class AppState:
    settings: Settings
    session_factory: object
    blob_store: LocalBlobStore
    secret_box: SecretBox
    bus: ProgressBus
    targets: TargetConfigService
    datasets: DatasetService
    converters: ConverterChainService
    prompt_assets: PromptAssetService
    monitor: RunMonitorService
    monitor_config: MonitoringConfigStore
    runs: RunService
    manual: ManualService
    attack_methods: AttackMethodCategoryService
    custom_scenarios: CustomScenarioService


def build_state(settings: Settings | None = None) -> AppState:
    s = settings or get_settings()
    engine = make_engine(s.database_url)
    SessionLocal = make_sessionmaker(engine)
    blob = LocalBlobStore(s.blob_dir)
    box = SecretBox(s.master_key)
    bus = ProgressBus()
    targets = TargetConfigService(SessionLocal, box)
    datasets = DatasetService(SessionLocal, blob)
    prompt_assets = PromptAssetService(SessionLocal, blob)
    converters = ConverterChainService(targets, prompt_assets)
    notifier = DingTalkNotifier(
        webhook_url=s.dingtalk_webhook_url,
        secret=s.dingtalk_secret,
        timeout_seconds=s.dingtalk_timeout_seconds,
        enabled=s.monitor_enabled,
    )
    monitor = RunMonitorService(
        SessionLocal,
        notifier,
        enabled=s.monitor_enabled,
        failure_rate_threshold=s.monitor_failure_rate_threshold,
        empty_response_rate_threshold=s.monitor_empty_response_rate_threshold,
        score_failure_rate_threshold=s.monitor_score_failure_rate_threshold,
        min_samples=s.monitor_min_samples,
        no_progress_seconds=s.monitor_no_progress_seconds,
        alert_cooldown_seconds=s.monitor_alert_cooldown_seconds,
    )
    monitor_config = MonitoringConfigStore(settings=s, monitor=monitor, root=s.blob_dir)
    runs = RunService(
        SessionLocal,
        blob,
        box,
        targets,
        datasets,
        bus,
        prompt_assets=prompt_assets,
        response_inline_max_bytes=s.response_inline_max_bytes,
        max_concurrency=s.max_concurrency,
        monitor=monitor,
    )
    manual = ManualService(SessionLocal, blob, targets, converters, prompt_assets)
    attack_methods = AttackMethodCategoryService(SessionLocal)
    custom_scenarios = CustomScenarioService(SessionLocal)
    return AppState(
        s,
        SessionLocal,
        blob,
        box,
        bus,
        targets,
        datasets,
        converters,
        prompt_assets,
        monitor,
        monitor_config,
        runs,
        manual,
        attack_methods,
        custom_scenarios,
    )


_STATE: AppState | None = None


def get_state() -> AppState:
    global _STATE
    if _STATE is None:
        _STATE = build_state()
    return _STATE


def require_admin(authorization: str = Header(default=""), state: AppState = Depends(get_state)) -> str:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        return verify_token(token, secret=state.settings.jwt_secret)
    except PermissionError:
        raise HTTPException(401, "invalid token") from None
