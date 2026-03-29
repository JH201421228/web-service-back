from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.Remember.core.deps import get_remember_db
from app.Remember.schemas.remember import (
    RememberAttemptCreateRequest,
    RememberAttemptResponse,
    RememberDeleteResponse,
    RememberTodayLeaderboardResponse,
)
from app.Remember.services.remember import (
    RememberRecordNotFoundError,
    create_attempt_record,
    delete_attempt_record,
    get_attempt_record,
    get_today_leaderboard,
    list_attempt_records,
)

LanguageCode = Literal["ko", "en"]
DisciplineCode = Literal["numbers", "cards"]
DifficultyCode = Literal["easy", "medium", "hard", "pro", "elite"]

router = APIRouter(tags=["Remember"])


@router.get(
    "/leaderboard/today",
    response_model=RememberTodayLeaderboardResponse,
    summary="Read today's public remember leaderboard",
)
def read_today_leaderboard(
    language: LanguageCode = Query(default="ko"),
    db: Session = Depends(get_remember_db),
) -> RememberTodayLeaderboardResponse:
    try:
        return get_today_leaderboard(db=db, language=language)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load today's remember leaderboard. {exc}",
        ) from exc


@router.post(
    "/records",
    response_model=RememberAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a remember attempt record",
)
def create_remember_record(
    payload: RememberAttemptCreateRequest,
    language: LanguageCode = Query(default="ko"),
    db: Session = Depends(get_remember_db),
) -> RememberAttemptResponse:
    try:
        return create_attempt_record(db=db, payload=payload, language=language)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create remember record. {exc}",
        ) from exc


@router.get(
    "/records",
    response_model=list[RememberAttemptResponse],
    summary="List remember attempt records",
)
def read_remember_records(
    device_id: str | None = Query(default=None, alias="deviceId"),
    discipline: DisciplineCode | None = Query(default=None),
    difficulty_id: DifficultyCode | None = Query(default=None, alias="difficultyId"),
    date_from: datetime | None = Query(default=None, alias="dateFrom"),
    date_to: datetime | None = Query(default=None, alias="dateTo"),
    limit: int = Query(default=100, ge=1, le=500),
    language: LanguageCode = Query(default="ko"),
    db: Session = Depends(get_remember_db),
) -> list[RememberAttemptResponse]:
    try:
        return list_attempt_records(
            db=db,
            language=language,
            device_id=device_id,
            discipline=discipline,
            difficulty_id=difficulty_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load remember records. {exc}",
        ) from exc


@router.get(
    "/records/{record_id}",
    response_model=RememberAttemptResponse,
    summary="Read a remember attempt record",
)
def read_remember_record(
    record_id: str,
    language: LanguageCode = Query(default="ko"),
    db: Session = Depends(get_remember_db),
) -> RememberAttemptResponse:
    try:
        return get_attempt_record(db=db, record_id=record_id, language=language)
    except RememberRecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load remember record. {exc}",
        ) from exc


@router.delete(
    "/records/{record_id}",
    response_model=RememberDeleteResponse,
    summary="Delete a remember attempt record",
)
def delete_remember_record(
    record_id: str,
    db: Session = Depends(get_remember_db),
) -> RememberDeleteResponse:
    try:
        return delete_attempt_record(db=db, record_id=record_id)
    except RememberRecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete remember record. {exc}",
        ) from exc
