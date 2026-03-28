from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests
from babel import Locale
from sqlalchemy.orm import Session

from app.Tourist.core.config import (
    KTO_DATALAB_DATE_INIT_ENDPOINT,
    KTO_DATALAB_GRID_ENDPOINT,
    KTO_DATALAB_MENU_CODE,
    KTO_DATALAB_MENU_GROUP,
    KTO_TOURISM_GENDER_QID,
    QUARANTINE_REGION_ENDPOINT,
    QUARANTINE_REGION_SERVICE_KEY,
    TRAVEL_BAN_ENDPOINT,
    TRAVEL_BAN_SERVICE_KEY,
    TRAVEL_WARNING_ENDPOINTS,
    TRAVEL_WARNING_SERVICE_KEY,
    VACCINATION_REFERENCE_ENDPOINT,
    VACCINATION_SERVICE_KEY,
)
from app.Tourist.models.country_mapping import TouristCountryMapping
from app.Tourist.models.country_snapshot import TouristCountrySnapshot
from app.Tourist.models.data_source import TouristDataSource
from app.Tourist.models.monthly_statistic import TouristMonthlyStatistic
from app.Tourist.models.vaccination_reference import TouristVaccinationReference
from app.Tourist.services.catalog import (
    CURRENT_SOURCE_KEYS,
    MANUAL_COUNTRY_CODE_ALIASES,
    NON_COUNTRY_TERRITORY_CODES,
    SOURCE_DEFINITIONS,
)
from app.Tourist.services.public_data import (
    dump_json,
    fetch_paginated_rows,
    load_json_list,
    normalize_code,
    normalize_text,
    pick_first,
    post_form_json,
)


def sync_tourist_data(
    db: Session,
    *,
    include_statistics: bool = False,
    force_statistics: bool = False,
) -> None:
    _prune_obsolete_sources(db)
    _upsert_manual_source(db)

    warning_rows = _fetch_source_rows(
        db=db,
        source_key="travel_warning",
        fetcher=_fetch_travel_warning_rows,
        raise_on_error=False,
    )
    ban_rows = _fetch_source_rows(
        db=db,
        source_key="travel_ban",
        fetcher=_fetch_travel_ban_rows,
        raise_on_error=False,
    )
    vaccination_rows = _fetch_source_rows(
        db=db,
        source_key="vaccination_reference",
        fetcher=_fetch_vaccination_reference_rows,
        raise_on_error=False,
    )
    quarantine_rows = _fetch_source_rows(
        db=db,
        source_key="quarantine_region",
        fetcher=_fetch_quarantine_rows,
        raise_on_error=False,
    )

    country_map, name_lookup = _build_country_map_from_db(db)
    if warning_rows:
        _apply_warning_seed_rows(country_map, name_lookup, warning_rows)
        _apply_travel_warning_rows(country_map, name_lookup, warning_rows)
    if ban_rows:
        _apply_travel_ban_rows(country_map, name_lookup, ban_rows)
    if quarantine_rows:
        _apply_quarantine_rows(country_map, name_lookup, quarantine_rows)

    if not country_map:
        raise ValueError("국가 기준 데이터를 가져오지 못했습니다.")

    _persist_country_snapshots(
        db,
        country_map,
        prune_stale=bool(warning_rows),
    )
    _persist_country_mappings(db, country_map)

    if vaccination_rows:
        _persist_vaccination_references(db, vaccination_rows)

    if include_statistics or force_statistics or _should_refresh_statistics(db):
        statistic_rows = _fetch_source_rows(
            db=db,
            source_key="tourism_statistics",
            fetcher=_fetch_tourism_statistics_rows,
            raise_on_error=False,
        )
        if statistic_rows:
            _persist_tourism_statistics(db, statistic_rows)

    db.commit()


def _fetch_source_rows(
    *,
    db: Session,
    source_key: str,
    fetcher,
    raise_on_error: bool = True,
) -> list[dict[str, Any]]:
    try:
        rows = fetcher()
    except Exception as exc:
        _upsert_data_source(
            db=db,
            source_key=source_key,
            status="failed",
            item_count=0,
            last_error=str(exc),
        )
        db.commit()
        if raise_on_error:
            raise
        return []

    _upsert_data_source(
        db=db,
        source_key=source_key,
        status="success",
        item_count=len(rows),
        last_error=None,
    )
    db.commit()
    return rows


