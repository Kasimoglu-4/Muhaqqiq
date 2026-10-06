"""FastAPI entry: create_app() + uvicorn (muhaqqiq.main:app)."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from muhaqqiq import __version__
from muhaqqiq.api.middleware import RateLimitMiddleware, RequestIdMiddleware
from muhaqqiq.api.routers import cards, health, meta, verify
from muhaqqiq.observability import init_sentry
from muhaqqiq.repositories.embeddings import DEFAULT_EMBEDDINGS
from muhaqqiq.repositories.sqlite_repo import init_db

logger = logging.getLogger("muhaqqiq")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _load_dotenv() -> None:
    """Load repo-root .env into os.environ (does not override existing vars)."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

_LOCAL_CORS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
)


def _cors_origins() -> list[str]:
    """Localhost defaults + MUHAQQIQ_CORS_ORIGINS (comma-separated production URLs)."""
    origins = list(_LOCAL_CORS)
    raw = os.environ.get("MUHAQQIQ_CORS_ORIGINS", "").strip()
    for part in raw.split(","):
        origin = part.strip().rstrip("/")
        if origin and origin not in origins:
            origins.append(origin)
    return origins


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_sentry()
    init_db().close()
    if DEFAULT_EMBEDDINGS.enabled():
        DEFAULT_EMBEDDINGS.load()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Muhaqqiq",
        version=__version__,
        description=(
            "Verification API for viral Islamic text. "
            "References always come from stored data — never from a language model."
        ),
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RateLimitMiddleware, limit=60, window_sec=60)
    application.add_middleware(RequestIdMiddleware)

    application.include_router(health.router)
    application.include_router(verify.router)
    application.include_router(cards.router)
    application.include_router(meta.router)
    return application


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("muhaqqiq.main:app", host="0.0.0.0", port=8000, reload=False)
