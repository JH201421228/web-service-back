from pydantic import BaseModel


class TouristDataSourceResponse(BaseModel):
    id: str
    label: str
    organization: str
    url: str
    officialUrl: str
    note: str
    lastCheckedAt: str
    status: str
    refreshCycle: str
    isManuallyVerified: bool


class TouristDashboardBarResponse(BaseModel):
    label: str
    value: int


class TouristDashboardCardResponse(BaseModel):
    id: str
    title: str
    subtitle: str
    sourceLabel: str
    status: str
    bars: list[TouristDashboardBarResponse]


class TouristCountrySummaryResponse(BaseModel):
    code: str
    nameKr: str
    nameEn: str | None = None
    region: str
    badgeLabel: str
    alertLevel: str
    alertLabel: str
    summary: str
    entrySummary: str | None = None
    quarantineSummary: str | None = None
    lastUpdatedAt: str
    flagImageUrl: str | None = None


class TouristHomeSummaryResponse(BaseModel):
    countryCount: int
    attentionCount: int
    controlCount: int
    limitaCount: int
    banCount: int
    quarantineCountryCount: int


class TouristHomeResponse(BaseModel):
    generatedAt: str
    summary: TouristHomeSummaryResponse
    featuredCountries: list[TouristCountrySummaryResponse]
    dashboardStats: list[TouristDashboardCardResponse]
    officialSources: list[TouristDataSourceResponse]


class TouristCountryDetailResponse(BaseModel):
    code: str
    nameKr: str
    nameEn: str | None = None
    region: str
    alertLevel: str
    alertLabel: str
    alertSummary: str
    entryRequirement: str | None = None
    quarantineSummary: str | None = None
    quarantineDiseases: list[str]
    vaccinationReferences: list[str]
    flagImageUrl: str | None = None
    mapImageUrl: str | None = None
    lastUpdatedAt: str
    syncedAt: str
    changeWarning: str
    officialUrl: str
    sources: list[TouristDataSourceResponse]


class TouristMonthlyStatisticResponse(BaseModel):
    baseYm: str
    segmentKey: str
    segmentLabel: str
    quantity: int
    previousQuantity: int | None = None
    changeRate: float | None = None


class TouristVaccinationReferenceResponse(BaseModel):
    code: str
    name: str
