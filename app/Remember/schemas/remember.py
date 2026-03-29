from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DisciplineCode = Literal["numbers", "cards"]
DifficultyCode = Literal["easy", "medium", "hard", "pro", "elite"]


class RememberAttemptCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    deviceId: str = Field(min_length=1, max_length=128)
    nickname: str = Field(default="Memory Runner", min_length=1, max_length=60)
    discipline: DisciplineCode
    difficultyId: DifficultyCode
    difficultyLabel: str | None = Field(default=None, max_length=60)
    durationMs: int = Field(ge=0)
    accuracy: int = Field(ge=0, le=100)
    totalItems: int = Field(gt=0)
    correctItems: int = Field(ge=0)
    summary: str | None = Field(default=None, max_length=255)
    achievedAt: datetime | None = None

    @model_validator(mode="after")
    def validate_record(self) -> "RememberAttemptCreateRequest":
        if self.correctItems > self.totalItems:
            raise ValueError("correctItems cannot be greater than totalItems.")
        return self


class RememberAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    deviceId: str
    nickname: str
    discipline: DisciplineCode
    difficultyId: DifficultyCode
    difficultyLabel: str
    durationMs: int
    accuracy: int
    totalItems: int
    correctItems: int
    summary: str | None = None
    achievedAt: str
    createdAt: str


class RememberLeaderboardEntryResponse(BaseModel):
    id: str
    nickname: str
    discipline: DisciplineCode
    difficultyId: DifficultyCode
    difficultyLabel: str
    durationMs: int
    accuracy: int
    achievedAt: str
    descriptor: str
    laneLabel: str


class RememberTodayLeaderboardResponse(BaseModel):
    source: Literal["remote"] = "remote"
    updatedAt: str
    entries: list[RememberLeaderboardEntryResponse]


class RememberDeleteResponse(BaseModel):
    deleted: bool = True
    id: str
