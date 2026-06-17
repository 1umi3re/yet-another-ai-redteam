from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from airedteam.api.deps import AppState, get_state, require_admin
from airedteam.core.registry import default_registry
from airedteam.services.custom_scenarios import internal_custom_scenario_id

router = APIRouter()


class RenderScenarioRunSpec(BaseModel):
    target_config_id: str
    dataset_config_id: str
    helper_config_ids: dict[str, str] = {}


class CustomScenarioIn(BaseModel):
    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    template: dict[str, Any]


def _requirement_out(req) -> dict[str, Any]:
    if is_dataclass(req):
        return asdict(req)
    if isinstance(req, dict):
        return dict(req)
    return {"id": str(req), "label": str(req), "type": "target_ref", "help": ""}


def _scenario_out(sc) -> dict[str, Any]:
    return {
        "id": sc.id,
        "title": sc.title,
        "description": sc.description,
        "tags": sc.tags,
        "level": getattr(sc, "level", "basic"),
        "requirements": [_requirement_out(req) for req in getattr(sc, "requirements", [])],
    }


@router.get("/scenarios")
async def list_scenarios(
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    r = default_registry()
    out = []
    for name in r.list("scenarios"):
        sc = r.get("scenarios", name)
        out.append(_scenario_out(sc))
    out.extend(await state.custom_scenarios.list())
    return out


@router.post("/scenarios/custom", status_code=201)
async def create_custom_scenario(
    body: CustomScenarioIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.custom_scenarios.create(
            name=body.name,
            description=body.description,
            tags=body.tags,
            template=body.template,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/scenarios/{scenario_id}/runspec")
async def render_scenario_runspec(
    scenario_id: str,
    req: RenderScenarioRunSpec,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    if internal_custom_scenario_id(scenario_id) is not None:
        try:
            return await state.custom_scenarios.render_runspec(
                public_id=scenario_id,
                target_config_id=req.target_config_id,
                dataset_config_id=req.dataset_config_id,
            )
        except KeyError:
            raise HTTPException(404) from None

    r = default_registry()
    try:
        sc = r.get("scenarios", scenario_id)
    except KeyError:
        raise HTTPException(404) from None
    try:
        return sc.runspec_template(
            target_config_id=req.target_config_id,
            dataset_config_id=req.dataset_config_id,
            **req.helper_config_ids,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
