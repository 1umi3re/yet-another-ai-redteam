from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from airedteam.api.deps import AppState, get_state, require_admin

router = APIRouter()


class MonitoringSettingsPatch(BaseModel):
    monitor_enabled: bool | None = None
    dingtalk_webhook_url: str | None = None
    dingtalk_secret: str | None = None
    clear_dingtalk_webhook_url: bool = False
    clear_dingtalk_secret: bool = False
    dingtalk_timeout_seconds: float | None = Field(default=None, gt=0, le=120)
    monitor_failure_rate_threshold: float | None = Field(default=None, ge=0, le=1)
    monitor_empty_response_rate_threshold: float | None = Field(default=None, ge=0, le=1)
    monitor_score_failure_rate_threshold: float | None = Field(default=None, ge=0, le=1)
    monitor_min_samples: int | None = Field(default=None, ge=1)
    monitor_no_progress_seconds: int | None = Field(default=None, ge=1)
    monitor_alert_cooldown_seconds: int | None = Field(default=None, ge=1)


@router.get("/settings/monitoring")
async def get_monitoring_settings(
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
) -> dict[str, Any]:
    return await state.monitor_config.get_public()


@router.patch("/settings/monitoring")
async def update_monitoring_settings(
    req: MonitoringSettingsPatch,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
) -> dict[str, Any]:
    return await state.monitor_config.update(req.model_dump(exclude_unset=True))


@router.post("/settings/monitoring/test")
async def test_monitoring_notification(
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
) -> dict[str, bool]:
    try:
        ok = await state.monitor.send_test_notification()
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not ok:
        raise HTTPException(502, "failed to send DingTalk test notification")
    return {"sent": True}
