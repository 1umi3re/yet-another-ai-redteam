from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from airedteam.api.deps import AppState, get_state, require_admin
from airedteam.core.attack_method_categories import converter_technical_categories
from airedteam.core.executor_methods import converter_method_names
from airedteam.core.prompt_framing_templates import attack_method_template_asset_id
from airedteam.core.registry import default_registry

router = APIRouter()


class CategoryIn(BaseModel):
    id: str
    name: str
    alias: str = ""
    type: str = ""
    description: str | None = None
    display_order: int = 1000


class CategoryPatch(BaseModel):
    name: str | None = None
    alias: str | None = None
    type: str | None = None
    description: str | None = None
    display_order: int | None = None


class MappingIn(BaseModel):
    category_id: str
    technical_category: str | None = None


class TemplateIn(BaseModel):
    name: str
    template: str
    active: bool = False


class TemplatePatch(BaseModel):
    name: str | None = None
    template: str | None = None


class ActiveTemplateIn(BaseModel):
    override_id: str | None = None


def current_attack_method_inputs() -> tuple[list[str], list[str], dict[str, str]]:
    registry = default_registry()
    native_executors = registry.list("executors")
    methods = converter_method_names()
    return native_executors, methods, converter_technical_categories()


async def ensure_current_attack_method_defaults(state: AppState) -> tuple[list[str], list[str], dict[str, str]]:
    native_executors, methods, technical_categories = current_attack_method_inputs()
    await state.attack_methods.ensure_defaults(
        native_executors=native_executors,
        converter_methods=methods,
        technical_categories=technical_categories,
    )
    return native_executors, methods, technical_categories


