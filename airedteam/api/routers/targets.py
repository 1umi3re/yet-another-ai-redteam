import asyncio
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from airedteam.api.deps import AppState, get_state, require_admin
from airedteam.core.types import Prompt
from airedteam.engine.factory import build_target

router = APIRouter()


class CreateTarget(BaseModel):
    name: str
    plugin: str
    params: dict[str, Any] = Field(default_factory=dict)
    secret: dict[str, Any] | None = None


class TargetOut(BaseModel):
    id: str
    name: str
    plugin: str
    params: dict[str, Any]
    has_secret: bool


class UpdateTargetLimits(BaseModel):
    timeout: float | None = Field(default=None, gt=0)
    max_concurrency: int | None = Field(default=None, gt=0)
    max_input_chars: int | None = Field(default=None, gt=0)
    input_limit_unit: str | None = Field(default=None, pattern="^characters$")


class CheckResult(BaseModel):
    ok: bool
    latency_ms: int | None = None
    response_preview: str | None = None
    stream_ok: bool | None = None
    stream_error: str | None = None
    error: str | None = None
    model_echo: str | None = None


def _to_out(row) -> TargetOut:
    return TargetOut(
        id=row.id,
        name=row.name,
        plugin=row.plugin,
        params=row.params_json or {},
        has_secret=row.secret_ciphertext is not None,
    )


def _probe_timeout(runtime_cfg: dict) -> float:
    raw = (runtime_cfg.get("params") or {}).get("timeout")
    if raw is None or raw == "":
        return 180.0
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 180.0
    return value if value > 0 else 180.0


@router.post("/targets", status_code=201, response_model=TargetOut)
async def create(req: CreateTarget, _=Depends(require_admin), state: AppState = Depends(get_state)):
    row = await state.targets.create(name=req.name, plugin=req.plugin, params=req.params, secret=req.secret)
    return _to_out(row)


@router.get("/targets", response_model=list[TargetOut])
async def list_targets(_=Depends(require_admin), state: AppState = Depends(get_state)):
    return [_to_out(r) for r in await state.targets.list()]


@router.patch("/targets/{tid}/limits", response_model=TargetOut)
async def update_limits(
    tid: str,
    req: UpdateTargetLimits,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        row = await state.targets.update_limits(
            tid,
            timeout_set="timeout" in req.model_fields_set,
            timeout=req.timeout,
            max_concurrency_set="max_concurrency" in req.model_fields_set,
            max_concurrency=req.max_concurrency,
            max_input_chars_set="max_input_chars" in req.model_fields_set,
            max_input_chars=req.max_input_chars,
            input_limit_unit_set="input_limit_unit" in req.model_fields_set,
            input_limit_unit=req.input_limit_unit,
        )
    except KeyError:
        raise HTTPException(404, "Target not found") from None
    return _to_out(row)


@router.delete("/targets/{tid}", status_code=204)
async def delete(tid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    if await state.targets.get(tid) is None:
        raise HTTPException(404)
    await state.targets.delete(tid)


async def _check_target_connectivity(runtime_cfg: dict) -> CheckResult:
    """Probe a target by sending a ping prompt and measuring response time."""
    target = None
    timeout = _probe_timeout(runtime_cfg)
    try:
        target = build_target(runtime_cfg)
        start = time.perf_counter()

        ping_prompt = Prompt(text="Reply with the single word: pong")
        response = await asyncio.wait_for(target.generate(ping_prompt), timeout=timeout)
        stream_ok = None
        stream_error = None
        if hasattr(target, "check_stream_support"):
            stream_ok, stream_error = await asyncio.wait_for(
                target.check_stream_support(Prompt(text="Reply with the single word: pong")),
                timeout=timeout,
            )

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        preview = response.text[:200] if response.text else None
        model_echo = runtime_cfg.get("params", {}).get("model")

        return CheckResult(
            ok=True,
            latency_ms=elapsed_ms,
            response_preview=preview,
            stream_ok=stream_ok,
            stream_error=stream_error,
            model_echo=model_echo,
        )
    except TimeoutError:
        return CheckResult(ok=False, error=f"TimeoutError: Request exceeded {timeout:g} seconds")
    except Exception as e:
        return CheckResult(ok=False, error=f"{type(e).__name__}: {str(e)}")
    finally:
        if target is not None:
            await target.aclose()


@router.post("/targets/{tid}/check", response_model=CheckResult)
async def check_target(tid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    """Check connectivity and responsiveness of a configured target."""
    if await state.targets.get(tid) is None:
        raise HTTPException(404, "Target not found")

    runtime_cfg = await state.targets.resolve_for_runtime(tid)
    return await _check_target_connectivity(runtime_cfg)


@router.post("/targets/check", response_model=CheckResult)
async def check_target_draft(req: CreateTarget, _=Depends(require_admin), state: AppState = Depends(get_state)):
    """Check connectivity of a target config without saving it."""
    # Build a runtime config from the request (without persisting)
    runtime_cfg = {"plugin": req.plugin, "params": req.params}

    # If there's a secret, we need to temporarily decrypt it for the check
    # But since we're not persisting, we can pass it directly to the target
    if req.secret:
        # For targets that use secrets, we need to inject them into params
        # This depends on how the target plugin expects secrets
        # Most targets like openai_compat expect api_key in the params
        if req.plugin in ("openai_compat", "anthropic_compat"):
            runtime_cfg["params"] = {**req.params, **req.secret}

    return await _check_target_connectivity(runtime_cfg)
