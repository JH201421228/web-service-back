from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.Remember.core.config import REMEMBER_DEFAULT_NICKNAME, REMEMBER_TIMEZONE
from app.Remember.models.attempt_record import RememberAttemptRecord
from app.Remember.schemas.remember import (
    RememberAttemptCreateRequest,
    RememberAttemptResponse,
    RememberDeleteResponse,
    RememberLeaderboardEntryResponse,
    RememberTodayLeaderboardResponse,
)

LanguageCode = Literal["ko", "en"]

LOCAL_TIMEZONE = ZoneInfo(REMEMBER_TIMEZONE)
DIFFICULTY_ORDER = {
    "easy": 0,
    "medium": 1,
    "hard": 2,
    "pro": 3,
    "elite": 4,
}
DIFFICULTY_LABELS = {
    "easy": {"ko": "쉬움", "en": "Easy"},
    "medium": {"ko": "중간", "en": "Medium"},
    "hard": {"ko": "어려움", "en": "Hard"},
    "pro": {"ko": "프로", "en": "Pro"},
    "elite": {"ko": "상위 랭커", "en": "Elite"},
}
LANE_LABELS = {
    "easy": {"ko": "입문 라인", "en": "Entry lane"},
    "medium": {"ko": "확장 라인", "en": "Expansion lane"},
    "hard": {"ko": "집중 라인", "en": "Focus lane"},
    "pro": {"ko": "실전 라인", "en": "Competition lane"},
    "elite": {"ko": "챔피언 라인", "en": "Champion lane"},
}


class RememberRecordNotFoundError(ValueError):
    pass


def get_today_leaderboard(
    db: Session,
    language: LanguageCode = "ko",
) -> RememberTodayLeaderboardResponse:
    start, end = _today_bounds()
    records = (
        db.query(RememberAttemptRecord)
        .filter(RememberAttemptRecord.achieved_at >= start)
        .filter(RememberAttemptRecord.achieved_at < end)
        .all()
    )

    best_by_slot: dict[tuple[str, str, str], RememberAttemptRecord] = {}
    for record in records:
        key = (record.device_id, record.discipline, record.difficulty_id)
        current = best_by_slot.get(key)
        if current is None or _compare_same_slot(record, current) > 0:
            best_by_slot[key] = record

    entries = [
        _to_leaderboard_entry(record=record, language=language)
        for record in best_by_slot.values()
    ]
    entries.sort(key=_leaderboard_sort_key)

    return RememberTodayLeaderboardResponse(
        updatedAt=_to_iso_string(datetime.now(LOCAL_TIMEZONE).replace(tzinfo=None)),
        entries=entries,
    )


