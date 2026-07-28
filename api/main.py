"""FastAPI application for ScriptLens structure-only analysis."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import draft, health, scripts, simulate, upload
from api.sessions import SessionStore
from nlp_shared import get_shared_nlp

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


def _cors_config() -> tuple[list[str], bool]:
    """Parse allowed CORS origins and whether credentials may be sent.

    A wildcard origin cannot be combined with credentialed requests (the CORS
    spec forbids it and browsers reject the response), so credentials are only
    enabled when explicit origins are configured.

    Returns:
        Tuple of (allowed origins, allow-credentials flag).
    """
    raw = os.environ.get("CORS_ORIGIN", "*").strip()
    if raw == "*":
        return ["*"], False
    origins = [part.strip() for part in raw.split(",") if part.strip()]
    return origins, True


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
    max_concurrency = max(1, int(os.environ.get("ANALYSIS_MAX_CONCURRENCY", "2")))
    app.state.analysis_semaphore = asyncio.Semaphore(max_concurrency)
    app.state.analysis_timeout = float(os.environ.get("ANALYSIS_TIMEOUT_SECONDS", "60"))
    yield


app = FastAPI(
    title="ScriptLens Structure API",
    version="3.0.0",
    description="Orphans, simulate cut, and simulate edit — structure-only analysis.",
    lifespan=lifespan,
)

_cors_allow_origins, _cors_allow_credentials = _cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins,
    allow_credentials=_cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach baseline security headers to every response.

    Args:
        request: Incoming HTTP request.
        call_next: Downstream handler in the middleware chain.

    Returns:
        The response with hardening headers applied.
    """
    response = await call_next(request)
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    return response

app.include_router(health.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(scripts.router, prefix="/api")
app.include_router(simulate.router, prefix="/api")
app.include_router(draft.router, prefix="/api")

if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
