from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from airedteam.api.deps import AppState, get_state, require_admin


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


def _to_out(row) -> TargetOut:
    return TargetOut(id=row.id, name=row.name, plugin=row.plugin, params=row.params_json or {}, has_secret=row.secret_ciphertext is not None)


@router.post("/targets", status_code=201, response_model=TargetOut)
async def create(req: CreateTarget, _=Depends(require_admin), state: AppState = Depends(get_state)):
    row = await state.targets.create(name=req.name, plugin=req.plugin, params=req.params, secret=req.secret)
    return _to_out(row)


@router.get("/targets", response_model=list[TargetOut])
async def list_targets(_=Depends(require_admin), state: AppState = Depends(get_state)):
    return [_to_out(r) for r in await state.targets.list()]


@router.delete("/targets/{tid}", status_code=204)
async def delete(tid: str, _=Depends(require_admin), state: AppState = Depends(get_state)):
    if await state.targets.get(tid) is None:
        raise HTTPException(404)
    await state.targets.delete(tid)
