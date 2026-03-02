import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.core.deps import get_db, get_current_user

# 모든 모델 import (테이블 생성을 위해)
from app.models import User, Habit  # noqa: F401


# 테스트용 인메모리 SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 테스트용 사용자 정보
TEST_USER = {
    "uid": "test-user-uid",
    "email": "test@example.com",
    "name": "Test User",
    "picture": None,
}


def override_get_db():
    """테스트용 DB 세션"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    """테스트용 가짜 사용자 (Firebase 인증 모킹)"""
    return TEST_USER


@pytest.fixture(scope="function")
def client():
    """테스트 클라이언트 생성"""
    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    # 의존성 오버라이드
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    # 테이블 삭제 (각 테스트 후 클린업)
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """테스트용 DB 세션 (서비스 레이어 직접 테스트용)"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers():
    """인증 헤더"""
    return {"Authorization": "Bearer fake-token"}

