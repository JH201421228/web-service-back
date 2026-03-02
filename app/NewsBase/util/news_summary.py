"""
뉴스 요약 & 퀴즈 생성 모듈

- 뉴스 URL을 받아 본문을 크롤링
- OpenAI GPT로 요약 & 4지선다 퀴즈 생성
- 사실 기반 요약만 포함 (추론/의견 제외)
"""

import os
import json
import re
import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """OpenAI 클라이언트 싱글턴 반환"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        _client = OpenAI(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# 뉴스 크롤링
# ---------------------------------------------------------------------------

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_news_content(url: str) -> dict[str, str]:
    """
    뉴스 URL에서 제목과 본문을 추출합니다.

    Returns:
        {"title": str, "content": str}
    """
    try:
        resp = httpx.get(url, headers=_HEADERS, follow_redirects=True, timeout=15)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise ValueError(f"뉴스 페이지를 불러올 수 없습니다: {e}") from e

    soup = BeautifulSoup(resp.text, "html.parser")

    # ── 제목 추출 ──────────────────────────────────────────────────
    title = ""
    # 네이버 뉴스
    for sel in [
        "h2#title_area span",
        "h2.media_end_head_headline",
        ".media_end_head_headline",
        "h1.news_title",
        "h1",
    ]:
        tag = soup.select_one(sel)
        if tag:
            title = tag.get_text(strip=True)
            break

    if not title:
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"].strip() if og_title else "제목 없음"

    # ── 본문 추출 ──────────────────────────────────────────────────
    content = ""
    # 네이버 뉴스 본문
    for sel in [
        "#dic_area",
        "#articleBodyContents",
        ".news_end_body_container",
        "article",
        ".article-body",
        ".article_body",
    ]:
        tag = soup.select_one(sel)
        if tag:
            # 광고·스크립트 제거
            for unwanted in tag.select("script, style, .ad, .advertisement, figure"):
                unwanted.decompose()
            content = tag.get_text(separator="\n", strip=True)
            break

    if not content:
        # fallback: <p> 태그 본문
        paragraphs = soup.find_all("p")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40)

    if not content:
        raise ValueError("뉴스 본문을 추출할 수 없습니다. URL을 확인해 주세요.")

    logger.debug("크롤링 완료 | URL=%s | title=%s | content_len=%d", url, title, len(content))
    return {"title": title, "content": content}


# ---------------------------------------------------------------------------
# GPT 요약 + 퀴즈 생성
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """당신은 뉴스 분석 전문가입니다.
주어진 뉴스 원문을 바탕으로 다음 두 가지를 JSON 형식으로 반드시 출력해야 합니다.

[규칙]
1. 제목(title)과 요약(summary)은 반드시 원문에 명시된 사실만 포함합니다. 추론, 의견, 평가는 절대 포함하지 마세요.
2. 제목은 사실만을 포함합니다.
3. 요약은 3~5문장의 한국어로 작성합니다.
4. 퀴즈(quiz)는 뉴스 내용을 바탕으로 4지선다형 질문 1개를 만듭니다.
5. 질문들은 질문 번호 없이 내용만을 포함합니다.
6. 정답은 반드시 뉴스 원문에서 확인 가능한 사실이어야 합니다.
7. 오답 보기는 그럴듯하지만 틀린 내용으로 구성합니다.

[출력 형식 - 반드시 아래 JSON만 출력, 다른 텍스트 금지]
{
  "title": "뉴스 제목",
  "summary": "요약 내용",
  "quiz": {
    "question": "질문",
    "options": ["보기1", "보기2", "보기3", "보기4"],
    "answer_index": 0,
    "explanation": "정답 이유 (원문 근거)"
  }
}
answer_index는 options 배열에서 정답의 0-based 인덱스입니다."""


def summarize_and_quiz(title: str, content: str) -> dict:
    """
    뉴스 제목 + 본문을 GPT에 전달하여 요약과 4지선다 퀴즈를 생성합니다.

    Returns:
        {
            "title": str,
            "summary": str,
            "quiz": {
                "question": str,
                "options": list[str],   # 4개
                "answer_index": int,    # 0-based
                "explanation": str
            }
        }
    """
    client = _get_client()

    user_message = f"""[뉴스 제목]
{title}

[뉴스 본문]
{content[:4000]}"""  # 토큰 절약을 위해 본문 최대 4000자

    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise RuntimeError(f"OpenAI API 호출 실패: {e}") from e

    raw = response.choices[0].message.content
    logger.debug("GPT 응답: %s", raw)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"GPT 응답 파싱 실패: {e}\n원본: {raw}") from e

    # 필수 필드 검증
    _validate_result(parsed)

    parsed["title"] = title
    return parsed


def _validate_result(data: dict) -> None:
    """GPT 응답이 필요한 구조를 갖추고 있는지 검증"""
    if "title" not in data:
        raise ValueError("GPT 응답에 'title' 필드가 없습니다.")
    if "summary" not in data:
        raise ValueError("GPT 응답에 'summary' 필드가 없습니다.")
    if "quiz" not in data:
        raise ValueError("GPT 응답에 'quiz' 필드가 없습니다.")

    quiz = data["quiz"]
    required_quiz_fields = ["question", "options", "answer_index", "explanation"]
    for field in required_quiz_fields:
        if field not in quiz:
            raise ValueError(f"quiz 필드에 '{field}'가 없습니다.")

    # save_json = {
    #     "title": data["title"],
    #     "summary": data["summary"],
    #     "quiz": data["quiz"]
    # }

    # with open("test.json", "w", encoding="utf-8") as f:
    #     json.dump(save_json, f, ensure_ascii=False, indent=2)

    if not isinstance(quiz["options"], list) or len(quiz["options"]) != 4:
        raise ValueError("quiz.options는 반드시 4개의 항목을 가진 리스트여야 합니다.")

    if not isinstance(quiz["answer_index"], int) or not (0 <= quiz["answer_index"] <= 3):
        raise ValueError("quiz.answer_index는 0~3 사이의 정수여야 합니다.")


# ---------------------------------------------------------------------------
# 통합 진입점
# ---------------------------------------------------------------------------

def process_news_url(url: str) -> dict:
    """
    뉴스 URL 하나를 받아 요약 + 퀴즈를 반환하는 메인 함수.

    Returns:
        {
            "title": str,
            "summary": str,
            "quiz": {
                "question": str,
                "options": list[str],
                "answer_index": int,
                "explanation": str
            }
        }
    """
    # 1. 크롤링
    news = fetch_news_content(url)

    # 2. GPT 요약 + 퀴즈
    result = summarize_and_quiz(news["title"], news["content"])

    return result


# ---------------------------------------------------------------------------
# 직접 실행 시 테스트
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    test_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://n.news.naver.com/mnews/article/422/0000839432"
    )

    print(f"\n📰 뉴스 URL: {test_url}\n")
    result = process_news_url(test_url)

    print(f"📌 제목: {result['title']}\n")
    print(f"📝 요약:\n{result['summary']}\n")
    print("❓ 퀴즈:")
    print(f"  Q. {result['quiz']['question']}")
    for i, opt in enumerate(result['quiz']['options']):
        marker = "✅" if i == result['quiz']['answer_index'] else "  "
        print(f"  {marker} {i + 1}. {opt}")
    print(f"\n💡 해설: {result['quiz']['explanation']}")