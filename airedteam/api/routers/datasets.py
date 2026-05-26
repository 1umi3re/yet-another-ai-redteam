from typing import Any

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel
from airedteam.api.deps import AppState, get_state, require_admin


router = APIRouter()


class DatasetOut(BaseModel):
    id: str
    name: str
    plugin: str
    item_count: int | None
    current_version: int = 1


def _to_out(row) -> DatasetOut:
    return DatasetOut(
        id=row.id,
        name=row.name,
        plugin=row.plugin,
        item_count=row.item_count,
        current_version=getattr(row, "current_version", None) or 1,
    )


@router.post("/datasets/upload", status_code=201, response_model=DatasetOut)
async def upload(name: str = Form(...), file: UploadFile = File(...), _=Depends(require_admin), state: AppState = Depends(get_state)):
    body = await file.read()
    try:
        row = await state.datasets.create_json_upload(name=name, file_bytes=body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _to_out(row)


class CreateHF(BaseModel):
    name: str
    repo: str
    split: str = "train"
    prompt_field: str = "prompt"
    limit: int | None = 100


class DatasetContentIn(BaseModel):
    items: list[Any]
    note: str | None = None


@router.post("/datasets/hf", status_code=201, response_model=DatasetOut)
async def create_hf(req: CreateHF, _=Depends(require_admin), state: AppState = Depends(get_state)):
    row = await state.datasets.create_hf(name=req.name, repo=req.repo, split=req.split, prompt_field=req.prompt_field, limit=req.limit)
    return _to_out(row)


@router.get("/datasets", response_model=list[DatasetOut])
async def list_datasets(_=Depends(require_admin), state: AppState = Depends(get_state)):
    return [_to_out(r) for r in await state.datasets.list()]


@router.get("/datasets/{dataset_id}/content")
async def get_dataset_content(
    dataset_id: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.datasets.content(dataset_id)
    except KeyError:
        raise HTTPException(404)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/datasets/{dataset_id}/content", response_model=DatasetOut)
async def update_dataset_content(
    dataset_id: str,
    body: DatasetContentIn,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        row = await state.datasets.update_items(dataset_id, items=body.items, note=body.note)
        return _to_out(row)
    except KeyError:
        raise HTTPException(404)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/datasets/{dataset_id}/versions")
async def list_dataset_versions(
    dataset_id: str,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.datasets.list_versions(dataset_id)
    except KeyError:
        raise HTTPException(404)


@router.post("/datasets/{dataset_id}/versions/{version}/restore", response_model=DatasetOut)
async def restore_dataset_version(
    dataset_id: str,
    version: int,
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        row = await state.datasets.restore_version(dataset_id, version)
        return _to_out(row)
    except KeyError:
        raise HTTPException(404)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/datasets/{dataset_id}/items")
async def list_dataset_items(
    dataset_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    _=Depends(require_admin),
    state: AppState = Depends(get_state),
):
    try:
        return await state.datasets.list_items(dataset_id, limit=limit, offset=offset, q=q)
    except KeyError:
        raise HTTPException(404)
    except Exception as e:
        raise HTTPException(400, str(e))
