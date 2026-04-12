"""
사신게임 퀵 솔로 모드 엔진.
공개 단서 2개 -> 단일 낮 투표 -> 밤 행동 루프로 진행한다.
"""
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

import app.Reaper.core.firebase_db as fdb
from app.Reaper.models.game import ReaperGame, ReaperPlayer
from app.Reaper.services.claim_generator import (
    ROLE_ANGEL,
    ROLE_CITIZEN,
    ROLE_ORACLE,
    ROLE_REAPER,
    TOWN_ROLES,
)

logger = logging.getLogger(__name__)

PHASE_TIMEOUTS = {
    "day_vote1": 60,
    "night": 60,
}

SPECIAL_ROLES = {ROLE_ANGEL, ROLE_ORACLE}
NIGHT_ACTION_ROLES = {ROLE_REAPER, ROLE_ANGEL, ROLE_ORACLE}


def _now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def _game_path(game_id: str) -> str:
    return f"games/{game_id}"


def assign_roles(player_count: int) -> list[str]:
    base_roles = [ROLE_REAPER, ROLE_CITIZEN]
    if player_count >= 3:
        base_roles.append(ROLE_ANGEL)
    if player_count >= 4:
        base_roles.append(ROLE_ORACLE)
    if player_count >= 5:
        base_roles.append(ROLE_CITIZEN)
    if player_count >= 6:
        base_roles.append(ROLE_CITIZEN)
    if player_count >= 7:
        base_roles.extend([ROLE_CITIZEN] * (player_count - 6))

    roles = base_roles[:player_count]
    random.shuffle(roles)
    return roles


def _has_night_action(role: str) -> bool:
    return role in NIGHT_ACTION_ROLES


def _is_town(role: str) -> bool:
    return role in TOWN_ROLES


def _build_public_clues(players: list[ReaperPlayer], game_data: Optional[dict] = None) -> list[str]:
    alive_players = [player for player in players if player.is_alive]
    if not alive_players:
        return []

    game_data = game_data or {}
    dynamic_clues: list[str] = []
    static_clues: list[str] = []

    last_night = game_data.get("last_night_kill_success")
    if last_night is not None:
        dynamic_clues.append(
            "지난밤 공격은 성공했습니다." if last_night else "지난밤 공격은 막혔습니다."
        )


    special_count = sum(1 for player in alive_players if player.role in SPECIAL_ROLES)
    static_clues.append(
        "살아있는 특수 역할은 2명 이상입니다."
        if special_count >= 2
        else "살아있는 특수 역할은 1명 이하입니다."
    )

    sample_player = random.choice(alive_players)
    static_clues.append(
        f"{sample_player.seat_number}번은 밤 행동이 있습니다."
        if _has_night_action(sample_player.role)
        else f"{sample_player.seat_number}번은 밤 행동이 없습니다."
    )

    if len(alive_players) >= 2:
        first, second = random.sample(alive_players, 2)
        static_clues.append(
            f"{first.seat_number}번과 {second.seat_number}번은 같은 편입니다."
            if _is_town(first.role) == _is_town(second.role)
            else f"{first.seat_number}번과 {second.seat_number}번은 다른 편입니다."
        )
        static_clues.append(
            f"{first.seat_number}번과 {second.seat_number}번 중 한 명 이상은 밤 행동이 있습니다."
            if _has_night_action(first.role) or _has_night_action(second.role)
            else f"{first.seat_number}번과 {second.seat_number}번은 둘 다 밤 행동이 없습니다."
        )

    if len(alive_players) >= 3:
        candidate = random.choice(alive_players)
        static_clues.append(
            f"{candidate.seat_number}번은 일반 역할입니다."
            if candidate.role == ROLE_CITIZEN
            else f"{candidate.seat_number}번은 일반 역할이 아닙니다."
        )

    selected: list[str] = []
    seen = set()

    for clue in dynamic_clues:
        if clue in seen:
            continue
        selected.append(clue)
        seen.add(clue)
        if len(selected) >= 2:
            return selected

    random.shuffle(static_clues)
    for clue in static_clues:
        if clue in seen:
            continue
        selected.append(clue)
        seen.add(clue)
        if len(selected) >= 2:
            break

    return selected


