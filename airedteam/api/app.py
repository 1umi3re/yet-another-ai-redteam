from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from airedteam.api.deps import get_state
from airedteam.api.routers import attack_methods as attack_methods_router
from airedteam.api.routers import converters as converters_router
from airedteam.api.routers import datasets as datasets_router
from airedteam.api.routers import login as login_router
from airedteam.api.routers import manual as manual_router
from airedteam.api.routers import plugins as plugins_router
from airedteam.api.routers import prompt_assets as prompt_assets_router
from airedteam.api.routers import runs as runs_router
from airedteam.api.routers import scenarios as scenarios_router
from airedteam.api.routers import settings as settings_router
from airedteam.api.routers import targets as targets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = get_state()
    from airedteam.storage.db import initialize_database, make_engine

    eng = make_engine(state.settings.database_url)
    await initialize_database(eng)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="airedteam API", lifespan=lifespan)
    state = get_state()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=state.settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(login_router.router, prefix="/api", tags=["auth"])
    app.include_router(targets_router.router, prefix="/api", tags=["targets"])
    app.include_router(datasets_router.router, prefix="/api", tags=["datasets"])
    app.include_router(plugins_router.router, prefix="/api", tags=["plugins"])
    app.include_router(attack_methods_router.router, prefix="/api", tags=["attack-methods"])
    app.include_router(scenarios_router.router, prefix="/api", tags=["scenarios"])
    app.include_router(runs_router.router, prefix="/api", tags=["runs"])
    app.include_router(settings_router.router, prefix="/api", tags=["settings"])
    app.include_router(manual_router.router, prefix="/api", tags=["manual"])
    app.include_router(prompt_assets_router.router, prefix="/api", tags=["prompt-assets"])
    app.include_router(converters_router.router, prefix="/api", tags=["converters"])
    return app
