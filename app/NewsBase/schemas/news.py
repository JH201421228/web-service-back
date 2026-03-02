from pydantic import BaseModel, HttpUrl, field_validator
from typing import List


class NewsSummaryRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("url은 비어 있을 수 없습니다.")
        if not v.startswith("http"):
            raise ValueError("유효한 URL을 입력해 주세요.")
        return v


class QuizSchema(BaseModel):
    question: str
    options: List[str]       # 4개
    answer_index: int        # 0-based
    explanation: str


class NewsSummaryResponse(BaseModel):
    title: str
    summary: str
    quiz: QuizSchema
