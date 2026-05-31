from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

from airedteam.config import Settings, get_settings
from airedteam.engine.progress import ProgressBus
from airedteam.services.converters import ConverterChainService
from airedteam.services.datasets import DatasetService
from airedteam.services.manual import ManualService
from airedteam.services.prompt_assets import PromptAssetService
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
    runs: RunService
    manual: ManualService


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
    )
    manual = ManualService(SessionLocal, blob, targets, converters, prompt_assets)
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
        runs,
        manual,
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
