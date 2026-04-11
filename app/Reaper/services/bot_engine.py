"""
봇 엔진: 낮 투표와 밤 행동만 자동 처리한다.
"""
import logging
import random
from typing import Optional

from sqlalchemy.orm import Session

import app.Reaper.core.firebase_db as fdb
from app.Reaper.models.game import ReaperPlayer
from app.Reaper.services.claim_generator import ROLE_ANGEL, ROLE_ORACLE, ROLE_REAPER

logger = logging.getLogger(__name__)

BOT_ARCHETYPES = [
    {
        "name": "aggressive",
        "vote_noise": 10,
        "chaos": 0.10,
        "grim_weight": 1.15,
        "reaper_power_weight": 1.15,
        "angel_self_bias": 8,
    },
    {
        "name": "steady",
        "vote_noise": 6,
        "chaos": 0.05,
        "grim_weight": 1.0,
        "reaper_power_weight": 1.0,
        "angel_self_bias": 14,
    },
    {
        "name": "swing",
        "vote_noise": 14,
        "chaos": 0.18,
        "grim_weight": 0.95,
        "reaper_power_weight": 0.95,
        "angel_self_bias": 10,
    },
    {
        "name": "chaotic",
        "vote_noise": 18,
        "chaos": 0.28,
        "grim_weight": 0.9,
        "reaper_power_weight": 1.05,
        "angel_self_bias": 6,
    },
]


def _bot_profile(bot_uid: str) -> dict:
    seed = sum((index + 1) * ord(char) for index, char in enumerate(bot_uid))
    return BOT_ARCHETYPES[seed % len(BOT_ARCHETYPES)]


def _weighted_pick(options: list, raw_score_fn, chaos: float = 0.0):
    if not options:
        return None
    if len(options) == 1:
        return options[0]
    if random.random() < chaos:
        return random.choice(options)

    raw_scores = [raw_score_fn(option) for option in options]
    floor = min(raw_scores)
    weights = [max(1.0, score - floor + 6.0) for score in raw_scores]
    return random.choices(options, weights=weights, k=1)[0]


def _get_alive_bots(game_id: str, db: Session) -> list[ReaperPlayer]:
    return db.query(ReaperPlayer).filter(
        ReaperPlayer.game_id == game_id,
        ReaperPlayer.is_bot == True,
        ReaperPlayer.is_alive == True,
    ).all()


def _get_bot_scores(game_id: str) -> dict:
    scores = {}
    players_data = fdb.get_path(f"games/{game_id}/players") or {}
    for uid, player in players_data.items():
        scores[uid] = {
            "grim_score": player.get("grim_score", 50),
            "power_score": player.get("power_score", 20),
            "influence_score": player.get("influence_score", 30),
        }
    return scores


def bot_submit_votes(game_id: str, vote_key: str, db: Session, candidates: Optional[list] = None):
    bots = _get_alive_bots(game_id, db)
    game_data = fdb.get_path(f"games/{game_id}/game") or {}
    votes = game_data.get(vote_key, {}) or {}
    bot_scores = _get_bot_scores(game_id)

    players_data = fdb.get_path(f"games/{game_id}/players") or {}
    alive_uids = [uid for uid, player in players_data.items() if player.get("is_alive")]

    for bot in bots:
        if bot.uid in votes:
            continue

        vote_pool = candidates if candidates else [uid for uid in alive_uids if uid != bot.uid]
        if not vote_pool:
            continue

        profile = _bot_profile(bot.uid)
        target = _weighted_pick(
            vote_pool,
            lambda uid: (
                bot_scores.get(uid, {}).get("grim_score", 50) * profile["grim_weight"]
                + bot_scores.get(uid, {}).get("influence_score", 30) * 0.15
                + random.uniform(-profile["vote_noise"], profile["vote_noise"])
            ),
            chaos=profile["chaos"],
        )
        fdb.set_path(f"games/{game_id}/game/{vote_key}/{bot.uid}", target)


def bot_submit_night_actions(game_id: str, db: Session):
    bots = _get_alive_bots(game_id, db)
    game_data = fdb.get_path(f"games/{game_id}/game") or {}
    if game_data.get("phase") != "night":
        return

    night_actions = game_data.get("night_actions", {}) or {}
    bot_scores = _get_bot_scores(game_id)
    players_data = fdb.get_path(f"games/{game_id}/players") or {}
    all_players = db.query(ReaperPlayer).filter(ReaperPlayer.game_id == game_id).all()
    role_map = {player.uid: player.role for player in all_players}
    alive_uids = [uid for uid, player in players_data.items() if player.get("is_alive")]

    for bot in bots:
        if bot.uid in night_actions:
            continue
        if bot.role not in (ROLE_REAPER, ROLE_ANGEL, ROLE_ORACLE):
            continue

        profile = _bot_profile(bot.uid)
        other_alive = [uid for uid in alive_uids if uid != bot.uid]
        if not other_alive:
            continue

        if bot.role == ROLE_REAPER:
            target = _weighted_pick(
                other_alive,
                lambda uid: (
                    bot_scores.get(uid, {}).get("influence_score", 30)
                    + bot_scores.get(uid, {}).get("power_score", 20) * profile["reaper_power_weight"]
                    - (18 if role_map.get(uid) == ROLE_ANGEL else 0)
                    + random.uniform(-8, 8)
                ),
                chaos=profile["chaos"],
            )
        elif bot.role == ROLE_ANGEL:
            protect_pool = [bot.uid] + other_alive
            target = _weighted_pick(
                protect_pool,
                lambda uid: (
                    (100 - bot_scores.get(uid, {}).get("grim_score", 50))
                    + bot_scores.get(uid, {}).get("influence_score", 30) * 0.5
                    + (profile["angel_self_bias"] if uid == bot.uid else 0)
                    + random.uniform(-10, 10)
                ),
                chaos=max(0.04, profile["chaos"] * 0.7),
            )
        else:
            investigated = game_data.get("oracle_investigated", []) or []
            uninvestigated = [uid for uid in other_alive if uid not in investigated]
            pool = uninvestigated if uninvestigated else other_alive
            target = _weighted_pick(
                pool,
                lambda uid: (
                    bot_scores.get(uid, {}).get("grim_score", 50) * (profile["grim_weight"] + 0.05)
                    + (12 if uid not in investigated else 0)
                    + random.uniform(-7, 7)
                ),
                chaos=max(0.03, profile["chaos"] * 0.6),
            )

        fdb.set_path(f"games/{game_id}/game/night_actions/{bot.uid}", target)
        logger.debug("[Bot] %s night action -> %s", bot.uid, target)
