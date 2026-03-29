from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.Tamagotchi.core.config import TAMAGOTCHI_TIMEZONE
from app.Tamagotchi.models.daily_history import TamagotchiDailyHistory
from app.Tamagotchi.models.leaderboard_entry import TamagotchiLeaderboardEntry
from app.Tamagotchi.models.player_profile import TamagotchiPlayerProfile
from app.Tamagotchi.schemas.tamagotchi import (
    TamagotchiDailyHealthSnapshot,
    TamagotchiDailyHistoryEntry,
    TamagotchiDailyLeaderboardResponse,
    TamagotchiLeaderboardEntryResponse,
    TamagotchiLeaderboardSubmitRequest,
    TamagotchiPlayerSnapshotResponse,
    TamagotchiPlayerSyncRequest,
)

LOCAL_TIMEZONE = ZoneInfo(TAMAGOTCHI_TIMEZONE)
MAX_SYNC_HISTORY = 90
MAX_RETURN_HISTORY = 30


def get_player_snapshot(
    db: Session,
    install_id: str,
) -> TamagotchiPlayerSnapshotResponse | None:
    player = (
        db.query(TamagotchiPlayerProfile)
        .filter(TamagotchiPlayerProfile.install_id == install_id)
        .first()
    )
    if player is None:
        return None

    history_rows = (
        db.query(TamagotchiDailyHistory)
        .filter(TamagotchiDailyHistory.player_id == player.id)
        .order_by(TamagotchiDailyHistory.date_key.desc())
        .limit(MAX_RETURN_HISTORY)
        .all()
    )
    return _to_player_snapshot(player=player, history_rows=history_rows)


def upsert_player_snapshot(
    db: Session,
    payload: TamagotchiPlayerSyncRequest,
) -> TamagotchiPlayerSnapshotResponse:
    player = (
        db.query(TamagotchiPlayerProfile)
        .filter(TamagotchiPlayerProfile.install_id == payload.installId)
        .first()
    )

    if player is None:
        player = TamagotchiPlayerProfile(install_id=payload.installId)

    player.language = payload.language
    player.nickname = payload.nickname
    player.pet_name = payload.petName
    player.starter_id = payload.selectedStarter
    player.exp = payload.exp
    player.coins = payload.coins
    player.mood = payload.mood
    player.energy = payload.energy
    player.cleanliness = payload.cleanliness
    player.bond = payload.bond
    player.streak = payload.streak
    player.last_sync_date = payload.lastSyncDate
    player.last_health_source = payload.lastHealthSource

    db.add(player)
    db.flush()

    incoming_history = payload.dailyHistory[:MAX_SYNC_HISTORY]
    existing_history: dict[date, TamagotchiDailyHistory] = {}

    if incoming_history:
        date_keys = [entry.date for entry in incoming_history]
        existing_history = {
            row.date_key: row
            for row in db.query(TamagotchiDailyHistory)
            .filter(TamagotchiDailyHistory.player_id == player.id)
            .filter(TamagotchiDailyHistory.date_key.in_(date_keys))
            .all()
        }

    for entry in incoming_history:
        history_row = existing_history.get(entry.date)
        if history_row is None:
            history_row = TamagotchiDailyHistory(
                player_id=player.id,
                date_key=entry.date,
            )

        _apply_history_row(history_row=history_row, entry=entry)
        db.add(history_row)

    db.commit()

    return get_player_snapshot(db=db, install_id=payload.installId)  # type: ignore[return-value]


def get_daily_leaderboard(
    db: Session,
    leaderboard_date: date,
    install_id: str | None = None,
    limit: int = 20,
) -> TamagotchiDailyLeaderboardResponse:
    rows = (
        db.query(TamagotchiLeaderboardEntry)
        .filter(TamagotchiLeaderboardEntry.date_key == leaderboard_date)
        .order_by(
            TamagotchiLeaderboardEntry.score.desc(),
            TamagotchiLeaderboardEntry.streak.desc(),
            TamagotchiLeaderboardEntry.stage.desc(),
            TamagotchiLeaderboardEntry.total_exp.desc(),
            TamagotchiLeaderboardEntry.submitted_at.asc(),
            TamagotchiLeaderboardEntry.id.asc(),
        )
        .all()
    )

    ranked_entries = [
        _to_leaderboard_entry(row=row, rank=index + 1, install_id=install_id)
        for index, row in enumerate(rows)
    ]
    self_entry = next(
        (entry for entry in ranked_entries if install_id and entry.installId == install_id),
        None,
    )

    return TamagotchiDailyLeaderboardResponse(
        date=leaderboard_date,
        updatedAt=_local_now_naive(),
        top=ranked_entries[:limit],
        self=self_entry,
    )


