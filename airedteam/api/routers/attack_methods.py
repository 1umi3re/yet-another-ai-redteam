from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from airedteam.api.deps import AppState, get_state, require_admin
from airedteam.core.attack_method_categories import converter_technical_categories
from airedteam.core.executor_methods import converter_method_names
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
