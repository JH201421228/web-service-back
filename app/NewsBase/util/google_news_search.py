"""
Google News 검색 결과 수집 모듈

- Google News RSS 피드를 이용하여 특정 키워드 검색 결과에서
  상위 N개의 뉴스 URL을 수집합니다.
- RSS 피드 URL 형식: https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko
"""

import json
import logging
from typing import Optional
from urllib.parse import quote, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

_GOOGLE_NEWS_RSS_SEARCH = (
    "https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
)
_GOOGLE_NEWS_ARTICLE_URL = "https://news.google.com/rss/articles/{article_id}"
_GOOGLE_NEWS_BATCH_EXECUTE_URL = (
    "https://news.google.com/_/DotsSplashUi/data/batchexecute"
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# 검색 키워드 매핑 (section_id로 사용할 고유 번호)
SEARCH_KEYWORDS = {
    "주식": 200,
    "비트코인": 201,
}


# ---------------------------------------------------------------------------
# Google News RSS → 실제 뉴스 URL 추출
# ---------------------------------------------------------------------------


def _resolve_google_news_url(google_url: str) -> Optional[str]:
    """
    Google News RSS의 중간 링크를 실제 뉴스 기사 URL로 변환합니다.
    """
    article_id = _extract_article_id(google_url)
    if not article_id:
        return google_url

    try:
        signature, timestamp = _fetch_decoding_params(article_id)
        return _decode_article_url(article_id, signature, timestamp)
    except Exception as e:
        logger.warning("Google News URL 디코딩 실패: %s → %s", google_url, e)
        return None


def _extract_article_id(google_url: str) -> Optional[str]:
    parsed = urlparse(google_url)
    path_parts = [part for part in parsed.path.split("/") if part]

    if parsed.hostname != "news.google.com":
        return None

    if len(path_parts) < 2 or path_parts[-2] not in {"articles", "read"}:
        return None

    return path_parts[-1]


def _fetch_decoding_params(article_id: str) -> tuple[str, str]:
    article_url = _GOOGLE_NEWS_ARTICLE_URL.format(article_id=article_id)
    resp = httpx.get(
        article_url,
        headers=_HEADERS,
        follow_redirects=True,
        timeout=15,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    node = soup.select_one("c-wiz > div[jscontroller]")
    if node is None:
        raise ValueError("Google News 디코딩 파라미터를 찾을 수 없습니다.")

    signature = node.get("data-n-a-sg")
    timestamp = node.get("data-n-a-ts")
    if not signature or not timestamp:
        raise ValueError("Google News 디코딩 파라미터가 비어 있습니다.")

    return signature, timestamp


def _decode_article_url(article_id: str, signature: str, timestamp: str) -> str:
    payload = [
        "Fbv4je",
        (
            f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",'
            f'null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,'
            f'null,0,0,null,0],"{article_id}",{timestamp},"{signature}"]'
        ),
    ]

    resp = httpx.post(
        _GOOGLE_NEWS_BATCH_EXECUTE_URL,
        headers={
            **_HEADERS,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        data=f"f.req={quote(json.dumps([[payload]]))}",
        timeout=15,
    )
    resp.raise_for_status()

    response_parts = resp.text.split("\n\n", 1)
    if len(response_parts) != 2:
        raise ValueError("Google News 디코딩 응답 형식이 올바르지 않습니다.")

    data = json.loads(response_parts[1])
    if not data:
        raise ValueError("Google News 디코딩 응답이 비어 있습니다.")

    decoded_payload = json.loads(data[0][2])
    decoded_url = decoded_payload[1]
    if not decoded_url or decoded_url.startswith("https://news.google.com/"):
        raise ValueError("실제 기사 URL을 추출하지 못했습니다.")

    return decoded_url


def fetch_google_news_urls(keyword: str, count: int = 5) -> list[dict]:
    """
    Google News RSS 피드에서 검색 키워드에 해당하는 뉴스를 수집합니다.

    Args:
        keyword : 검색 키워드 (예: "주식", "비트코인")
        count   : 가져올 기사 수 (기본값 5)

    Returns:
        [{"title": str, "url": str}, ...] 리스트 (최대 count개)

    Raises:
        ValueError : RSS 피드 요청 실패 또는 뉴스를 찾지 못한 경우
    """
    encoded_keyword = quote(keyword)
    rss_url = _GOOGLE_NEWS_RSS_SEARCH.format(keyword=encoded_keyword)

    try:
        resp = httpx.get(rss_url, headers=_HEADERS, follow_redirects=True, timeout=15)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise ValueError(
            f"Google News RSS를 불러올 수 없습니다 (keyword={keyword}): {e}"
        ) from e

    soup = BeautifulSoup(resp.text, "xml")
    items = soup.find_all("item")

    if not items:
        raise ValueError(
            f"Google News 검색 결과를 찾을 수 없습니다. (keyword={keyword})"
        )

    results: list[dict] = []
    for item in items:
        title_tag = item.find("title")
        link_tag = item.find("link")

        if not title_tag or not link_tag:
            continue

        title = title_tag.get_text(strip=True)
        google_link = link_tag.get_text(strip=True)

        # Google News 리다이렉트 URL → 실제 URL
        actual_url = _resolve_google_news_url(google_link)
        if actual_url:
            results.append({"title": title, "url": actual_url})

        if len(results) >= count:
            break

    if not results:
        raise ValueError(
            f"Google News에서 유효한 뉴스 URL을 수집할 수 없습니다. (keyword={keyword})"
        )

    logger.info(
        "Google News 검색 '%s' — %d개 URL 수집 완료", keyword, len(results)
    )
    return results


# ---------------------------------------------------------------------------
# 직접 실행 시 테스트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    kw = sys.argv[1] if len(sys.argv) > 1 else "주식"
    cnt = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print(f"\n🔍 Google News 검색: [{kw}] 상위 {cnt}개\n")

    try:
        news_items = fetch_google_news_urls(keyword=kw, count=cnt)
        for i, item in enumerate(news_items, start=1):
            print(f"  {i}. {item['title']}")
            print(f"     {item['url']}\n")
    except ValueError as e:
        print(f"❌ 오류: {e}")
