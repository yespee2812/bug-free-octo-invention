"""FastAPI application for ScriptLens structure-only analysis."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import draft, health, scripts, simulate, upload
from api.sessions import SessionStore
from nlp_shared import get_shared_nlp

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def _cors_origins() -> list[str]:
    """Parse allowed CORS origins from the environment.

    Returns:
        List of allowed origins; ``*`` when unset (development default).
    """
    raw = os.environ.get("CORS_ORIGIN", "*").strip()
    if raw == "*":
        return ["*"]
    return [part.strip() for part in raw.split(",") if part.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Warm shared resources at startup and attach session store.

    Args:
        app: FastAPI application instance.

    Yields:
        Control to the request loop after startup work completes.
    """
    get_shared_nlp()
    ttl_hours = int(os.environ.get("SESSION_TTL_HOURS", "24"))
    app.state.session_store = SessionStore(ttl_hours=ttl_hours)
    yield


app = FastAPI(
    title="ScriptLens Structure API",
    version="3.0.0",
    description="Orphans, simulate cut, and simulate edit — structure-only analysis.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(scripts.router, prefix="/api")
app.include_router(simulate.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
