from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from app.Tourist.models.country_snapshot import TouristCountrySnapshot
from app.Tourist.models.data_source import TouristDataSource
from app.Tourist.models.monthly_statistic import TouristMonthlyStatistic
from app.Tourist.models.vaccination_reference import TouristVaccinationReference
from app.Tourist.schemas.tourist import (
    TouristCountryDetailResponse,
    TouristCountrySummaryResponse,
    TouristDashboardBarResponse,
    TouristDashboardCardResponse,
    TouristDataSourceResponse,
    TouristHomeResponse,
    TouristHomeSummaryResponse,
    TouristMonthlyStatisticResponse,
    TouristVaccinationReferenceResponse,
)
from app.Tourist.services.catalog import (
    ALERT_LABELS,
    ALERT_PRIORITY,
    DEFAULT_CHANGE_WARNING,
    SOURCE_DEFINITIONS,
    VACCINATION_REFERENCE_LIMIT,
)
from app.Tourist.services.public_data import load_json_list, shorten_text


class CountrySnapshotNotFoundError(ValueError):
    pass


def list_country_summaries(db: Session) -> list[TouristCountrySummaryResponse]:
    snapshots = db.query(TouristCountrySnapshot).all()
    snapshots.sort(
        key=lambda snapshot: (
            -ALERT_PRIORITY.get(snapshot.alert_level, 0),
            0 if snapshot.quarantine_summary else 1,
            snapshot.country_name,
        )
    )
    return [_to_country_summary(snapshot) for snapshot in snapshots]


def get_country_detail(db: Session, country_code: str) -> TouristCountryDetailResponse:
    snapshot = (
        db.query(TouristCountrySnapshot)
        .filter(TouristCountrySnapshot.country_code == country_code.upper())
        .one_or_none()
    )
    if snapshot is None:
        raise CountrySnapshotNotFoundError(f"{country_code} 국가의 적재 데이터가 없습니다.")

    return TouristCountryDetailResponse(
        code=snapshot.country_code,
        nameKr=snapshot.country_name,
        nameEn=snapshot.country_name_en,
        region=snapshot.continent or "Official Data",
        alertLevel=snapshot.alert_level,
        alertLabel=ALERT_LABELS.get(snapshot.alert_level, ALERT_LABELS["none"]),
        alertSummary=snapshot.alert_summary or "최신 여행경보를 확인하세요.",
        entryRequirement=snapshot.entry_requirement,
        quarantineSummary=snapshot.quarantine_summary,
        quarantineDiseases=load_json_list(snapshot.quarantine_diseases),
        vaccinationReferences=[
            item.name for item in list_vaccination_references(db)[:VACCINATION_REFERENCE_LIMIT]
        ],
        flagImageUrl=snapshot.flag_image_url,
        mapImageUrl=snapshot.map_image_url,
        lastUpdatedAt=_build_last_updated_at(snapshot),
        syncedAt=snapshot.synced_at.isoformat(),
        changeWarning=DEFAULT_CHANGE_WARNING,
        officialUrl=_build_country_official_url(snapshot),
        sources=_list_data_sources(db),
    )


def get_home_payload(db: Session) -> TouristHomeResponse:
    snapshots = db.query(TouristCountrySnapshot).all()
    if not snapshots:
        raise ValueError("적재된 여행 데이터가 없습니다. 동기화를 먼저 실행해야 합니다.")

    counts = Counter(snapshot.alert_level for snapshot in snapshots)
    quarantine_country_count = sum(1 for snapshot in snapshots if snapshot.quarantine_summary)
    featured = sorted(
        snapshots,
        key=lambda snapshot: (
            -ALERT_PRIORITY.get(snapshot.alert_level, 0),
            0 if snapshot.quarantine_summary else 1,
            snapshot.country_name,
        ),
    )[:6]

    return TouristHomeResponse(
        generatedAt=max(snapshot.synced_at for snapshot in snapshots).isoformat(),
        summary=TouristHomeSummaryResponse(
            countryCount=len(snapshots),
            attentionCount=counts.get("attention", 0),
            controlCount=counts.get("control", 0),
            limitaCount=counts.get("limita", 0),
            banCount=counts.get("ban", 0),
            quarantineCountryCount=quarantine_country_count,
        ),
        featuredCountries=[_to_country_summary(snapshot) for snapshot in featured],
        dashboardStats=_build_dashboard_cards(db, snapshots),
        officialSources=_list_data_sources(db),
    )


def list_monthly_statistics(db: Session) -> list[TouristMonthlyStatisticResponse]:
    rows = (
        db.query(TouristMonthlyStatistic)
        .filter(TouristMonthlyStatistic.metric_key == "tourism_gender_monthly")
        .order_by(TouristMonthlyStatistic.base_ym.asc(), TouristMonthlyStatistic.segment_key.asc())
        .all()
    )
    return [
        TouristMonthlyStatisticResponse(
            baseYm=row.base_ym,
            segmentKey=row.segment_key,
            segmentLabel=row.segment_label,
            quantity=row.quantity,
            previousQuantity=row.previous_quantity,
            changeRate=row.change_rate,
        )
        for row in rows
    ]


def list_vaccination_references(db: Session) -> list[TouristVaccinationReferenceResponse]:
    rows = (
        db.query(TouristVaccinationReference)
        .order_by(TouristVaccinationReference.vaccine_code.asc())
        .all()
    )
    return [
        TouristVaccinationReferenceResponse(
            code=row.vaccine_code,
            name=row.vaccine_name,
        )
        for row in rows
    ]


def _build_last_updated_at(snapshot: TouristCountrySnapshot) -> str:
    if snapshot.source_updated_at:
        return snapshot.source_updated_at
    return snapshot.synced_at.date().isoformat()


