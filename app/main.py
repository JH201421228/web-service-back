import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.NewsBase.core.logging import setup_logging, get_logger
from app.NewsBase.core.scheduler import start_scheduler, stop_scheduler

# 로깅 설정
setup_logging(
    log_level="INFO",
    log_to_console=True,
    log_to_file=True,
)

logger = get_logger(__name__)

# Firebase Admin SDK 초기화 (import 시 자동 실행)
import app.NewsBase.core.firebase  # noqa: F401, E402


# ---------------------------------------------------------------------------
# Lifespan: 서버 시작/종료 시 스케줄러 제어
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    """서버 시작 → 스케줄러 ON / 서버 종료 → 스케줄러 OFF"""
    logger.info("Combinator API 서버 시작")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Combinator API 서버 종료")


# ---------------------------------------------------------------------------
# FastAPI 앱
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Combinator API",
    description="여러 서비스의 api를 통합하여 사용",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
from app.NewsBase.api.v1 import api_router  # noqa: E402
from app.NewsBase.core.deps import get_db    # noqa: E402

app.include_router(api_router)


# ---------------------------------------------------------------------------
# 미들웨어
# ---------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {request.method} {request.url.path} - Status: {response.status_code}")
    return response


# ---------------------------------------------------------------------------
# 헬스체크
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}