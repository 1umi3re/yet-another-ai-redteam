from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from airedteam.api.deps import get_state
from airedteam.storage import models
from airedteam.api.routers import login as login_router
from airedteam.api.routers import targets as targets_router
from airedteam.api.routers import datasets as datasets_router
from airedteam.api.routers import plugins as plugins_router
from airedteam.api.routers import scenarios as scenarios_router
from airedteam.api.routers import runs as runs_router
from airedteam.api.routers import manual as manual_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = get_state()
    from airedteam.storage.db import make_engine
    eng = make_engine(state.settings.database_url)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="airedteam API", lifespan=lifespan)
    state = get_state()
    app.add_middleware(CORSMiddleware,
                       allow_origins=state.settings.cors_origins,
                       allow_credentials=True,
                       allow_methods=["*"],
                       allow_headers=["*"])
    app.include_router(login_router.router, prefix="/api", tags=["auth"])
    app.include_router(targets_router.router, prefix="/api", tags=["targets"])
    app.include_router(datasets_router.router, prefix="/api", tags=["datasets"])
    app.include_router(plugins_router.router, prefix="/api", tags=["plugins"])
    app.include_router(scenarios_router.router, prefix="/api", tags=["scenarios"])
    app.include_router(runs_router.router, prefix="/api", tags=["runs"])
    app.include_router(manual_router.router, prefix="/api", tags=["manual"])
    return app
