import json
import re
import xml.etree.ElementTree as ET
from typing import Any
from unicodedata import normalize as unicode_normalize

import requests

from app.Tourist.core.config import PUBLIC_DATA_TIMEOUT_SECONDS


class PublicDataFetchError(RuntimeError):
    pass


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicode_normalize("NFKC", str(value)).strip().lower()
    return re.sub(r"[\s,·ㆍ\-_()/\\\[\]{}'\".:]", "", text)


def normalize_code(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    return text if len(text) == 2 else None


def pick_first(record: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() not in {"none", "null"}:
            return text
    return None


def shorten_text(value: str | None, limit: int = 120) -> str | None:
    if not value:
        return None
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}…"


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def load_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if item]


def _request(url: str, params: dict[str, Any]) -> Any:
    response = requests.get(url, params=params, timeout=PUBLIC_DATA_TIMEOUT_SECONDS)
    response.raise_for_status()
    text = response.text.strip()

    if text.startswith("<"):
        return _parse_xml_payload(text)

    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise PublicDataFetchError(f"Unsupported response format from {url}") from exc


def post_form_json(
    url: str,
    *,
    data: dict[str, Any],
    session: requests.Session | None = None,
) -> Any:
    client = session or requests
    response = client.post(url, data=data, timeout=PUBLIC_DATA_TIMEOUT_SECONDS)
    response.raise_for_status()
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise PublicDataFetchError(f"Unsupported JSON response format from {url}") from exc


def _parse_xml_payload(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text)
    rows: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        rows.append(
            {
                child.tag: (child.text or "").strip()
                for child in item
                if child.tag
            }
        )

    total_count_text = root.findtext(".//totalCount")
    total_count = int(total_count_text) if total_count_text and total_count_text.isdigit() else None

    return {
        "rows": rows,
        "totalCount": total_count,
    }


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return payload["rows"]

    if isinstance(payload, dict):
        for candidate in (
            payload.get("data"),
            payload.get("items"),
            payload.get("item"),
            payload.get("results"),
        ):
            if isinstance(candidate, list):
                return candidate
            if isinstance(candidate, dict):
                if isinstance(candidate.get("item"), list):
                    return candidate["item"]
                if isinstance(candidate.get("item"), dict):
                    return [candidate["item"]]

        response = payload.get("response")
        if isinstance(response, dict):
            body = response.get("body", response)
            items = body.get("items", body.get("item"))
            if isinstance(items, dict):
                item = items.get("item", items)
                if isinstance(item, list):
                    return item
                if isinstance(item, dict):
                    return [item]
            if isinstance(items, list):
                return items

    return []


def _extract_total_count(payload: Any) -> int | None:
    if isinstance(payload, dict):
        for key in ("totalCount", "total_count"):
            value = payload.get(key)
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)

        response = payload.get("response")
        if isinstance(response, dict):
            body = response.get("body", response)
            for key in ("totalCount", "total_count"):
                value = body.get(key)
                if isinstance(value, int):
                    return value
                if isinstance(value, str) and value.isdigit():
                    return int(value)

    return None


def fetch_paginated_rows(
    url: str,
    *,
    service_key: str,
    page_param: str,
    per_page_param: str,
    page_size: int = 200,
    extra_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = 1

    while True:
        params = {
            "serviceKey": service_key,
            page_param: page,
            per_page_param: page_size,
        }
        if extra_params:
            params.update(extra_params)

        payload = _request(url, params)
        page_rows = _extract_rows(payload)
        if not page_rows:
            break

        rows.extend(page_rows)
        total_count = _extract_total_count(payload)
        if total_count is not None and len(rows) >= total_count:
            break
        if len(page_rows) < page_size:
            break
        page += 1

    return rows
