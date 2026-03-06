"""
뉴스 API 라우터

GET /api/news/list?section_id=100&date=2026-03-04&when=0
  - Response: List[NewsResponse]
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.NewsBase.core.deps import get_db
from app.NewsBase.schemas.news import NewsResponse
from app.NewsBase.services.news import get_news_list, count_date_news

router = APIRouter(prefix="/news", tags=["News"])


@router.get(
    "/list",
    response_model=List[NewsResponse],
    summary="뉴스 목록 조회",
    description=(
        "섹션 ID, 날짜, 오전/오후 구분으로 저장된 뉴스 목록을 반환합니다.\n\n"
        "- `section_id`: 네이버 뉴스 섹션 (100=정치, 101=경제, 102=사회, 103=생활문화, 104=세계, 105=IT과학)\n"
        "- `date`: 조회 날짜 (YYYY-MM-DD)\n"
        "- `when`: 0=오전, 1=오후"
    ),
)
def list_news(
    section_id: int = Query(..., description="섹션 ID (예: 100)"),
    date: str = Query(..., description="날짜 (YYYY-MM-DD)"),
    when: int = Query(..., ge=0, le=1, description="0=오전, 1=오후"),
    db: Session = Depends(get_db),
) -> List[NewsResponse]:
    try:
        return get_news_list(db=db, section_id=section_id, date=date, when=when)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 목록 조회 중 오류가 발생했습니다: {e}",
        )

@router.get(
    "/count",
    response_model=int,
    summary="뉴스 개수 조회",
    description=(
        "날짜 기준으로 저장된 뉴스 개수를 반환합니다.\n\n"
        "- `date`: 조회 날짜 (YYYY-MM-DD)\n"
        "- `when`: 0=오전, 1=오후"
    ),
)
def count_news(
    date: str = Query(..., description="날짜 (YYYY-MM-DD)"),
    when: int = Query(..., ge=0, le=1, description="0=오전, 1=오후"),
    db: Session = Depends(get_db),
) -> int:
    try:
        return count_date_news(db=db, date=date, when=when)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 개수 조회 중 오류가 발생했습니다: {e}",
        )