@router.get("/attack-method-categories")
async def list_attack_method_categories(
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    await ensure_current_attack_method_defaults(state)
    return await state.attack_methods.list_catalog()


@router.post("/attack-method-categories", status_code=201)
async def create_attack_method_category(
    body: CategoryIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.attack_methods.create_category(
            category_id=body.id,
            name=body.name,
            alias=body.alias,
            type=body.type,
            description=body.description,
            display_order=body.display_order,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


def _template_response(
    *,
    executor_kind: str,
    executor_name: str,
    default_asset_id: str | None,
    asset: dict | None,
    method_assets: list[dict] | None = None,
) -> dict:
    if asset is None or default_asset_id is None:
        return {
            "executor_kind": executor_kind,
            "executor_name": executor_name,
            "is_template_backed": False,
            "default_asset_id": None,
            "active_override": None,
            "templates": [],
        }
    active_override = asset.get("active_override")
    templates = []
    builtin_assets = _method_builtin_template_assets(
        method_assets=method_assets or [asset],
        executor_name=executor_name,
        default_asset_id=default_asset_id,
    )
    for builtin_asset in builtin_assets:
        is_default_asset = builtin_asset["id"] == default_asset_id
        template_asset = asset if is_default_asset else builtin_asset
        templates.append(
            {
                "id": "builtin" if is_default_asset else builtin_asset["id"],
                "asset_id": builtin_asset["id"],
                "name": _template_asset_name(builtin_asset, default_asset_id=default_asset_id),
                "template": template_asset["template"],
                "is_builtin": True,
                "is_active": is_default_asset and active_override is None,
                "created_at": None,
                "updated_at": None,
            }
        )
    for override in asset.get("overrides") or []:
        templates.append(
            {
                "id": override["id"],
                "asset_id": override["asset_id"],
                "name": override["name"],
                "template": override["template"],
                "is_builtin": False,
                "is_active": bool(override.get("is_active")),
                "created_at": override.get("created_at"),
                "updated_at": override.get("updated_at"),
            }
        )
    return {
        "executor_kind": executor_kind,
        "executor_name": executor_name,
        "is_template_backed": True,
        "default_asset_id": default_asset_id,
        "asset": asset,
        "active_override": active_override,
        "templates": templates,
    }


def _method_builtin_template_assets(
    *,
    method_assets: list[dict],
    executor_name: str,
    default_asset_id: str,
) -> list[dict]:
    seen: set[str] = set()
    builtin_assets: list[dict] = []
    for item in method_assets:
        asset_id = str(item.get("id") or "")
        if (
            item.get("purpose") != "attack_template"
            or item.get("plugin") != executor_name
            or item.get("is_custom")
            or asset_id in seen
        ):
            continue
        seen.add(asset_id)
        builtin_assets.append(item)
    builtin_assets.sort(key=lambda item: (item["id"] != default_asset_id, item["id"]))
    return builtin_assets


def _template_asset_name(asset: dict, *, default_asset_id: str) -> str:
    asset_id = str(asset["id"])
    if asset_id == default_asset_id:
        return "Built-in default"
    plugin = str(asset.get("plugin") or "")
    prefix = f"attack_method.{plugin}.template."
    label = asset_id
    if asset_id.startswith(prefix):
        label = asset_id.removeprefix(prefix)
    if label.endswith(".v1"):
        label = label.removesuffix(".v1")
    return " / ".join(part.replace("_", " ").replace("-", " ").title() for part in label.split("."))


async def _attack_method_template_detail(
    *,
    state: AppState,
    executor_kind: str,
    executor_name: str,
) -> dict:
    default_asset_id = (
        attack_method_template_asset_id(executor_name) if executor_kind == "converter_method" else None
    )
    if default_asset_id is None:
        return _template_response(
            executor_kind=executor_kind,
            executor_name=executor_name,
            default_asset_id=None,
            asset=None,
        )
    try:
        asset = await state.prompt_assets.get_asset(default_asset_id)
    except KeyError:
        raise HTTPException(404, f"missing attack method template asset: {default_asset_id}") from None
    method_assets = state.prompt_assets.list_builtin_assets()
    return _template_response(
        executor_kind=executor_kind,
        executor_name=executor_name,
        default_asset_id=default_asset_id,
        asset=asset,
        method_assets=method_assets,
    )


@router.get("/attack-methods/{executor_kind}/{executor_name}/templates")
async def list_attack_method_templates(
    executor_kind: str,
    executor_name: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    return await _attack_method_template_detail(
        state=state,
        executor_kind=executor_kind,
        executor_name=executor_name,
    )


@router.post("/attack-methods/{executor_kind}/{executor_name}/templates", status_code=201)
async def create_attack_method_template(
    executor_kind: str,
    executor_name: str,
    body: TemplateIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    detail = await _attack_method_template_detail(
        state=state,
        executor_kind=executor_kind,
        executor_name=executor_name,
    )
    if not detail["is_template_backed"]:
        raise HTTPException(400, "attack method does not support prompt templates")
    try:
        return await state.prompt_assets.create_override(
            detail["default_asset_id"],
            name=body.name,
            template=body.template,
            active=body.active,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.patch("/attack-methods/templates/{override_id}")
async def update_attack_method_template(
    override_id: str,
    body: TemplatePatch,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.prompt_assets.update_override(
            override_id,
            **body.model_dump(exclude_unset=True),
        )
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.delete("/attack-methods/templates/{override_id}", status_code=204)
async def delete_attack_method_template(
    override_id: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        await state.prompt_assets.delete_override(override_id)
    except KeyError:
        raise HTTPException(404) from None


@router.post("/attack-methods/{executor_kind}/{executor_name}/templates/active")
async def set_active_attack_method_template(
    executor_kind: str,
    executor_name: str,
    body: ActiveTemplateIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    detail = await _attack_method_template_detail(
        state=state,
        executor_kind=executor_kind,
        executor_name=executor_name,
    )
    if not detail["is_template_backed"]:
        raise HTTPException(400, "attack method does not support prompt templates")
    try:
        await state.prompt_assets.set_active_override(detail["default_asset_id"], body.override_id)
    except KeyError:
        raise HTTPException(404) from None
    return await _attack_method_template_detail(
        state=state,
        executor_kind=executor_kind,
        executor_name=executor_name,
    )


@router.patch("/attack-method-categories/{category_id}")
async def update_attack_method_category(
    category_id: str,
    body: CategoryPatch,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.attack_methods.update_category(
            category_id,
            **body.model_dump(exclude_unset=True),
        )
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.delete("/attack-method-categories/{category_id}", status_code=204)
async def delete_attack_method_category(
    category_id: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        await state.attack_methods.delete_category(category_id)
        return Response(status_code=204)
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.put("/attack-method-categories/mappings/{executor_kind}/{executor_name}")
async def upsert_attack_method_mapping(
    executor_kind: str,
    executor_name: str,
    body: MappingIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.attack_methods.upsert_mapping(
            executor_kind,
            executor_name,
            category_id=body.category_id,
            technical_category=body.technical_category,
        )
    except KeyError:
        raise HTTPException(404) from None
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
