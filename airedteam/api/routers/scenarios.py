from fastapi import APIRouter, Depends

from airedteam.api.deps import require_admin
from airedteam.core.registry import default_registry

router = APIRouter()


@router.get("/scenarios")
async def list_scenarios(_=Depends(require_admin)):
    r = default_registry()
    out = []
    for name in r.list("scenarios"):
        sc = r.get("scenarios", name)
        out.append({"id": sc.id, "title": sc.title, "description": sc.description, "tags": sc.tags})
    return out