def _to_country_summary(snapshot: TouristCountrySnapshot) -> TouristCountrySummaryResponse:
    quarantine_summary = snapshot.quarantine_summary
    summary = (
        shorten_text(snapshot.alert_summary, limit=140)
        or quarantine_summary
        or "최신 여행경보를 확인하세요."
    )

    if snapshot.alert_level != "none":
        badge_label = ALERT_LABELS.get(snapshot.alert_level, ALERT_LABELS["none"])
    elif quarantine_summary:
        badge_label = "검역관리"
    else:
        badge_label = "업데이트 완료"

    return TouristCountrySummaryResponse(
        code=snapshot.country_code,
        nameKr=snapshot.country_name,
        nameEn=snapshot.country_name_en,
        region=snapshot.continent or "Official Data",
        badgeLabel=badge_label,
        alertLevel=snapshot.alert_level,
        alertLabel=ALERT_LABELS.get(snapshot.alert_level, ALERT_LABELS["none"]),
        summary=summary,
        entrySummary=shorten_text(snapshot.entry_requirement, limit=140),
        quarantineSummary=quarantine_summary,
        lastUpdatedAt=_build_last_updated_at(snapshot),
        flagImageUrl=snapshot.flag_image_url,
    )


def _build_dashboard_cards(
    db: Session,
    snapshots: list[TouristCountrySnapshot],
) -> list[TouristDashboardCardResponse]:
    cards: list[TouristDashboardCardResponse] = []
    statistics = list_monthly_statistics(db)
    if statistics:
        cards.append(_build_monthly_trend_card(statistics))
        cards.append(_build_gender_share_card(statistics))
    cards.append(_build_alert_distribution_card(snapshots))
    return cards


def _build_monthly_trend_card(
    statistics: list[TouristMonthlyStatisticResponse],
) -> TouristDashboardCardResponse:
    totals = [row for row in statistics if row.segmentKey == "total"][-6:]
    max_quantity = max((row.quantity for row in totals), default=1)
    bars = [
        TouristDashboardBarResponse(
            label=f"{row.baseYm[4:6]}월",
            value=round(row.quantity / max_quantity * 100) if max_quantity else 0,
        )
        for row in totals
    ]
    return TouristDashboardCardResponse(
        id="monthly-trend",
        title="월간 해외관광 추이",
        subtitle="한국관광 데이터랩 기준 최근 6개월 전체 해외관광객 흐름입니다.",
        sourceLabel="한국관광공사 해외관광 통계",
        status="실데이터",
        bars=bars,
    )


def _build_gender_share_card(
    statistics: list[TouristMonthlyStatisticResponse],
) -> TouristDashboardCardResponse:
    latest_month = max(row.baseYm for row in statistics)
    latest_rows = [
        row
        for row in statistics
        if row.baseYm == latest_month and row.segmentKey in {"male", "female", "crew", "total"}
    ]
    total_row = next((row for row in latest_rows if row.segmentKey == "total"), None)
    total_quantity = total_row.quantity if total_row and total_row.quantity else 1
    bars = [
        TouristDashboardBarResponse(
            label=row.segmentLabel,
            value=round(row.quantity / total_quantity * 100) if total_quantity else 0,
        )
        for row in latest_rows
        if row.segmentKey != "total"
    ]
    return TouristDashboardCardResponse(
        id="gender-share",
        title="최신 출국자 구성",
        subtitle=f"{latest_month[:4]}년 {latest_month[4:6]}월 기준 성별/승무원 비중입니다.",
        sourceLabel="한국관광공사 해외관광 통계",
        status="실데이터",
        bars=bars,
    )


def _build_alert_distribution_card(
    snapshots: list[TouristCountrySnapshot],
) -> TouristDashboardCardResponse:
    total = max(len(snapshots), 1)
    alert_counts = Counter(snapshot.alert_level for snapshot in snapshots)
    bars = [
        TouristDashboardBarResponse(
            label=ALERT_LABELS[level],
            value=round(alert_counts.get(level, 0) / total * 100),
        )
        for level in ("attention", "control", "limita", "ban")
    ]
    return TouristDashboardCardResponse(
        id="alert-distribution",
        title="여행경보 분포",
        subtitle="현재 적재된 국가별 여행경보 비중입니다.",
        sourceLabel="외교부 여행경보 / 여행금지",
        status="실데이터",
        bars=bars,
    )


def _list_data_sources(db: Session) -> list[TouristDataSourceResponse]:
    rows = (
        db.query(TouristDataSource)
        .order_by(TouristDataSource.display_order.asc())
        .all()
    )
    return [_to_source_response(row) for row in rows]


def _to_source_response(row: TouristDataSource) -> TouristDataSourceResponse:
    definition = SOURCE_DEFINITIONS.get(row.source_key, {})
    return TouristDataSourceResponse(
        id=row.source_key,
        label=row.label,
        organization=row.organization,
        url=row.url,
        officialUrl=row.url,
        note=row.note,
        lastCheckedAt=row.last_synced_at.date().isoformat() if row.last_synced_at else "-",
        status=row.status,
        refreshCycle=definition.get("refresh_cycle", "daily"),
        isManuallyVerified=bool(definition.get("is_manually_verified", False)),
    )


def _build_country_official_url(snapshot: TouristCountrySnapshot) -> str:
    if snapshot.alert_level != "none":
        return SOURCE_DEFINITIONS["travel_warning"]["official_url"]
    if snapshot.quarantine_summary:
        return SOURCE_DEFINITIONS["quarantine_region"]["official_url"]
    return SOURCE_DEFINITIONS["travel_ban"]["official_url"]
