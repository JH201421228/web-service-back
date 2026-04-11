"""
솔로 사신게임 API.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

import app.Reaper.core.firebase_db as fdb
from app.Reaper.core.deps import get_reaper_db
from app.Reaper.models.game import ReaperPlayer
from app.Reaper.schemas.game import NightActionRequest, VoteRequest
from app.Reaper.schemas.session import SoloStartResponse
from app.Reaper.services import bot_scheduler, game_engine
from app.Reaper.services.solo_game_service import create_solo_game, generate_random_nickname

router = APIRouter(tags=["Reaper Game"])


def _get_uid(x_uid: Optional[str] = Header(None)) -> str:
    if not x_uid:
        raise HTTPException(status_code=401, detail="X-Uid header required")
    return x_uid


def _get_game_id(x_game_id: Optional[str] = Header(None, alias="X-Game-Id")) -> str:
    if not x_game_id:
        raise HTTPException(status_code=401, detail="X-Game-Id header required")
    return x_game_id


def _get_player(game_id: str, uid: str, db: Session) -> ReaperPlayer:
    player = db.query(ReaperPlayer).filter(
        ReaperPlayer.game_id == game_id,
        ReaperPlayer.uid == uid,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not in game")
    if not player.is_alive:
        raise HTTPException(status_code=400, detail="Player is not alive")
    return player


@router.post("/solo/start", response_model=SoloStartResponse)
def solo_start(db: Session = Depends(get_reaper_db)):
    uid = f"solo_{uuid.uuid4().hex[:12]}"
    nickname, hashtag = generate_random_nickname()
    game = create_solo_game(uid, nickname, hashtag, db, bot_count=5)
    result = game_engine.start_game(game.id, db)

    bot_scheduler.schedule_bot_votes(game.id, "votes")
    bot_scheduler.schedule_phase_timeout(game.id, "day_vote1", game_engine.PHASE_TIMEOUTS["day_vote1"])

    return SoloStartResponse(
        game_id=result["game_id"],
        uid=uid,
        nickname=nickname,
        hashtag=hashtag,
        is_guest=True,
        avatar_seed=uid,
    )


@router.post("/solo/vote")
def submit_vote(
    req: VoteRequest,
    db: Session = Depends(get_reaper_db),
    uid: str = Depends(_get_uid),
    game_id: str = Depends(_get_game_id),
):
    _get_player(game_id, uid, db)
    game_data = fdb.get_path(f"games/{game_id}/game") or {}
    if game_data.get("phase") != "day_vote1":
        raise HTTPException(status_code=400, detail="Not in vote phase")

    game_engine.submit_vote(game_id, uid, req.target_uid, db)
    return {"ok": True}


@router.post("/solo/night-action")
def night_action(
    req: NightActionRequest,
    db: Session = Depends(get_reaper_db),
    uid: str = Depends(_get_uid),
    game_id: str = Depends(_get_game_id),
):
    player = _get_player(game_id, uid, db)
    game_data = fdb.get_path(f"games/{game_id}/game") or {}
    if game_data.get("phase") != "night":
        raise HTTPException(status_code=400, detail="Not in night phase")

    from app.Reaper.services.claim_generator import ROLE_ANGEL, ROLE_ORACLE, ROLE_REAPER

    if player.role not in (ROLE_REAPER, ROLE_ANGEL, ROLE_ORACLE):
        raise HTTPException(status_code=400, detail="Your role has no night action")

    game_engine.submit_night_action(game_id, uid, req.target_uid, db)
    return {"ok": True}


@router.get("/solo/my-role")
def get_my_role(
    db: Session = Depends(get_reaper_db),
    uid: str = Depends(_get_uid),
    game_id: str = Depends(_get_game_id),
):
    player = db.query(ReaperPlayer).filter(
        ReaperPlayer.game_id == game_id,
        ReaperPlayer.uid == uid,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return {
        "uid": uid,
        "role": player.role,
        "seat_number": player.seat_number,
        "is_alive": player.is_alive,
    }