def create_attempt_record(
    db: Session,
    payload: RememberAttemptCreateRequest,
    language: LanguageCode = "ko",
) -> RememberAttemptResponse:
    achieved_at = _normalize_datetime(payload.achievedAt)
    nickname = payload.nickname.strip() or REMEMBER_DEFAULT_NICKNAME
    difficulty_label = (
        payload.difficultyLabel.strip()
        if payload.difficultyLabel and payload.difficultyLabel.strip()
        else _difficulty_label(payload.difficultyId, language="ko")
    )

    record = RememberAttemptRecord(
        public_id=f"remember-{uuid4().hex}",
        device_id=payload.deviceId,
        nickname=nickname,
        discipline=payload.discipline,
        difficulty_id=payload.difficultyId,
        difficulty_label=difficulty_label,
        duration_ms=payload.durationMs,
        accuracy=payload.accuracy,
        total_items=payload.totalItems,
        correct_items=payload.correctItems,
        summary=payload.summary.strip() if payload.summary else None,
        achieved_at=achieved_at,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return _to_attempt_response(record=record, language=language)


def list_attempt_records(
    db: Session,
    language: LanguageCode = "ko",
    device_id: str | None = None,
    discipline: str | None = None,
    difficulty_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 100,
) -> list[RememberAttemptResponse]:
    query = db.query(RememberAttemptRecord)

    if device_id:
        query = query.filter(RememberAttemptRecord.device_id == device_id)
    if discipline:
        query = query.filter(RememberAttemptRecord.discipline == discipline)
    if difficulty_id:
        query = query.filter(RememberAttemptRecord.difficulty_id == difficulty_id)
    if date_from:
        query = query.filter(RememberAttemptRecord.achieved_at >= _normalize_datetime(date_from))
    if date_to:
        query = query.filter(RememberAttemptRecord.achieved_at <= _normalize_datetime(date_to))

    records = (
        query.order_by(
            RememberAttemptRecord.achieved_at.desc(),
            RememberAttemptRecord.created_at.desc(),
        )
        .limit(limit)
        .all()
    )

    return [_to_attempt_response(record=record, language=language) for record in records]


def get_attempt_record(
    db: Session,
    record_id: str,
    language: LanguageCode = "ko",
) -> RememberAttemptResponse:
    record = _get_record_or_raise(db=db, record_id=record_id)
    return _to_attempt_response(record=record, language=language)


def delete_attempt_record(db: Session, record_id: str) -> RememberDeleteResponse:
    record = _get_record_or_raise(db=db, record_id=record_id)
    db.delete(record)
    db.commit()
    return RememberDeleteResponse(id=record_id)


def _get_record_or_raise(db: Session, record_id: str) -> RememberAttemptRecord:
    record = (
        db.query(RememberAttemptRecord)
        .filter(RememberAttemptRecord.public_id == record_id)
        .first()
    )
    if record is None:
        raise RememberRecordNotFoundError(f"Remember record not found: {record_id}")
    return record


def _to_attempt_response(
    record: RememberAttemptRecord,
    language: LanguageCode = "ko",
) -> RememberAttemptResponse:
    return RememberAttemptResponse(
        id=record.public_id,
        deviceId=record.device_id,
        nickname=record.nickname,
        discipline=record.discipline,
        difficultyId=record.difficulty_id,
        difficultyLabel=_difficulty_label(record.difficulty_id, language, record.difficulty_label),
        durationMs=record.duration_ms,
        accuracy=record.accuracy,
        totalItems=record.total_items,
        correctItems=record.correct_items,
        summary=record.summary,
        achievedAt=_to_iso_string(record.achieved_at),
        createdAt=_to_iso_string(record.created_at),
    )


def _to_leaderboard_entry(
    record: RememberAttemptRecord,
    language: LanguageCode = "ko",
) -> RememberLeaderboardEntryResponse:
    return RememberLeaderboardEntryResponse(
        id=record.public_id,
        nickname=record.nickname,
        discipline=record.discipline,
        difficultyId=record.difficulty_id,
        difficultyLabel=_difficulty_label(record.difficulty_id, language, record.difficulty_label),
        durationMs=record.duration_ms,
        accuracy=record.accuracy,
        achievedAt=_to_iso_string(record.achieved_at),
        descriptor=str(record.correct_items),
        laneLabel=_lane_label(record.difficulty_id, language),
    )


def _compare_same_slot(candidate: RememberAttemptRecord, current: RememberAttemptRecord) -> int:
    if candidate.correct_items != current.correct_items:
        return 1 if candidate.correct_items > current.correct_items else -1
    if candidate.accuracy != current.accuracy:
        return 1 if candidate.accuracy > current.accuracy else -1
    if candidate.duration_ms != current.duration_ms:
        return 1 if candidate.duration_ms < current.duration_ms else -1
    if candidate.achieved_at != current.achieved_at:
        return 1 if candidate.achieved_at < current.achieved_at else -1
    return 0


def _leaderboard_sort_key(entry: RememberLeaderboardEntryResponse) -> tuple[int, int, int, datetime]:
    difficulty_rank = DIFFICULTY_ORDER.get(entry.difficultyId, -1)
    achieved_at = _parse_iso_string(entry.achievedAt)
    return (-difficulty_rank, -entry.accuracy, entry.durationMs, achieved_at)


def _difficulty_label(
    difficulty_id: str,
    language: LanguageCode = "ko",
    fallback: str | None = None,
) -> str:
    label_map = DIFFICULTY_LABELS.get(difficulty_id)
    if label_map:
        return label_map[language]
    return fallback or difficulty_id


def _lane_label(difficulty_id: str, language: LanguageCode = "ko") -> str:
    label_map = LANE_LABELS.get(difficulty_id)
    if label_map:
        return label_map[language]
    return difficulty_id


def _normalize_datetime(value: datetime | None) -> datetime:
    if value is None:
        localized = datetime.now(LOCAL_TIMEZONE)
    elif value.tzinfo is None:
        localized = value.replace(tzinfo=LOCAL_TIMEZONE)
    else:
        localized = value.astimezone(LOCAL_TIMEZONE)

    return localized.replace(tzinfo=None)


def _to_iso_string(value: datetime) -> str:
    localized = value.replace(tzinfo=LOCAL_TIMEZONE)
    return localized.isoformat()


def _parse_iso_string(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _today_bounds() -> tuple[datetime, datetime]:
    now = datetime.now(LOCAL_TIMEZONE)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.replace(tzinfo=None), end.replace(tzinfo=None)
