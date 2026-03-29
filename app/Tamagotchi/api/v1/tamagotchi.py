from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.Tamagotchi.core.deps import get_tamagotchi_db
from app.Tamagotchi.schemas.tamagotchi import (
    TamagotchiDailyLeaderboardResponse,
    TamagotchiLeaderboardSubmitRequest,
    TamagotchiPlayerSnapshotResponse,
    TamagotchiPlayerSyncRequest,
)
from app.Tamagotchi.services.tamagotchi import (
    get_daily_leaderboard,
    get_player_snapshot,
    submit_and_fetch_daily_leaderboard,
    upsert_player_snapshot,
)

router = APIRouter(tags=["Tamagotchi"])


@router.get(
    "/players/{install_id}",
    response_model=TamagotchiPlayerSnapshotResponse | None,
    summary="Read a tamagotchi player snapshot",
)
def read_player_snapshot(
    install_id: str,
    db: Session = Depends(get_tamagotchi_db),
) -> TamagotchiPlayerSnapshotResponse | None:
    try:
        return get_player_snapshot(db=db, install_id=install_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tamagotchi player snapshot. {exc}",
        ) from exc


@router.post(
    "/players/sync",
    response_model=TamagotchiPlayerSnapshotResponse,
    summary="Create or update a tamagotchi player snapshot",
)
def sync_player_snapshot(
    payload: TamagotchiPlayerSyncRequest,
    db: Session = Depends(get_tamagotchi_db),
) -> TamagotchiPlayerSnapshotResponse:
    try:
        return upsert_player_snapshot(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync tamagotchi player snapshot. {exc}",
        ) from exc


@router.get(
    "/leaderboard/daily",
    response_model=TamagotchiDailyLeaderboardResponse,
    summary="Read a daily tamagotchi leaderboard",
)
def read_daily_leaderboard(
    leaderboard_date: date = Query(alias="date"),
    install_id: str | None = Query(default=None, alias="installId"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_tamagotchi_db),
) -> TamagotchiDailyLeaderboardResponse:
    try:
        return get_daily_leaderboard(
            db=db,
            leaderboard_date=leaderboard_date,
            install_id=install_id,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tamagotchi leaderboard. {exc}",
        ) from exc


@router.post(
    "/leaderboard/submit-and-fetch",
    response_model=TamagotchiDailyLeaderboardResponse,
    summary="Submit today's score and fetch the tamagotchi leaderboard",
)
def submit_daily_leaderboard(
    payload: TamagotchiLeaderboardSubmitRequest,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_tamagotchi_db),
) -> TamagotchiDailyLeaderboardResponse:
    try:
        return submit_and_fetch_daily_leaderboard(
            db=db,
            payload=payload,
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
            detail=f"Failed to submit tamagotchi leaderboard. {exc}",
        ) from exc
