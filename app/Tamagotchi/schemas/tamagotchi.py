from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

StarterId = Literal["sproutling", "droplet", "sparko"]
AppLanguage = Literal["ko", "en"]
HealthSource = Literal["health-connect", "mock"]


class TamagotchiDailyHealthSnapshot(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    date: date
    steps: int = Field(ge=0)
    sleepHours: float = Field(ge=0)
    avgHeartRate: int = Field(ge=0)
    calories: int = Field(ge=0)
    activeMinutes: int = Field(ge=0)
    source: HealthSource


class TamagotchiDailyHistoryEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    date: date
    health: TamagotchiDailyHealthSnapshot
    score: int = Field(ge=0)
    expGained: int = Field(ge=0)
    coinsGained: int = Field(ge=0)
    totalExp: int = Field(ge=0)
    stage: int = Field(ge=1, le=10)

    @model_validator(mode="after")
    def validate_entry(self) -> "TamagotchiDailyHistoryEntry":
        if self.health.date != self.date:
            raise ValueError("health.date must match date.")
        return self


class TamagotchiPlayerSyncRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    installId: str = Field(min_length=1, max_length=128)
    language: AppLanguage
    nickname: str = Field(min_length=1, max_length=60)
    petName: str = Field(min_length=1, max_length=60)
    selectedStarter: StarterId
    exp: int = Field(ge=0)
    coins: int = Field(ge=0)
    mood: int = Field(ge=0, le=100)
    energy: int = Field(ge=0, le=100)
    cleanliness: int = Field(ge=0, le=100)
    bond: int = Field(ge=0, le=100)
    streak: int = Field(ge=0)
    lastSyncDate: date | None = None
    lastHealthSource: HealthSource | None = None
    dailyHistory: list[TamagotchiDailyHistoryEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_daily_history(self) -> "TamagotchiPlayerSyncRequest":
        unique_dates = {entry.date for entry in self.dailyHistory}
        if len(unique_dates) != len(self.dailyHistory):
            raise ValueError("dailyHistory contains duplicate dates.")
        return self


class TamagotchiPlayerSnapshotResponse(TamagotchiPlayerSyncRequest):
    source: Literal["remote"] = "remote"
    updatedAt: datetime


class TamagotchiLeaderboardSubmitRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    date: date
    installId: str = Field(min_length=1, max_length=128)
    nickname: str = Field(min_length=1, max_length=60)
    petName: str = Field(min_length=1, max_length=60)
    starter: StarterId
    score: int = Field(ge=0)
    streak: int = Field(ge=0)
    stage: int = Field(ge=1, le=10)
    totalExp: int = Field(ge=0)


class TamagotchiLeaderboardEntryResponse(BaseModel):
    installId: str
    nickname: str
    petName: str
    starter: StarterId
    score: int
    streak: int
    stage: int
    totalExp: int
    rank: int
    isSelf: bool = False


class TamagotchiDailyLeaderboardResponse(BaseModel):
    source: Literal["remote"] = "remote"
    date: date
    updatedAt: datetime
    top: list[TamagotchiLeaderboardEntryResponse]
    self: TamagotchiLeaderboardEntryResponse | None = None