def _initial_game_state(players: list[ReaperPlayer]) -> dict:
    return {
        "phase": "day_vote1",
        "turn": 1,
        "phase_end_time": _now_ts() + PHASE_TIMEOUTS["day_vote1"],
        "votes": {},
        "night_actions": {},
        "vote_result": None,
        "top_candidate": None,
        "night_result": {"killed_uid": None, "success": False},
        "prev_exiled": None,
        "prev_exiled_role": None,
        "last_night_kill_success": None,
        "last_night_angel_protected": False,
        "winner": None,
        "public_clues": _build_public_clues(players, {}),
        "final_vote_result": None,
        "exiled_this_day": None,
        "killed_this_night": None,
        "oracle_investigated": [],
    }


def start_game(game_id: str, db: Session) -> dict:
    game = db.query(ReaperGame).filter(ReaperGame.id == game_id).first()
    if not game:
        raise ValueError("Game not found")
    if game.status != "waiting":
        raise ValueError("Game already started")

    players = db.query(ReaperPlayer).filter(
        ReaperPlayer.game_id == game_id
    ).order_by(ReaperPlayer.seat_number).all()
    if len(players) < 2:
        raise ValueError("Not enough players")

    roles = assign_roles(len(players))

    # 플레이어(index 0, seat 1)가 시민이 되지 않도록 보장
    if roles[0] == ROLE_CITIZEN:
        for i in range(1, len(roles)):
            if roles[i] != ROLE_CITIZEN:
                roles[0], roles[i] = roles[i], roles[0]
                break

    for index, player in enumerate(players):
        player.role = roles[index]
        player.is_alive = True

    game.status = "playing"
    game.started_at = datetime.utcnow()
    db.commit()

    firebase_players = {
        player.uid: {
            "uid": player.uid,
            "nickname": player.nickname,
            "hashtag": player.hashtag,
            "is_bot": player.is_bot,
            "seat_number": player.seat_number,
            "is_alive": True,
            "role": None,
            "grim_score": 50,
            "power_score": 20,
            "influence_score": 30,
        }
        for player in players
    }

    initial_state = _initial_game_state(players)

    fdb.set_path(_game_path(game_id), {
        "id": game_id,
        "mode": "solo",
        "status": "playing",
        "players": firebase_players,
        "game": initial_state,
    })

    for player in players:
        fdb.set_path(f"{_game_path(game_id)}/private/{player.uid}", {"role": player.role})

    return {"game_id": game_id, "phase": "day_vote1", "turn": 1}


def submit_vote(game_id: str, player_uid: str, target_uid: str, db: Session):
    fdb.set_path(f"{_game_path(game_id)}/game/votes/{player_uid}", target_uid)
    _check_all_votes(game_id, db)


def submit_night_action(game_id: str, player_uid: str, target_uid: str, db: Session):
    fdb.set_path(f"{_game_path(game_id)}/game/night_actions/{player_uid}", target_uid)

    try:
        from app.Reaper.services.bot_scheduler import fast_track_bot_night_actions

        fast_track_bot_night_actions(game_id)
    except Exception as exc:
        logger.warning("[Game] fast night bot schedule failed: %s", exc)

    _check_all_night_actions(game_id, db)


def _check_all_votes(game_id: str, db: Session):
    game_data = fdb.get_path(f"{_game_path(game_id)}/game") or {}
    if game_data.get("phase") != "day_vote1":
        return
    votes = game_data.get("votes", {}) or {}
    players_data = fdb.get_path(f"{_game_path(game_id)}/players") or {}
    alive_uids = [uid for uid, player in players_data.items() if player.get("is_alive")]

    if not alive_uids:
        return

    if all(uid in votes for uid in alive_uids):
        _process_vote1(game_id, game_data, db)


def _check_all_night_actions(game_id: str, db: Session):
    game_data = fdb.get_path(f"{_game_path(game_id)}/game") or {}
    if game_data.get("phase") != "night":
        return
    night_actions = game_data.get("night_actions", {}) or {}
    players = db.query(ReaperPlayer).filter(
        ReaperPlayer.game_id == game_id,
        ReaperPlayer.is_alive == True,
    ).all()
    actor_uids = [player.uid for player in players if player.role in NIGHT_ACTION_ROLES]

    if not actor_uids:
        return

    if all(uid in night_actions for uid in actor_uids):
        _process_night(game_id, game_data, players, db)


