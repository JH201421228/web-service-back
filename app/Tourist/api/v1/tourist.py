from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.Tourist.core.deps import get_tourist_db
from app.Tourist.schemas.tourist import (
    TouristCountryDetailResponse,
    TouristCountrySummaryResponse,
    TouristHomeResponse,
    TouristMonthlyStatisticResponse,
    TouristVaccinationReferenceResponse,
)
from app.Tourist.services.tourist import (
    CountrySnapshotNotFoundError,
    get_country_detail,
    get_home_payload,
    list_country_summaries,
    list_monthly_statistics,
    list_vaccination_references,
)

router = APIRouter(tags=["Tourist"])


@router.get(
    "/home",
    response_model=TouristHomeResponse,
    summary="홈 화면 여행 정보 조회",
)
def read_tourist_home(db: Session = Depends(get_tourist_db)) -> TouristHomeResponse:
    try:
        return get_home_payload(db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"홈 화면 여행 정보를 불러오지 못했습니다: {exc}",
        ) from exc


@router.get(
    "/countries",
    response_model=list[TouristCountrySummaryResponse],
    summary="국가별 여행 정보 목록 조회",
)
def read_tourist_countries(
    db: Session = Depends(get_tourist_db),
) -> list[TouristCountrySummaryResponse]:
    try:
        return list_country_summaries(db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"국가별 여행 정보를 불러오지 못했습니다: {exc}",
        ) from exc


@router.get(
    "/countries/{country_code}",
    response_model=TouristCountryDetailResponse,
    summary="국가별 여행 상세 정보 조회",
)
def read_tourist_country_detail(
    country_code: str,
    db: Session = Depends(get_tourist_db),
) -> TouristCountryDetailResponse:
    try:
        return get_country_detail(db=db, country_code=country_code)
    except CountrySnapshotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"국가 상세 정보를 불러오지 못했습니다: {exc}",
        ) from exc


@router.get(
    "/stats/monthly",
    response_model=list[TouristMonthlyStatisticResponse],
    summary="월간 해외관광 통계 조회",
)
def read_tourist_monthly_statistics(
    db: Session = Depends(get_tourist_db),
) -> list[TouristMonthlyStatisticResponse]:
    try:
        return list_monthly_statistics(db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"월간 해외관광 통계를 불러오지 못했습니다: {exc}",
        ) from exc


@router.get(
    "/vaccinations",
    response_model=list[TouristVaccinationReferenceResponse],
    summary="예방접종 기준 정보 조회",
)
def read_tourist_vaccinations(
    db: Session = Depends(get_tourist_db),
) -> list[TouristVaccinationReferenceResponse]:
    try:
        return list_vaccination_references(db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예방접종 기준 정보를 불러오지 못했습니다: {exc}",
        ) from exc
