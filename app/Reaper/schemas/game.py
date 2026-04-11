from pydantic import BaseModel


class VoteRequest(BaseModel):
    target_uid: str


class NightActionRequest(BaseModel):
    target_uid: str
