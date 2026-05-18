from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from airedteam.api.deps import AppState, get_state, require_admin


router = APIRouter()


class ConverterRefIn(BaseModel):
    plugin: str
    params: dict[str, Any] = Field(default_factory=dict)


class PreviewIn(BaseModel):
    text: str
    converters: list[ConverterRefIn] = Field(default_factory=list)


@router.post("/converters/preview")
async def preview_converters(body: PreviewIn, _=Depends(require_admin),
                             state: AppState = Depends(get_state)):
    try:
        result = await state.converters.apply(
            body.text,
            [c.model_dump() for c in body.converters],
        )
    except Exception as e:
        raise HTTPException(400, detail=str(e))
    return {
        "original_text": result.original_text,
        "transformed_text": result.transformed_text,
        "converter_chain": result.converter_chain,
        "converters": result.converters,
    }
