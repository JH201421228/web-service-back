"""
공식 주장 템플릿 생성기.
역할별 진실/거짓 규칙에 따라 선택 가능한 후보를 생성한다.
"""
import random
from typing import Any


# 역할 상수
ROLE_REAPER = "reaper"
ROLE_CITIZEN = "citizen"
ROLE_ANGEL = "angel"
ROLE_ORACLE = "oracle"
ROLE_DETECTIVE = "detective"

TOWN_ROLES = {ROLE_CITIZEN, ROLE_ANGEL, ROLE_ORACLE, ROLE_DETECTIVE}

# 진실만 말해야 하는 역할
TRUTH_ROLES = {ROLE_REAPER, ROLE_ANGEL}
# 거짓만 말해야 하는 역할
LIE_ROLES = {ROLE_CITIZEN, ROLE_ORACLE, ROLE_DETECTIVE}

# 역할 속성
ROLE_ATTRS = {
    ROLE_REAPER:   {"is_town": False, "is_special": True,  "has_night": True,  "has_attack": True,  "has_protect": False, "has_investigate": False, "has_reveal": False, "survives_night": False},
    ROLE_CITIZEN:  {"is_town": True,  "is_special": False, "has_night": False, "has_attack": False, "has_protect": False, "has_investigate": False, "has_reveal": False, "survives_night": False},
    ROLE_ANGEL:    {"is_town": True,  "is_special": True,  "has_night": True,  "has_attack": False, "has_protect": True,  "has_investigate": False, "has_reveal": False, "survives_night": True},
    ROLE_ORACLE:   {"is_town": True,  "is_special": True,  "has_night": True,  "has_attack": False, "has_protect": False, "has_investigate": True,  "has_reveal": False, "survives_night": False},
    ROLE_DETECTIVE:{"is_town": True,  "is_special": True,  "has_night": False, "has_attack": False, "has_protect": False, "has_investigate": False, "has_reveal": True,  "survives_night": False},
}


def _attr(role: str, key: str) -> bool:
    return ROLE_ATTRS.get(role, {}).get(key, False)


def _eval_self_template(template_id: int, my_role: str, game_state: dict) -> bool | None:
    """자기 자신 관련 핵심 정보문 진실 여부 평가 (None = 평가 불가)"""
    a = ROLE_ATTRS.get(my_role, {})
    survivors = game_state.get("survivors", [])
    prev_exiled = game_state.get("prev_exiled_role")

    match template_id:
        case 1: return a.get("is_town", False)           # 나는 선역이다
        case 2: return not a.get("is_town", True)        # 나는 사신 진영이다
        case 3: return not a.get("is_special", True)     # 나는 일반 역할이다
        case 4: return a.get("is_special", False)        # 나는 특수 역할이다
        case 5: return a.get("has_night", False)         # 나는 밤 행동이 있다
        case 6: return not a.get("has_night", True)      # 나는 밤 행동이 없다
        case 7: return a.get("has_attack", False)        # 나는 공격 능력이 있다
        case 8: return a.get("has_protect", False)       # 나는 보호 능력이 있다
        case 9: return a.get("has_investigate", False)   # 나는 조사 능력이 있다
        case 10: return a.get("has_reveal", False)       # 나는 공개 능력이 있다
        case 11: return a.get("survives_night", False)   # 밤 제거 대상이 되어도 생존
        case 12: return a.get("is_special", False)       # 핵심 역할로 분류됨
    return None


def _eval_target_template(template_id: int, target_role: str, game_state: dict) -> bool | None:
    """단일 대상 관련 핵심 정보문 진실 여부 평가"""
    a = ROLE_ATTRS.get(target_role, {})
    match template_id:
        case 13: return a.get("is_town", False)
        case 14: return not a.get("is_town", True)
        case 15: return not a.get("is_special", True)
        case 16: return a.get("is_special", False)
        case 17: return a.get("has_night", False)
        case 18: return not a.get("has_night", True)
        case 19: return a.get("has_attack", False)
        case 20: return a.get("has_protect", False)
        case 21: return a.get("has_investigate", False)
        case 22: return a.get("has_reveal", False)
        case 23: return a.get("survives_night", False)
    return None


