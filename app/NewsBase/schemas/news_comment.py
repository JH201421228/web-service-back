from pydantic import BaseModel, Field, field_validator


class NewsCommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("댓글 내용은 비어 있을 수 없습니다.")
        return content


class NewsCommentResponse(BaseModel):
    comment_id: int
    news_id: int
    content: str
    created_at: str

    class Config:
        from_attributes = True