def _transition_to_day_vote(game_id: str, db: Session, turn: int, base_game_data: Optional[dict] = None):
    players = db.query(ReaperPlayer).filter(ReaperPlayer.game_id == game_id).all()
    game_data = base_game_data or fdb.get_path(f"{_game_path(game_id)}/game") or {}
    public_clues = _build_public_clues(players, game_data)

    fdb.update_path(f"{_game_path(game_id)}/game", {
        "phase": "day_vote1",
        "turn": turn,
        "phase_end_time": _now_ts() + PHASE_TIMEOUTS["day_vote1"],
        "votes": {},
        "night_actions": {},
        "vote_result": None,
        "top_candidate": None,
        "public_clues": public_clues,
        "exiled_this_day": None,
        "killed_this_night": None,
        "final_vote_result": None,
    })

    try:
        from app.Reaper.services.bot_scheduler import schedule_bot_votes, schedule_phase_timeout

        schedule_bot_votes(game_id, "votes")
        schedule_phase_timeout(game_id, "day_vote1", PHASE_TIMEOUTS["day_vote1"])
    except Exception as exc:
        logger.warning("[Game] bot vote schedule failed: %s", exc)


def _process_vote1(game_id: str, game_data: dict, db: Session):
    votes = game_data.get("votes", {}) or {}
    tally: dict[str, int] = {}
    for target_uid in votes.values():
        if target_uid:
            tally[target_uid] = tally.get(target_uid, 0) + 1

    if not tally:
        _transition_to_night(game_id, db)
        return

    max_votes = max(tally.values())
    leaders = [uid for uid, count in tally.items() if count == max_votes]
    update_data = {
        "vote_result": {"tally": tally, "leaders": leaders},
        "top_candidate": leaders[0] if len(leaders) == 1 else None,
    }

    if len(leaders) != 1:
        update_data["final_vote_result"] = {"exiled": False}
        fdb.update_path(f"{_game_path(game_id)}/game", update_data)
        _transition_to_night(game_id, db)
        return

    exiled_uid = leaders[0]
    player = db.query(ReaperPlayer).filter(
        ReaperPlayer.game_id == game_id,
        ReaperPlayer.uid == exiled_uid,
    ).first()
    if not player:
        _transition_to_night(game_id, db)
        return

    player.is_alive = False
    db.commit()

    exiled_role = player.role
    fdb.update_path(f"{_game_path(game_id)}/players/{exiled_uid}", {"is_alive": False})
    fdb.update_path(f"{_game_path(game_id)}/game", {
        **update_data,
        "prev_exiled": exiled_uid,
        "prev_exiled_role": exiled_role,
        "exiled_this_day": {"uid": exiled_uid, "role": exiled_role},
        "final_vote_result": {"exiled": True, "uid": exiled_uid, "role": exiled_role},
    })

    if _check_win_condition(game_id, db):
        return

    _transition_to_night(game_id, db)


def _transition_to_night(game_id: str, db: Session):
    fdb.update_path(f"{_game_path(game_id)}/game", {
        "phase": "night",
        "phase_end_time": _now_ts() + PHASE_TIMEOUTS["night"],
        "night_actions": {},
    })

    try:
        from app.Reaper.services.bot_scheduler import schedule_bot_night_actions, schedule_phase_timeout

        schedule_bot_night_actions(game_id)
        schedule_phase_timeout(game_id, "night", PHASE_TIMEOUTS["night"])
    except Exception as exc:
        logger.warning("[Game] bot night schedule failed: %s", exc)


