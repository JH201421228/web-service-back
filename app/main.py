import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.NewsBase.core.logging import get_logger, setup_logging
from app.NewsBase.core.scheduler import (
    start_scheduler as start_news_scheduler,
    stop_scheduler as stop_news_scheduler,
)
from app.Tourist.core.scheduler import (
    start_scheduler as start_tourist_scheduler,
    stop_scheduler as stop_tourist_scheduler,
)

setup_logging(
    log_level="INFO",
    log_to_console=True,
    log_to_file=True,
)

logger = get_logger(__name__)

import app.NewsBase.core.firebase  # noqa: F401, E402


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("Combinator API server starting")
    start_news_scheduler()
    start_tourist_scheduler()
    yield
    stop_tourist_scheduler()
    stop_news_scheduler()
    logger.info("Combinator API server stopped")


app = FastAPI(
    title="Combinator API",
    description="NewsBase, Tourist, WhatYourName APIs",
    version="0.1.0",
    lifespan=lifespan,
)

DEFAULT_WEB_CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://newsbase-da15f.web.app",
    "https://newsbase.store",
    "https://whatsyourname.shop",
]

DEFAULT_TOURIST_CORS_ALLOWED_ORIGINS: list[str] = []
CORS_ALLOW_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"


def _parse_cors_allowed_origins(env_name: str, default_origins: list[str]) -> list[str]:
    raw_origins = os.getenv(env_name)
    if not raw_origins:
        return default_origins.copy()

    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def _allowed_origins_for_path(path: str) -> list[str]:
    if path.startswith("/api/v1/tourist"):
        return tourist_cors_allowed_origins

    if path.startswith("/api/v1/whatyourname"):
        return web_cors_allowed_origins

    if path.startswith("/api"):
        return web_cors_allowed_origins

    return []


def _apply_cors_headers(
    response: Response,
    origin: str,
    request_headers: str | None = None,
) -> None:
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = CORS_ALLOW_METHODS
    response.headers["Access-Control-Allow-Headers"] = request_headers or "*"
    response.headers["Access-Control-Max-Age"] = "600"
    response.headers["Vary"] = "Origin"


web_cors_allowed_origins = _parse_cors_allowed_origins(
    "CORS_ALLOWED_ORIGINS",
    DEFAULT_WEB_CORS_ALLOWED_ORIGINS,
)
tourist_cors_allowed_origins = _parse_cors_allowed_origins(
    "TOURIST_CORS_ALLOWED_ORIGINS",
    DEFAULT_TOURIST_CORS_ALLOWED_ORIGINS,
)
logger.info("Configured web CORS origins: %s", web_cors_allowed_origins)
logger.info(
    "Configured tourist CORS origins: %s",
    tourist_cors_allowed_origins if tourist_cors_allowed_origins else "none",
)

from app.NewsBase.api.v1 import api_router as news_router  # noqa: E402
from app.NewsBase.core.deps import get_db  # noqa: E402
from app.Tourist.api.v1 import api_router as tourist_router  # noqa: E402
from app.Tourist.core.deps import get_tourist_db  # noqa: E402
from app.WhatYourName.api.v1 import api_router as what_router  # noqa: E402

app.include_router(news_router)
app.include_router(tourist_router)
app.include_router(what_router, prefix="/api/v1/whatyourname")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin")
    allowed_origins = _allowed_origins_for_path(request.url.path)
    requested_headers = request.headers.get("access-control-request-headers")
    requested_method = request.headers.get("access-control-request-method")

    if request.method == "OPTIONS" and origin and requested_method:
        if origin not in allowed_origins:
            return Response(status_code=403)

        response = Response(status_code=204)
        _apply_cors_headers(response, origin, requested_headers)
        return response

    logging.getLogger(__name__).info("Request: %s %s", request.method, request.url.path)
    response = await call_next(request)

    if origin and origin in allowed_origins:
        _apply_cors_headers(response, origin, requested_headers)

    logging.getLogger(__name__).info(
        "Response: %s %s - Status: %s",
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}


@app.get("/health/db/tourist")
def health_tourist_db(db: Session = Depends(get_tourist_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "tourist"}
