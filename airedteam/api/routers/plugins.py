from fastapi import APIRouter, Depends
from airedteam.core.registry import default_registry
from airedteam.api.deps import require_admin


router = APIRouter()


@router.get("/plugins")
async def plugins(_=Depends(require_admin)):
    r = default_registry()
    return {g: r.list(g) for g in ("targets", "datasets", "converters", "executors", "scorers")}