def submit_and_fetch_daily_leaderboard(
    db: Session,
    payload: TamagotchiLeaderboardSubmitRequest,
    limit: int = 20,
) -> TamagotchiDailyLeaderboardResponse:
    entry = (
        db.query(TamagotchiLeaderboardEntry)
        .filter(TamagotchiLeaderboardEntry.date_key == payload.date)
        .filter(TamagotchiLeaderboardEntry.install_id == payload.installId)
        .first()
    )

    if entry is None:
        entry = TamagotchiLeaderboardEntry(
            date_key=payload.date,
            install_id=payload.installId,
        )

    entry.nickname = payload.nickname
    entry.pet_name = payload.petName
    entry.starter_id = payload.starter

    if _should_replace_leaderboard_entry(entry=entry, payload=payload):
        entry.score = payload.score
        entry.streak = payload.streak
        entry.stage = payload.stage
        entry.total_exp = payload.totalExp
        entry.submitted_at = _local_now_naive()

    db.add(entry)
    db.commit()

    return get_daily_leaderboard(
        db=db,
        leaderboard_date=payload.date,
        install_id=payload.installId,
        limit=limit,
    )


def _apply_history_row(
    history_row: TamagotchiDailyHistory,
    entry: TamagotchiDailyHistoryEntry,
) -> None:
    history_row.date_key = entry.date
    history_row.steps = entry.health.steps
    history_row.sleep_hours = entry.health.sleepHours
    history_row.avg_heart_rate = entry.health.avgHeartRate
    history_row.calories = entry.health.calories
    history_row.active_minutes = entry.health.activeMinutes
    history_row.health_source = entry.health.source
    history_row.score = entry.score
    history_row.exp_gained = entry.expGained
    history_row.coins_gained = entry.coinsGained
    history_row.total_exp = entry.totalExp
    history_row.stage = entry.stage


def _to_player_snapshot(
    player: TamagotchiPlayerProfile,
    history_rows: list[TamagotchiDailyHistory],
) -> TamagotchiPlayerSnapshotResponse:
    history_entries = [_to_history_entry(row=row) for row in history_rows]

    return TamagotchiPlayerSnapshotResponse(
        installId=player.install_id,
        language=player.language,
        nickname=player.nickname,
        petName=player.pet_name,
        selectedStarter=player.starter_id,
        exp=player.exp,
        coins=player.coins,
        mood=player.mood,
        energy=player.energy,
        cleanliness=player.cleanliness,
        bond=player.bond,
        streak=player.streak,
        lastSyncDate=player.last_sync_date,
        lastHealthSource=player.last_health_source,
        dailyHistory=history_entries,
        updatedAt=_with_timezone(player.updated_at),
    )


def _to_history_entry(row: TamagotchiDailyHistory) -> TamagotchiDailyHistoryEntry:
    return TamagotchiDailyHistoryEntry(
        date=row.date_key,
        health=TamagotchiDailyHealthSnapshot(
            date=row.date_key,
            steps=row.steps,
            sleepHours=row.sleep_hours,
            avgHeartRate=row.avg_heart_rate,
            calories=row.calories,
            activeMinutes=row.active_minutes,
            source=row.health_source,
        ),
        score=row.score,
        expGained=row.exp_gained,
        coinsGained=row.coins_gained,
        totalExp=row.total_exp,
        stage=row.stage,
    )


def _to_leaderboard_entry(
    row: TamagotchiLeaderboardEntry,
    rank: int,
    install_id: str | None = None,
) -> TamagotchiLeaderboardEntryResponse:
    return TamagotchiLeaderboardEntryResponse(
        installId=row.install_id,
        nickname=row.nickname,
        petName=row.pet_name,
        starter=row.starter_id,
        score=row.score,
        streak=row.streak,
        stage=row.stage,
        totalExp=row.total_exp,
        rank=rank,
        isSelf=install_id == row.install_id if install_id else False,
    )


def _should_replace_leaderboard_entry(
    entry: TamagotchiLeaderboardEntry,
    payload: TamagotchiLeaderboardSubmitRequest,
) -> bool:
    if entry.id is None:
        return True
    if payload.score > entry.score:
        return True
    if payload.score < entry.score:
        return False
    if payload.stage > entry.stage:
        return True
    if payload.stage < entry.stage:
        return False
    if payload.totalExp > entry.total_exp:
        return True
    if payload.totalExp < entry.total_exp:
        return False
    return payload.streak > entry.streak


def _local_now_naive() -> datetime:
    return datetime.now(LOCAL_TIMEZONE).replace(tzinfo=None)


def _with_timezone(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(LOCAL_TIMEZONE)

    if value.tzinfo is None:
        return value.replace(tzinfo=LOCAL_TIMEZONE)

    return value.astimezone(LOCAL_TIMEZONE)
