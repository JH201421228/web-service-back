"""
네이버 뉴스 헤드라인 URL 수집 모듈

- https://news.naver.com/section/{sid} 페이지에서
  헤드라인 뉴스 링크를 순서대로 최대 N개 반환합니다.
- 기본 섹션: 100 (정치)
"""

import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

_BASE_SECTION_URL = "https://news.naver.com/section/{sid}"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://news.naver.com/",
}

# 섹션 ID 매핑
SECTION_IDS = {
    "정치": 100,
    "경제": 101,
    "사회": 102,
    "생활/문화": 103,
    "세계": 104,
    "IT/과학": 105,
}


# ---------------------------------------------------------------------------
# 헤드라인 URL 수집
# ---------------------------------------------------------------------------


def fetch_headline_urls(sid: int = 100, count: int = 5) -> list[str]:
    """
    네이버 뉴스 특정 섹션에서 헤드라인 뉴스 URL을 순서대로 반환합니다.

    Args:
        sid   : 섹션 ID (기본값 100 = 정치)
        count : 가져올 기사 수 (기본값 5)

    Returns:
        헤드라인 뉴스 URL 리스트 (최대 count개)

    Raises:
        ValueError : 페이지 요청 실패 또는 헤드라인 링크를 찾지 못한 경우
    """
    url = _BASE_SECTION_URL.format(sid=sid)

    try:
        resp = httpx.get(url, headers=_HEADERS, follow_redirects=True, timeout=15)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise ValueError(f"섹션 페이지를 불러올 수 없습니다 (sid={sid}): {e}") from e

    soup = BeautifulSoup(resp.text, "html.parser")

    # 헤드라인 기사 컨테이너: div.sa_item._SECTION_HEADLINE
    # 각 컨테이너 안의 a.sa_text_title 에 기사 URL이 있음
    urls: list[str] = []

    # 1순위: 헤드라인 전용 클래스에서 추출
    headline_links = soup.select(".sa_item._SECTION_HEADLINE .sa_text_title")

    # 2순위 (fallback): 헤드라인 클래스가 없을 경우 일반 기사 링크에서 추출
    if not headline_links:
        logger.warning("헤드라인 전용 셀렉터로 링크를 찾지 못했습니다. 일반 셀렉터를 사용합니다.")
        headline_links = soup.select(".sa_text_title")

    for a_tag in headline_links:
        href: Optional[str] = a_tag.get("href")
        if href and href.startswith("http") and href not in urls:
            urls.append(href)
        if len(urls) >= count:
            break

    if not urls:
        raise ValueError(
            f"헤드라인 뉴스 링크를 찾을 수 없습니다. "
            f"네이버 뉴스 HTML 구조가 변경되었을 수 있습니다. (sid={sid})"
        )

    logger.debug("헤드라인 URL %d개 수집 완료 (sid=%d)", len(urls), sid)
    return urls


# ---------------------------------------------------------------------------
# 직접 실행 시 테스트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    sid = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    section_name = next((k for k, v in SECTION_IDS.items() if v == sid), str(sid))
    print(f"\n📰 네이버 뉴스 [{section_name}] 헤드라인 상위 {count}개\n")

    try:
        headline_urls = fetch_headline_urls(sid=sid, count=count)
        for i, u in enumerate(headline_urls, start=1):
            print(f"  {i}. {u}")
    except ValueError as e:
        print(f"❌ 오류: {e}")