def _eval_relation_template(template_id: int, role_x: str, role_y: str) -> bool | None:
    ax = ROLE_ATTRS.get(role_x, {})
    ay = ROLE_ATTRS.get(role_y, {})
    x_town = ax.get("is_town", False)
    y_town = ay.get("is_town", False)
    x_special = ax.get("is_special", False)
    y_special = ay.get("is_special", False)
    x_night = ax.get("has_night", False)
    y_night = ay.get("has_night", False)

    match template_id:
        case 24: return x_town == y_town
        case 25: return x_town != y_town
        case 26: return x_town or y_town
        case 27: return x_special or y_special
        case 28: return x_special != y_special
        case 29: return x_night or y_night
        case 30: return x_night != y_night
    return None


def _eval_state_template(template_id: int, game_state: dict, my_role: str) -> bool | None:
    """상태/이벤트 템플릿 진실 여부 평가"""
    last_night_kill_success = game_state.get("last_night_kill_success")
    last_night_angel_protected = game_state.get("last_night_angel_protected", False)
    survivors_roles = game_state.get("survivors_roles", [])
    prev_exiled_role = game_state.get("prev_exiled_role")
    survivor_reaper_count = survivors_roles.count(ROLE_REAPER)
    survivor_town_count = sum(1 for r in survivors_roles if r in TOWN_ROLES)

    match template_id:
        case 31:
            return last_night_kill_success if last_night_kill_success is not None else None
        case 32:
            return not last_night_kill_success if last_night_kill_success is not None else None
        case 33:
            return last_night_angel_protected
        case 34:
            return ROLE_ORACLE in survivors_roles
        case 35:
            return ROLE_DETECTIVE in survivors_roles
        case 36:
            return ROLE_ANGEL in survivors_roles
        case 37:
            return ROLE_REAPER in survivors_roles
        case 38:
            return survivors_roles.count(ROLE_CITIZEN) >= 2
        case 39:
            return sum(1 for r in survivors_roles if _attr(r, "is_special")) >= 2
        case 40:
            if prev_exiled_role is None:
                return None
            return prev_exiled_role in TOWN_ROLES
        case 41:
            if prev_exiled_role is None:
                return None
            return prev_exiled_role == ROLE_REAPER
        case 42:
            return survivor_town_count > survivor_reaper_count
    return None


# 행동 선언문 템플릿 (대상 변수 포함)
ACTION_TEMPLATES = [
    "오늘은 {X}번을 찍겠다.",
    "최종도 {X}번을 유지하겠다.",
    "오늘은 {X}번과 {Y}번 중 한 명을 보겠다.",
    "지금은 {X}번이 가장 수상하다.",
    "{X}번보다 {Y}번이 더 수상하다.",
    "오늘은 내 판단을 유지한다.",
    "오늘은 재투표까지 보겠다.",
    "지금은 정보 정리가 먼저다.",
]

REACTION_TEMPLATES = [
    "이 주장은 약하다.",
    "지금 지목은 빠르다.",
    "그쪽은 아직 보류다.",
    "오늘은 한 명만 보자.",
    "표가 너무 갈린다.",
    "재투표로 다시 보자.",
    "나는 기존 판단 유지.",
    "특수 역할 공개는 이르다.",
]


def _fill_action_template(template: str, survivors: list[dict]) -> str:
    """행동 선언문에 실제 플레이어 번호를 채운다."""
    if not survivors:
        return template
    seats = [str(p["seat_number"]) for p in survivors]
    if "{X}" in template and "{Y}" in template:
        chosen = random.sample(seats, min(2, len(seats)))
        x = chosen[0]
        y = chosen[1] if len(chosen) > 1 else chosen[0]
        return template.replace("{X}", x).replace("{Y}", y)
    if "{X}" in template:
        x = random.choice(seats)
        return template.replace("{X}", x)
    return template


