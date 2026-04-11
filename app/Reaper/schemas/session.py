from pydantic import BaseModel


class SoloStartResponse(BaseModel):
    game_id: str
    uid: str
    nickname: str
    hashtag: str
    is_guest: bool
    avatar_seed: str