def _fetch_travel_warning_rows() -> list[dict[str, Any]]:
    last_error: Exception | None = None
    attempts = (("page", "perPage"), ("pageNo", "numOfRows"))

    for endpoint in TRAVEL_WARNING_ENDPOINTS:
        for page_param, per_page_param in attempts:
            try:
                rows = fetch_paginated_rows(
                    endpoint,
                    service_key=TRAVEL_WARNING_SERVICE_KEY,
                    page_param=page_param,
                    per_page_param=per_page_param,
                    extra_params={"returnType": "JSON"},
                )
                if rows:
                    return rows
            except Exception as exc:
                last_error = exc

    if last_error is not None:
        raise last_error
    return []


def _fetch_travel_ban_rows() -> list[dict[str, Any]]:
    return fetch_paginated_rows(
        TRAVEL_BAN_ENDPOINT,
        service_key=TRAVEL_BAN_SERVICE_KEY,
        page_param="pageNo",
        per_page_param="numOfRows",
    )


def _fetch_vaccination_reference_rows() -> list[dict[str, Any]]:
    return fetch_paginated_rows(
        VACCINATION_REFERENCE_ENDPOINT,
        service_key=VACCINATION_SERVICE_KEY,
        page_param="pageNo",
        per_page_param="numOfRows",
    )


def _fetch_quarantine_rows() -> list[dict[str, Any]]:
    return fetch_paginated_rows(
        QUARANTINE_REGION_ENDPOINT,
        service_key=QUARANTINE_REGION_SERVICE_KEY,
        page_param="page",
        per_page_param="perPage",
        page_size=1000,
    )


def _fetch_tourism_statistics_rows() -> list[dict[str, Any]]:
    session = requests.Session()
    init_payload = post_form_json(
        KTO_DATALAB_DATE_INIT_ENDPOINT,
        data={
            "menuGrpCd": KTO_DATALAB_MENU_GROUP,
            "menuCd": KTO_DATALAB_MENU_CODE,
        },
        session=session,
    )
    monthly = next(
        item for item in init_payload.get("list", []) if str(item.get("cyclDiv")) == "1"
    )
    start_ym = str(monthly["bgngDteVal"])
    end_ym = str(monthly["endDteVal"])
    grid_payload = post_form_json(
        KTO_DATALAB_GRID_ENDPOINT,
        data={
            "adminYn": "N",
            "BASE_YM1": start_ym,
            "BASE_YM2": end_ym,
            "srchBgngYear": start_ym[:4],
            "srchEndYear": end_ym[:4],
            "srchBgngMm": start_ym[4:6],
            "srchEndMm": end_ym[4:6],
            "srchAreaDate": "1",
            "qid": KTO_TOURISM_GENDER_QID,
        },
        session=session,
    )
    return grid_payload.get("list", [])


