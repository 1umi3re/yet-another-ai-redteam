from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from airedteam.api.deps import AppState, get_state, require_admin


router = APIRouter()


class OverrideIn(BaseModel):
    name: str
    template: str


class ActiveIn(BaseModel):
    override_id: str | None = None


@router.get("/prompt-assets")
async def list_prompt_assets(
    _=Depends(require_admin), state: AppState = Depends(get_state),
):
    return await state.prompt_assets.list_assets()


@router.get("/prompt-assets/{asset_id:path}")
async def get_prompt_asset(
    asset_id: str, _=Depends(require_admin), state: AppState = Depends(get_state),
):
    try:
        return await state.prompt_assets.get_asset(asset_id)
    except KeyError:
        raise HTTPException(404)


@router.post("/prompt-assets/{asset_id:path}/overrides", status_code=201)
async def create_prompt_asset_override(
    asset_id: str,
    body: OverrideIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.prompt_assets.create_override(
            asset_id, name=body.name, template=body.template,
        )
    except KeyError:
        raise HTTPException(404)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.patch("/prompt-assets/overrides/{override_id}")
async def update_prompt_asset_override(
    override_id: str,
    body: OverrideIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.prompt_assets.update_override(
            override_id, name=body.name, template=body.template,
        )
    except KeyError:
        raise HTTPException(404)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/prompt-assets/{asset_id:path}/active")
async def set_active_prompt_asset_override(
    asset_id: str,
    body: ActiveIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        await state.prompt_assets.set_active_override(asset_id, body.override_id)
        return await state.prompt_assets.get_asset(asset_id)
    except KeyError:
        raise HTTPException(404)