def generate_candidates(
    my_uid: str,
    my_role: str,
    game_state: dict,
    survivors: list[dict],
    turn: int,
) -> dict:
    """
    역할에 따라 핵심 정보문 후보 4개와 행동 선언문 후보 4개를 생성한다.
    game_state: {
        survivors_roles, last_night_kill_success, last_night_angel_protected,
        prev_exiled_role, ...
    }
    survivors: [{uid, seat_number, role (None for others)}, ...]
    """
    must_be_true = my_role in TRUTH_ROLES  # True=진실만, False=거짓만

    other_survivors = [s for s in survivors if s["uid"] != my_uid]

    def make_self_candidates() -> list[dict]:
        candidates = []
        for tid in range(1, 13):
            truth = _eval_self_template(tid, my_role, game_state)
            if truth is None:
                continue
            valid = (truth == must_be_true)
            # 템플릿 텍스트 생성
            texts = [
                "나는 선역이다.", "나는 사신 편이다.", "나는 일반 역할이다.",
                "나는 특수 역할이다.", "나는 밤에 행동한다.", "나는 밤 행동이 없다.",
                "나는 공격이 있다.", "나는 보호가 있다.", "나는 조사가 있다.",
                "나는 공개가 있다.", "나는 밤 공격을 버틴다.",
                "나는 핵심 역할이다.",
            ]
            candidates.append({"idx": tid, "text": texts[tid - 1], "is_valid": valid, "truth": truth})
        return candidates

    def make_target_candidates() -> list[dict]:
        if not other_survivors:
            return []
        candidates = []
        target = random.choice(other_survivors)
        target_role = target.get("role")
        if target_role is None:
            return []
        seat = target["seat_number"]
        for tid in range(13, 24):
            truth = _eval_target_template(tid, target_role, game_state)
            if truth is None:
                continue
            valid = (truth == must_be_true)
            texts = [
                f"{seat}번은 선역이다.", f"{seat}번은 사신 편이다.",
                f"{seat}번은 일반 역할이다.", f"{seat}번은 특수 역할이다.",
                f"{seat}번은 밤에 행동한다.", f"{seat}번은 밤 행동이 없다.",
                f"{seat}번은 공격이 있다.", f"{seat}번은 보호가 있다.",
                f"{seat}번은 조사가 있다.", f"{seat}번은 공개가 있다.",
                f"{seat}번은 밤 공격을 버틴다.",
            ]
            candidates.append({"idx": tid, "text": texts[tid - 13], "target_uid": target["uid"], "is_valid": valid, "truth": truth})
        return candidates

    def make_relation_candidates() -> list[dict]:
        if len(other_survivors) < 2:
            return []
        pair = random.sample(other_survivors, 2)
        rx, ry = pair[0].get("role"), pair[1].get("role")
        if not rx or not ry:
            return []
        sx, sy = pair[0]["seat_number"], pair[1]["seat_number"]
        candidates = []
        for tid in range(24, 31):
            truth = _eval_relation_template(tid, rx, ry)
            if truth is None:
                continue
            valid = (truth == must_be_true)
            texts = [
                f"{sx}번과 {sy}번은 같은 편이다.",
                f"{sx}번과 {sy}번은 다른 편이다.",
                f"{sx}번과 {sy}번 중 한 명은 선역이다.",
                f"{sx}번과 {sy}번 중 한 명은 특수다.",
                f"{sx}번과 {sy}번 중 한 명만 특수다.",
                f"{sx}번과 {sy}번 중 한 명은 밤 행동이 있다.",
                f"{sx}번과 {sy}번 중 한 명만 밤 행동이 있다.",
            ]
            candidates.append({"idx": tid, "text": texts[tid - 24], "is_valid": valid, "truth": truth})
        return candidates

    def make_state_candidates() -> list[dict]:
        candidates = []
        for tid in range(31, 43):
            if tid in (31, 32, 33) and turn == 1:  # 첫 턴에는 밤 결과 없음
                continue
            if tid in (40, 41):  # 직전 추방자 관련 단서 제외
                continue
            truth = _eval_state_template(tid, game_state, my_role)
            if truth is None:
                continue
            valid = (truth == must_be_true)
            texts = [
                "지난밤 공격이 성공했다.", "지난밤 공격이 실패했다.",
                "지난밤 천사 수호가 맞았다.",
                "지금 조사 역할이 살아 있다.",
                "지금 공개 역할이 살아 있다.",
                "지금 보호 역할이 살아 있다.",
                "지금 공격 역할이 살아 있다.",
                "지금 일반 역할이 2명 이상이다.",
                "지금 특수 역할이 2명 이상이다.",
                "직전 추방은 선역이었다.",
                "직전 추방은 사신이었다.",
                "지금 선역 수가 더 많다.",
            ]
            candidates.append({"idx": tid, "text": texts[tid - 31], "is_valid": valid, "truth": truth})
        return candidates

    # 후보 풀 생성 (빠른 진행을 위해 핵심 정보문 4개만 제공)
    self_pool = make_self_candidates()
    target_pool = make_target_candidates()
    relation_pool = make_relation_candidates()
    state_pool = make_state_candidates()

    # valid 항목이 2개 이상 나오도록 시도
    def pick_n(pool, n, prefer_valid=True):
        valid = [c for c in pool if c["is_valid"]]
        invalid = [c for c in pool if not c["is_valid"]]
        result = []
        if prefer_valid:
            result += random.sample(valid, min(n, len(valid)))
            if len(result) < n:
                result += random.sample(invalid, min(n - len(result), len(invalid)))
        else:
            all_pool = pool[:]
            random.shuffle(all_pool)
            result = all_pool[:n]
        return result

    def extend_unique(dest: list[dict], items: list[dict], limit: int):
        seen = {c["idx"] for c in dest}
        for item in items:
            if item["idx"] in seen:
                continue
            dest.append(item)
            seen.add(item["idx"])
            if len(dest) >= limit:
                break

    core_candidates: list[dict] = []
    for pool in (self_pool, target_pool, relation_pool, state_pool):
        extend_unique(core_candidates, pick_n(pool, 1), 4)

    all_pool = self_pool + target_pool + relation_pool + state_pool
    extend_unique(core_candidates, pick_n(all_pool, 4 - len(core_candidates)), 4)

    # valid 개수가 2개 미만이면 전체 풀에서 추가
    valid_count = sum(1 for c in core_candidates if c["is_valid"])
    if valid_count < 2:
        extra_valid = [c for c in all_pool if c["is_valid"]]
        random.shuffle(extra_valid)
        boosted_candidates: list[dict] = []
        extend_unique(boosted_candidates, extra_valid[:2], 4)
        extend_unique(boosted_candidates, core_candidates, 4)
        core_candidates = boosted_candidates

    # 최대 4개로 제한
    core_candidates = core_candidates[:4]

    # 행동 선언문 4개 생성
    action_indices = random.sample(range(len(ACTION_TEMPLATES)), min(4, len(ACTION_TEMPLATES)))
    action_candidates = []
    for i in action_indices:
        text = _fill_action_template(ACTION_TEMPLATES[i], other_survivors)
        action_candidates.append({"idx": i, "text": text, "is_valid": True})

    return {
        "core_templates": core_candidates,
        "action_templates": action_candidates,
    }


