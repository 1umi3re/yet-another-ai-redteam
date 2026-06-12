from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from airedteam.api.deps import AppState, get_state, require_admin

router = APIRouter()


class OverrideIn(BaseModel):
    name: str
    template: str


class AssetIn(BaseModel):
    id: str
    plugin: str = "custom"
    purpose: str = "custom"
    category: str | None = None
    variables: list[str] = []
    template: str
    version: int = 1


class ActiveIn(BaseModel):
    override_id: str | None = None


@router.get("/prompt-assets")
async def list_prompt_assets(
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    return await state.prompt_assets.list_assets()


@router.post("/prompt-assets", status_code=201)
async def create_prompt_asset(
    body: AssetIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.prompt_assets.create_asset(
            asset_id=body.id,
            plugin=body.plugin,
            purpose=body.purpose,
            category=body.category,
            variables=body.variables,
            template=body.template,
            version=body.version,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/prompt-assets/{asset_id:path}")
async def get_prompt_asset(
    asset_id: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.prompt_assets.get_asset(asset_id)
    except KeyError:
        raise HTTPException(404) from None


@router.post("/prompt-assets/{asset_id:path}/overrides", status_code=201)
async def create_prompt_asset_override(
    asset_id: str,
    body: OverrideIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.prompt_assets.create_override(
            asset_id,
            name=body.name,
            template=body.template,
        )
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.patch("/prompt-assets/overrides/{override_id}")
async def update_prompt_asset_override(
    override_id: str,
    body: OverrideIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.prompt_assets.update_override(
            override_id,
            name=body.name,
            template=body.template,
        )
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


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
        raise HTTPException(404) from None


@router.delete("/prompt-assets/overrides/{override_id}", status_code=204)
async def delete_prompt_asset_override(
    override_id: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        await state.prompt_assets.delete_override(override_id)
    except KeyError:
        raise HTTPException(404) from None


@router.delete("/prompt-assets/{asset_id:path}", status_code=204)
async def delete_prompt_asset(
    asset_id: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        await state.prompt_assets.delete_asset(asset_id)
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
