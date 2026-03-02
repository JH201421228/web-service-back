"""
뉴스 요약 + 퀴즈 API 라우터

POST /api/news/summary
  - Body: { "url": "https://..." }
  - Response: { "title", "summary", "quiz": { "question", "options", "answer_index", "explanation" } }
"""

from fastapi import APIRouter, HTTPException, status

from app.NewsBase.schemas.news import NewsSummaryRequest, NewsSummaryResponse
from app.NewsBase.services.news import get_news_summary

router = APIRouter(prefix="/news", tags=["News"])


@router.post(
    "/summary",
    response_model=NewsSummaryResponse,
    summary="뉴스 요약 & 4지선다 퀴즈 생성",
    description=(
        "뉴스 URL을 전달하면 사실 기반 요약과 4지선다형 퀴즈를 반환합니다.\n\n"
        "- `title`: 뉴스 제목\n"
        "- `summary`: 사실만 담은 3~5문장 요약\n"
        "- `quiz.question`: 퀴즈 질문\n"
        "- `quiz.options`: 보기 4개 리스트\n"
        "- `quiz.answer_index`: 정답 보기의 0-based 인덱스\n"
        "- `quiz.explanation`: 정답 해설 (원문 근거)"
    ),
)
async def summarize_news(body: NewsSummaryRequest) -> NewsSummaryResponse:
    try:
        return get_news_summary(body.url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예상치 못한 오류가 발생했습니다: {e}",
        )