def generate_bot_claim(
    my_uid: str,
    my_role: str,
    game_state: dict,
    survivors: list[dict],
    turn: int,
    bot_scores: dict,
) -> dict:
    """봇의 핵심 정보문 + 행동 선언문 자동 선택."""
    candidates = generate_candidates(my_uid, my_role, game_state, survivors, turn)
    core_pool = candidates["core_templates"]
    action_pool = candidates["action_templates"]

    # 유효한 후보 중에서 선택 (봇은 항상 유효한 것만 선택 가능)
    valid_core = [c for c in core_pool if c["is_valid"]]
    if not valid_core:
        valid_core = core_pool

    # claimValue 계산 (간단한 heuristic)
    def score_core(c):
        base = random.randint(-5, 5)
        # 자기 정보문은 보수적으로
        if c["idx"] <= 12:
            base -= 2
        # 선역 관련 주장에 점수 추가 (사신은 선역 지목 가능)
        return base

    valid_core.sort(key=score_core, reverse=True)
    chosen_core = valid_core[0]

    # 행동 선언문: grimScore 가장 높은 대상에 투표 선언
    top_target = None
    if bot_scores:
        alive_uids = [s["uid"] for s in survivors if s["uid"] != my_uid]
        if alive_uids:
            top_uid = max(alive_uids, key=lambda u: bot_scores.get(u, {}).get("grim_score", 50) + random.randint(-5, 5))
            top_target = next((s for s in survivors if s["uid"] == top_uid), None)

    # 행동 선언문 선택
    action = random.choice(action_pool)
    if top_target:
        seat = top_target["seat_number"]
        candidates_for_target = [c for c in action_pool if "{X}" in ACTION_TEMPLATES[c["idx"]]]
        if candidates_for_target:
            chosen_action_template = random.choice(candidates_for_target)
            text = ACTION_TEMPLATES[chosen_action_template["idx"]].replace("{X}", str(seat))
            other_seats = [str(s["seat_number"]) for s in survivors if s["uid"] not in (my_uid, top_target["uid"])]
            y_seat = random.choice(other_seats) if other_seats else str(seat)
            text = text.replace("{Y}", y_seat)
            action = {"idx": chosen_action_template["idx"], "text": text, "is_valid": True}

    return {
        "core_idx": chosen_core["idx"],
        "core_text": chosen_core["text"],
        "action_idx": action["idx"],
        "action_text": action["text"],
    }
