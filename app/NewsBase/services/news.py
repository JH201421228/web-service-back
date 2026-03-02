"""
뉴스 요약 서비스 레이어

lib/news_summary.py 의 핵심 로직을 감싸는 서비스 함수 모음.
라우터 → 서비스 → lib 순서로 호출됩니다.
"""

from app.NewsBase.util.news_summary import process_news_url
from app.NewsBase.schemas.news import NewsSummaryResponse, QuizSchema


def get_news_summary(url: str) -> NewsSummaryResponse:
    """
    뉴스 URL을 받아 요약 + 4지선다 퀴즈를 반환합니다.

    Raises:
        ValueError: URL 접근 불가 또는 본문 추출 실패
        RuntimeError: OpenAI API 오류
    """
    result = process_news_url(url)

    return NewsSummaryResponse(
        title=result["title"],
        summary=result["summary"],
        quiz=QuizSchema(
            question=result["quiz"]["question"],
            options=result["quiz"]["options"],
            answer_index=result["quiz"]["answer_index"],
            explanation=result["quiz"]["explanation"],
        ),
    )
