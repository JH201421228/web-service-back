from pydantic import BaseModel
from typing import List, Optional


class QuizSchema(BaseModel):
    question: str
    options: List[str]
    answer_index: int
    explanation: str


class NewsResponse(BaseModel):
    nid: int
    section_id: Optional[int]
    title: Optional[str]
    summary: Optional[str]
    comment_count: int = 0
    quiz: QuizSchema
    when: int
    url: Optional[str]
    date: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
