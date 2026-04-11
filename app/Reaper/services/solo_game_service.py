"""
솔로 게임 세션 생성 서비스.
"""
import logging
import random
import uuid

from sqlalchemy.orm import Session

from app.Reaper.models.game import ReaperGame, ReaperPlayer

logger = logging.getLogger(__name__)

ADJECTIVES = [
    "신비로운", "날카로운", "조용한", "빠른", "어두운", "차가운", "뜨거운",
    "번뜩이는", "수상한", "침착한", "냉철한", "교활한", "용감한", "예리한",
    "잠잠한", "흔들리지않는", "집요한", "영리한", "무자비한", "신중한",
]

NOUNS = [
    "사신", "탐정", "천사", "조사관", "관찰자", "추리꾼", "증인", "목격자",
    "밀정", "심판자", "결정자", "방랑자", "침입자", "수호자", "감시자",
    "예언자", "해석자", "추적자", "분석가", "연구자",
]

BOT_NAMES = [
    "어둠속의루시퍼", "침묵의아자젤", "냉정한카론", "그림자의타나토스",
    "교활한벨페고르", "수수께끼의오시리스", "비밀의아누비스", "어둠의페르세포네",
    "차가운하데스", "신비의에레보스", "침착한네메시스", "예리한테미스",
    "공정한아스트라이아", "날카로운모이라이", "집요한에리니에스",
]


def generate_random_nickname() -> tuple[str, str]:
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    hashtag = str(random.randint(1000, 9999))
    return f"{adjective}{noun}", hashtag


def generate_bot_nickname() -> tuple[str, str]:
    name = random.choice(BOT_NAMES)
    hashtag = str(random.randint(1000, 9999))
    return name, hashtag


def create_solo_game(uid: str, nickname: str, hashtag: str, db: Session, bot_count: int = 5) -> ReaperGame:
    game_id = str(uuid.uuid4())[:8].upper()
    game = ReaperGame(
        id=game_id,
        title="솔로 모드",
        creator_uid=uid,
        status="waiting",
        player_capacity=bot_count + 1,
        bot_total=bot_count,
    )
    db.add(game)

    db.add(ReaperPlayer(
        game_id=game_id,
        uid=uid,
        nickname=nickname,
        hashtag=hashtag,
        is_bot=False,
        seat_number=1,
    ))

    for index in range(bot_count):
        bot_uid = f"bot_{game_id}_{index + 1}"
        bot_nickname, bot_hashtag = generate_bot_nickname()
        db.add(ReaperPlayer(
            game_id=game_id,
            uid=bot_uid,
            nickname=bot_nickname,
            hashtag=bot_hashtag,
            is_bot=True,
            seat_number=index + 2,
        ))

    db.commit()
    logger.info("[SoloGame] Created %s for %s", game_id, uid)
    return game