def _process_night(game_id: str, game_data: dict, players: list[ReaperPlayer], db: Session):
    night_actions = game_data.get("night_actions", {}) or {}
    oracle_investigated = game_data.get("oracle_investigated", []) or []

    angel_target = None
    oracle_target = None
    reaper_target = None

    for player in players:
        action = night_actions.get(player.uid)
        if not action:
            continue
        if player.role == ROLE_ANGEL:
            angel_target = action
        elif player.role == ROLE_ORACLE:
            oracle_target = action
        elif player.role == ROLE_REAPER:
            reaper_target = action

    killed_uid = None
    kill_success = False
    angel_protected = False

    if reaper_target:
        target_player = next((player for player in players if player.uid == reaper_target), None)
        if target_player:
            if target_player.role == ROLE_ANGEL:
                kill_success = False
            elif angel_target == reaper_target:
                kill_success = False
                angel_protected = True
            else:
                kill_success = True
                killed_uid = reaper_target
                target_player.is_alive = False
                db.commit()
                fdb.update_path(f"{_game_path(game_id)}/players/{reaper_target}", {"is_alive": False})

    if oracle_target:
        oracle = next((player for player in players if player.role == ROLE_ORACLE), None)
        target = next((player for player in players if player.uid == oracle_target), None)
        if oracle and target:
            fdb.set_path(
                f"{_game_path(game_id)}/private/{oracle.uid}/oracle_result",
                {"target_uid": oracle_target, "role": target.role},
            )
            if oracle_target not in oracle_investigated:
                oracle_investigated.append(oracle_target)

    game_update = {
        "night_result": {"killed_uid": killed_uid, "success": kill_success},
        "last_night_kill_success": kill_success,
        "last_night_angel_protected": angel_protected,
        "oracle_investigated": oracle_investigated,
    }
    if killed_uid:
        game_update["killed_this_night"] = killed_uid

    fdb.update_path(f"{_game_path(game_id)}/game", game_update)

    if _check_win_condition(game_id, db):
        return

    _transition_to_next_day(game_id, game_data, db)


def _transition_to_next_day(game_id: str, game_data: dict, db: Session):
    next_turn = game_data.get("turn", 1) + 1
    refreshed_game_data = {**game_data, **(fdb.get_path(f"{_game_path(game_id)}/game") or {})}
    _transition_to_day_vote(game_id, db, next_turn, refreshed_game_data)


def _check_win_condition(game_id: str, db: Session) -> bool:
    players = db.query(ReaperPlayer).filter(ReaperPlayer.game_id == game_id).all()
    alive_players = [player for player in players if player.is_alive]
    reaper_alive = [player for player in alive_players if player.role == ROLE_REAPER]
    town_alive = [player for player in alive_players if player.role in TOWN_ROLES]

    winner = None
    if not reaper_alive:
        winner = "town"
    elif len(reaper_alive) >= len(town_alive):
        winner = "reaper"

    if not winner:
        return False

    game = db.query(ReaperGame).filter(ReaperGame.id == game_id).first()
    if game:
        game.status = "ended"
        game.winner = winner
        game.ended_at = datetime.utcnow()
        db.commit()

    reveal = {player.uid: player.role for player in players}
    fdb.update_path(f"{_game_path(game_id)}/game", {
        "winner": winner,
        "phase": "ended",
        "role_reveal": reveal,
    })
    fdb.update_path(_game_path(game_id), {"status": "ended"})
    logger.info("[Game] %s ended: winner=%s", game_id, winner)
    return True


def handle_phase_timeout(game_id: str, expected_phase: str, db: Session):
    game_data = fdb.get_path(f"{_game_path(game_id)}/game") or {}
    if game_data.get("phase") != expected_phase:
        return

    players_data = fdb.get_path(f"{_game_path(game_id)}/players") or {}
    alive_uids = [uid for uid, player in players_data.items() if player.get("is_alive")]

    if expected_phase == "day_vote1":
        votes = game_data.get("votes", {}) or {}
        for uid in alive_uids:
            if uid in votes:
                continue
            candidates = [target_uid for target_uid in alive_uids if target_uid != uid]
            if not candidates:
                continue
            fdb.set_path(f"{_game_path(game_id)}/game/votes/{uid}", random.choice(candidates))
        refreshed = fdb.get_path(f"{_game_path(game_id)}/game") or game_data
        _process_vote1(game_id, refreshed, db)
        return

    if expected_phase == "night":
        players = db.query(ReaperPlayer).filter(
            ReaperPlayer.game_id == game_id,
            ReaperPlayer.is_alive == True,
        ).all()
        night_actions = game_data.get("night_actions", {}) or {}
        for player in players:
            if player.role not in NIGHT_ACTION_ROLES or player.uid in night_actions:
                continue
            candidates = [uid for uid in alive_uids if uid != player.uid]
            if not candidates:
                continue
            fdb.set_path(
                f"{_game_path(game_id)}/game/night_actions/{player.uid}",
                random.choice(candidates),
            )
        refreshed = fdb.get_path(f"{_game_path(game_id)}/game") or game_data
        _process_night(game_id, refreshed, players, db)