def _build_country_map_from_db(
    db: Session,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    country_map, name_lookup = _build_country_seed_catalog()

    for snapshot in db.query(TouristCountrySnapshot).all():
        if len(snapshot.country_code) != 2:
            continue
        payload = country_map.setdefault(snapshot.country_code, _make_empty_country_payload(snapshot.country_code))
        payload.update(
            {
                "country_code": snapshot.country_code,
                "country_name": snapshot.country_name,
                "country_name_en": snapshot.country_name_en,
                "continent": snapshot.continent,
                "flag_image_url": snapshot.flag_image_url,
                "map_image_url": snapshot.map_image_url,
                "alert_level": snapshot.alert_level,
                "alert_summary": snapshot.alert_summary,
                "attention": snapshot.attention,
                "attention_partial": snapshot.attention_partial,
                "attention_note": snapshot.attention_note,
                "control": snapshot.control,
                "control_partial": snapshot.control_partial,
                "control_note": snapshot.control_note,
                "limita": snapshot.limita,
                "limita_partial": snapshot.limita_partial,
                "limita_note": snapshot.limita_note,
                "ban": snapshot.ban,
                "ban_partial": snapshot.ban_partial,
                "ban_note": snapshot.ban_note,
                "entry_requirement": snapshot.entry_requirement,
                "entry_requirement_details": snapshot.entry_requirement_details,
                "quarantine_summary": snapshot.quarantine_summary,
                "quarantine_diseases": snapshot.quarantine_diseases or dump_json([]),
                "source_updated_at": snapshot.source_updated_at,
            }
        )
        _register_country_names(name_lookup, snapshot.country_code, snapshot.country_name, snapshot.country_name_en)

    for mapping in db.query(TouristCountryMapping).all():
        if len(mapping.app_country_code) != 2:
            continue
        _register_country_names(
            name_lookup,
            mapping.app_country_code,
            mapping.country_name,
            mapping.country_name_en,
        )
        for alias in load_json_list(mapping.aliases_json):
            normalized = normalize_text(alias)
            if normalized:
                name_lookup[normalized] = mapping.app_country_code

    return country_map, name_lookup


def _build_country_seed_catalog() -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    ko_locale = Locale.parse("ko")
    en_locale = Locale.parse("en")
    country_map: dict[str, dict[str, Any]] = {}
    name_lookup: dict[str, str] = {}

    for code, country_name in ko_locale.territories.items():
        if not _is_supported_country_code(code):
            continue
        payload = _make_empty_country_payload(code)
        payload["country_name"] = country_name
        payload["country_name_en"] = en_locale.territories.get(code)
        country_map[code] = payload
        _register_country_names(name_lookup, code, payload["country_name"], payload["country_name_en"])

    for alias, code in MANUAL_COUNTRY_CODE_ALIASES.items():
        if code not in country_map:
            continue
        name_lookup[normalize_text(alias)] = code

    return country_map, name_lookup


def _is_supported_country_code(code: str) -> bool:
    return len(code) == 2 and code.isalpha() and code.upper() not in NON_COUNTRY_TERRITORY_CODES


def _make_empty_country_payload(code: str) -> dict[str, Any]:
    return {
        "country_code": code,
        "country_name": code,
        "country_name_en": None,
        "continent": None,
        "flag_image_url": None,
        "map_image_url": None,
        "alert_level": "none",
        "alert_summary": None,
        "attention": None,
        "attention_partial": None,
        "attention_note": None,
        "control": None,
        "control_partial": None,
        "control_note": None,
        "limita": None,
        "limita_partial": None,
        "limita_note": None,
        "ban": None,
        "ban_partial": None,
        "ban_note": None,
        "entry_requirement": None,
        "entry_requirement_details": None,
        "quarantine_summary": None,
        "quarantine_diseases": dump_json([]),
        "source_updated_at": None,
    }


def _apply_warning_seed_rows(
    country_map: dict[str, dict[str, Any]],
    name_lookup: dict[str, str],
    rows: list[dict[str, Any]],
) -> None:
    for row in rows:
        code = normalize_code(pick_first(row, "country_iso_alp2", "countryIsoAlp2"))
        country_name = pick_first(row, "country_nm", "countryName")
        if not code or not country_name:
            continue

        payload = country_map.setdefault(
            code,
            {
                "country_code": code,
                "country_name": country_name,
                "country_name_en": pick_first(row, "country_eng_nm", "countryEnName"),
                "continent": pick_first(row, "continent_nm", "continentName"),
                "flag_image_url": pick_first(row, "flag_download_url"),
                "map_image_url": pick_first(row, "dang_map_download_url", "map_download_url"),
                "alert_level": "none",
                "alert_summary": None,
                "attention": None,
                "attention_partial": None,
                "attention_note": None,
                "control": None,
                "control_partial": None,
                "control_note": None,
                "limita": None,
                "limita_partial": None,
                "limita_note": None,
                "ban": None,
                "ban_partial": None,
                "ban_note": None,
                "entry_requirement": None,
                "entry_requirement_details": None,
                "quarantine_summary": None,
                "quarantine_diseases": dump_json([]),
                "source_updated_at": None,
            },
        )
        payload["country_name"] = payload.get("country_name") or country_name
        payload["country_name_en"] = payload.get("country_name_en") or pick_first(
            row, "country_eng_nm", "countryEnName"
        )
        payload["continent"] = payload.get("continent") or pick_first(
            row, "continent_nm", "continentName"
        )
        payload["flag_image_url"] = payload.get("flag_image_url") or pick_first(
            row, "flag_download_url"
        )
        payload["map_image_url"] = payload.get("map_image_url") or pick_first(
            row, "dang_map_download_url", "map_download_url"
        )
        _register_country_names(name_lookup, code, payload["country_name"], payload.get("country_name_en"))


def _apply_travel_warning_rows(
    country_map: dict[str, dict[str, Any]],
    name_lookup: dict[str, str],
    rows: list[dict[str, Any]],
) -> None:
    for row in rows:
        code = _resolve_country_code(row, name_lookup)
        if not code or code not in country_map:
            continue

        target = country_map[code]
        target["country_name"] = target["country_name"] or pick_first(
            row, "country_nm", "countryName"
        )
        target["country_name_en"] = target["country_name_en"] or pick_first(
            row, "country_eng_nm", "countryEnName"
        )
        target["continent"] = pick_first(
            row,
            "continent_nm",
            "continentName",
            "continent",
        ) or target.get("continent")
        target["flag_image_url"] = pick_first(
            row,
            "flag_download_url",
            "imgUrl",
        ) or target.get("flag_image_url")
        target["map_image_url"] = pick_first(
            row,
            "dang_map_download_url",
            "danger_map_download_url",
            "map_download_url",
            "imgUrl2",
        ) or target.get("map_image_url")
        _apply_alarm_level(
            target,
            alarm_level=pick_first(row, "alarm_lvl"),
            region_type=pick_first(row, "region_ty"),
            remark=pick_first(row, "remark"),
        )
        target["source_updated_at"] = pick_first(
            row,
            "wrt_dt",
            "wrtDt",
            "written_dt",
        ) or target.get("source_updated_at")
        target["alert_level"] = _determine_alert_level(target)
        target["alert_summary"] = _build_alert_summary(target)


def _apply_travel_ban_rows(
    country_map: dict[str, dict[str, Any]],
    name_lookup: dict[str, str],
    rows: list[dict[str, Any]],
) -> None:
    for row in rows:
        code = _resolve_country_code(row, name_lookup)
        if not code:
            continue

        target = country_map.setdefault(
            code,
            {
                "country_code": code,
                "country_name": pick_first(row, "countryName") or code,
                "country_name_en": pick_first(row, "countryEnName"),
                "continent": pick_first(row, "continent"),
                "flag_image_url": pick_first(row, "imgUrl"),
                "map_image_url": pick_first(row, "imgUrl2"),
                "alert_level": "none",
                "alert_summary": None,
                "attention": None,
                "attention_partial": None,
                "attention_note": None,
                "control": None,
                "control_partial": None,
                "control_note": None,
                "limita": None,
                "limita_partial": None,
                "limita_note": None,
                "ban": None,
                "ban_partial": None,
                "ban_note": None,
                "entry_requirement": None,
                "entry_requirement_details": None,
                "quarantine_summary": None,
                "quarantine_diseases": dump_json([]),
                "source_updated_at": None,
            },
        )
        _register_country_names(
            name_lookup,
            code,
            pick_first(row, "countryName"),
            pick_first(row, "countryEnName"),
        )
        target["continent"] = target.get("continent") or pick_first(row, "continent")
        target["flag_image_url"] = target.get("flag_image_url") or pick_first(row, "imgUrl")
        target["map_image_url"] = target.get("map_image_url") or pick_first(row, "imgUrl2")
        target["ban"] = pick_first(row, "ban") or target.get("ban")
        target["ban_partial"] = pick_first(
            row,
            "banPartial",
            "ban_partial",
        ) or target.get("ban_partial")
        target["ban_note"] = pick_first(row, "banNote", "ban_note") or target.get("ban_note")
        target["source_updated_at"] = pick_first(row, "wrtDt", "wrt_dt") or target.get(
            "source_updated_at"
        )
        target["alert_level"] = _determine_alert_level(target)
        target["alert_summary"] = _build_alert_summary(target)


def _apply_quarantine_rows(
    country_map: dict[str, dict[str, Any]],
    name_lookup: dict[str, str],
    rows: list[dict[str, Any]],
) -> None:
    latest_date = max(
        (
            date
            for date in (
                pick_first(row, "검역일", "inspectionDate")
                for row in rows
            )
            if date
        ),
        default=None,
    )
    if latest_date is None:
        return

    grouped: dict[str, dict[str, Any]] = {}

    for row in rows:
        if pick_first(row, "검역일", "inspectionDate") != latest_date:
            continue

        code = _resolve_country_code(row, name_lookup)
        if not code or code not in country_map:
            continue

        group = grouped.setdefault(
            code,
            {
                "offices": set(),
                "types": set(),
                "vehicle_count": 0,
                "traveler_count": 0,
            },
        )
        office = pick_first(row, "검역소", "office")
        transport_type = pick_first(row, "구분", "transportType")
        if office:
            group["offices"].add(office)
        if transport_type:
            group["types"].add(transport_type)
        group["vehicle_count"] += _safe_int(pick_first(row, "운송수단 검역수"))
        group["traveler_count"] += sum(
            (
                _safe_int(pick_first(row, "내국인 승객수")),
                _safe_int(pick_first(row, "내국인 승무원수")),
                _safe_int(pick_first(row, "외국인 승객수")),
                _safe_int(pick_first(row, "외국인 승무원수")),
                _safe_int(pick_first(row, "환승객수")),
            )
        )

    for code, group in grouped.items():
        target = country_map[code]
        types = sorted(group["types"])
        target["quarantine_diseases"] = dump_json(types)
        target["quarantine_summary"] = (
            f"{latest_date} 기준 검역소 {len(group['offices'])}곳, "
            f"운송수단 {group['vehicle_count']}건, 여행객 {group['traveler_count']}명"
        )


def _persist_country_snapshots(
    db: Session,
    country_map: dict[str, dict[str, Any]],
    *,
    prune_stale: bool,
) -> None:
    existing = {
        snapshot.country_code: snapshot
        for snapshot in db.query(TouristCountrySnapshot).all()
    }
    synced_at = datetime.now(UTC).replace(tzinfo=None)
    seen_codes: set[str] = set()

    for code, payload in country_map.items():
        if not payload.get("country_name"):
            continue

        snapshot = existing.get(code) or TouristCountrySnapshot(country_code=code)
        snapshot.country_name = payload["country_name"]
        snapshot.country_name_en = payload.get("country_name_en")
        snapshot.continent = payload.get("continent")
        snapshot.flag_image_url = payload.get("flag_image_url")
        snapshot.map_image_url = payload.get("map_image_url")
        snapshot.alert_level = payload.get("alert_level", "none")
        snapshot.alert_summary = payload.get("alert_summary")
        snapshot.attention = payload.get("attention")
        snapshot.attention_partial = payload.get("attention_partial")
        snapshot.attention_note = payload.get("attention_note")
        snapshot.control = payload.get("control")
        snapshot.control_partial = payload.get("control_partial")
        snapshot.control_note = payload.get("control_note")
        snapshot.limita = payload.get("limita")
        snapshot.limita_partial = payload.get("limita_partial")
        snapshot.limita_note = payload.get("limita_note")
        snapshot.ban = payload.get("ban")
        snapshot.ban_partial = payload.get("ban_partial")
        snapshot.ban_note = payload.get("ban_note")
        snapshot.entry_requirement = payload.get("entry_requirement")
        snapshot.entry_requirement_details = payload.get("entry_requirement_details")
        snapshot.quarantine_summary = payload.get("quarantine_summary")
        snapshot.quarantine_diseases = payload.get("quarantine_diseases")
        snapshot.source_updated_at = payload.get("source_updated_at")
        snapshot.synced_at = synced_at

        db.add(snapshot)
        seen_codes.add(code)

    if prune_stale:
        stale_codes = set(existing) - seen_codes
        if stale_codes:
            (
                db.query(TouristCountrySnapshot)
                .filter(TouristCountrySnapshot.country_code.in_(stale_codes))
                .delete(synchronize_session=False)
            )


def _persist_country_mappings(
    db: Session,
    country_map: dict[str, dict[str, Any]],
) -> None:
    existing = {
        mapping.app_country_code: mapping
        for mapping in db.query(TouristCountryMapping).all()
    }
    synced_at = datetime.now(UTC).replace(tzinfo=None)
    seen_codes: set[str] = set()

    for code, payload in country_map.items():
        mapping = existing.get(code) or TouristCountryMapping(
            app_country_code=code,
            iso_alpha2=code[:2],
        )
        aliases = sorted(
            {
                alias
                for alias in (
                    payload.get("country_name"),
                    payload.get("country_name_en"),
                    code,
                )
                if alias
            }
        )
        mapping.iso_alpha2 = code[:2]
        mapping.iso_alpha3 = code if len(code) == 3 else None
        mapping.country_name = payload.get("country_name") or code
        mapping.country_name_en = payload.get("country_name_en")
        mapping.aliases_json = dump_json(aliases)
        mapping.source_key = "travel_warning"
        mapping.is_active = True
        mapping.synced_at = synced_at
        db.add(mapping)
        seen_codes.add(code)

    stale_rows = (
        db.query(TouristCountryMapping)
        .filter(~TouristCountryMapping.app_country_code.in_(seen_codes))
        .all()
    )
    for row in stale_rows:
        row.is_active = False
        db.add(row)


def _persist_vaccination_references(db: Session, rows: list[dict[str, Any]]) -> None:
    existing = {
        ref.vaccine_code: ref
        for ref in db.query(TouristVaccinationReference).all()
    }
    synced_at = datetime.now(UTC).replace(tzinfo=None)
    seen_codes: set[str] = set()

    for row in rows:
        code = pick_first(row, "cd")
        name = pick_first(row, "cdNm")
        if not code or not name:
            continue
        ref = existing.get(code) or TouristVaccinationReference(vaccine_code=code)
        ref.vaccine_name = name
        ref.source_key = "vaccination_reference"
        ref.synced_at = synced_at
        db.add(ref)
        seen_codes.add(code)

    if seen_codes:
        (
            db.query(TouristVaccinationReference)
            .filter(~TouristVaccinationReference.vaccine_code.in_(seen_codes))
            .delete(synchronize_session=False)
        )


def _persist_tourism_statistics(db: Session, rows: list[dict[str, Any]]) -> None:
    existing = {
        (row.metric_key, row.base_ym, row.segment_key): row
        for row in db.query(TouristMonthlyStatistic).all()
    }
    synced_at = datetime.now(UTC).replace(tzinfo=None)
    seen_keys: set[tuple[str, str, str]] = set()

    for row in rows:
        base_ym = pick_first(row, "BASE_YM", "baseYm")
        segment_label = pick_first(row, "SEX_CD", "sexCd")
        if not base_ym or not segment_label or not base_ym.isdigit() or len(base_ym) != 6:
            continue

        key = (
            "tourism_gender_monthly",
            base_ym,
            _normalize_stat_segment_key(segment_label),
        )
        stat = existing.get(key) or TouristMonthlyStatistic(
            metric_key=key[0],
            base_ym=key[1],
            segment_key=key[2],
        )
        stat.segment_label = segment_label
        stat.quantity = _safe_int(row.get("QTY"))
        stat.previous_quantity = _safe_int(row.get("PRE_QTY"))
        stat.change_rate = _safe_float(row.get("C_RATE"))
        stat.source_key = "tourism_statistics"
        stat.synced_at = synced_at
        db.add(stat)
        seen_keys.add(key)

    if seen_keys:
        stale_rows = (
            db.query(TouristMonthlyStatistic)
            .filter(TouristMonthlyStatistic.metric_key == "tourism_gender_monthly")
            .all()
        )
        for row in stale_rows:
            key = (row.metric_key, row.base_ym, row.segment_key)
            if key not in seen_keys:
                db.delete(row)


def _should_refresh_statistics(db: Session) -> bool:
    latest = (
        db.query(TouristMonthlyStatistic)
        .filter(TouristMonthlyStatistic.metric_key == "tourism_gender_monthly")
        .order_by(TouristMonthlyStatistic.base_ym.desc())
        .first()
    )
    if latest is None:
        return True
    current_ym = datetime.now(UTC).strftime("%Y%m")
    return latest.base_ym < current_ym


def _register_country_names(
    name_lookup: dict[str, str],
    code: str,
    country_name: str | None,
    country_name_en: str | None,
) -> None:
    for value in (country_name, country_name_en, code):
        normalized = normalize_text(value)
        if normalized:
            name_lookup[normalized] = code


def _resolve_country_code(
    row: dict[str, Any],
    name_lookup: dict[str, str],
) -> str | None:
    direct_code = normalize_code(
        pick_first(
            row,
            "country_iso_alp2",
            "countryIsoAlp2",
            "isoCode",
            "iso_code",
        )
    )
    if direct_code:
        return direct_code

    for key in (
        "country_nm",
        "countryName",
        "country_name",
        "country_eng_nm",
        "countryEnName",
        "country_en_name",
        "ntnNm",
        "출발국가",
    ):
        value = pick_first(row, key)
        if not value:
            continue
        normalized = normalize_text(value)
        if normalized in name_lookup:
            return name_lookup[normalized]
        if normalized in MANUAL_COUNTRY_CODE_ALIASES:
            return MANUAL_COUNTRY_CODE_ALIASES[normalized]

    return None


def _apply_alarm_level(
    target: dict[str, Any],
    *,
    alarm_level: str | None,
    region_type: str | None,
    remark: str | None,
) -> None:
    if not alarm_level:
        return

    target_field = {
        "1": ("attention", "attention_partial", "attention_note", "여행유의"),
        "2": ("control", "control_partial", "control_note", "여행자제"),
        "3": ("limita", "limita_partial", "limita_note", "출국권고"),
        "4": ("ban", "ban_partial", "ban_note", "여행금지"),
    }.get(str(alarm_level).strip())
    if target_field is None:
        return

    state_key, partial_key, note_key, label = target_field
    target[state_key] = target.get(state_key) or label
    if region_type and region_type != "전체":
        target[partial_key] = target.get(partial_key) or region_type
    if remark:
        target[note_key] = target.get(note_key) or remark


def _determine_alert_level(target: dict[str, Any]) -> str:
    if target.get("ban") or target.get("ban_partial") or target.get("ban_note"):
        return "ban"
    if target.get("limita") or target.get("limita_partial") or target.get("limita_note"):
        return "limita"
    if target.get("control") or target.get("control_partial") or target.get("control_note"):
        return "control"
    if target.get("attention") or target.get("attention_partial") or target.get("attention_note"):
        return "attention"
    return "none"


def _build_alert_summary(target: dict[str, Any]) -> str:
    for key in (
        "ban_note",
        "limita_note",
        "control_note",
        "attention_note",
        "ban_partial",
        "limita_partial",
        "control_partial",
        "attention_partial",
    ):
        value = target.get(key)
        if value:
            return str(value)
    return ""


def _normalize_stat_segment_key(value: str) -> str:
    return {
        "남성": "male",
        "여성": "female",
        "승무원": "crew",
        "전체": "total",
    }.get(value, normalize_text(value) or "other")


def _safe_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _prune_obsolete_sources(db: Session) -> None:
    (
        db.query(TouristDataSource)
        .filter(~TouristDataSource.source_key.in_(CURRENT_SOURCE_KEYS))
        .delete(synchronize_session=False)
    )


def _upsert_manual_source(db: Session) -> None:
    _upsert_data_source(
        db=db,
        source_key="customs_manual",
        status="manual",
        item_count=1,
        last_error=None,
    )
    db.commit()


def _upsert_data_source(
    *,
    db: Session,
    source_key: str,
    status: str,
    item_count: int,
    last_error: str | None,
) -> None:
    definition = SOURCE_DEFINITIONS[source_key]
    data_source = (
        db.query(TouristDataSource)
        .filter(TouristDataSource.source_key == source_key)
        .one_or_none()
    )
    if data_source is None:
        data_source = TouristDataSource(source_key=source_key)

    data_source.display_order = definition["display_order"]
    data_source.label = definition["label"]
    data_source.organization = definition["organization"]
    data_source.url = definition["official_url"]
    data_source.note = definition["note"]
    data_source.status = status
    data_source.item_count = item_count
    data_source.last_error = last_error
    data_source.last_synced_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(data_source)
