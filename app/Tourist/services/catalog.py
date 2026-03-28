from __future__ import annotations

ALERT_LABELS = {
    "none": "특이 경보 없음",
    "attention": "여행유의",
    "control": "여행자제",
    "limita": "출국권고",
    "ban": "여행금지",
}

ALERT_PRIORITY = {
    "none": 0,
    "attention": 1,
    "control": 2,
    "limita": 3,
    "ban": 4,
}

DEFAULT_CHANGE_WARNING = (
    "비자, 검역, 세관 규정은 수시로 바뀔 수 있으므로 예약 직전과 출국 직전에 "
    "공식 사이트에서 다시 확인해야 합니다."
)

CUSTOMS_OFFICIAL_URL = "https://www.customs.go.kr/"
MOFA_TRAVEL_OFFICIAL_URL = "https://www.data.go.kr/data/15095500/openapi.do"
MOFA_TRAVEL_BAN_OFFICIAL_URL = "https://www.data.go.kr/data/15000504/openapi.do"
KDCA_VACCINATION_OFFICIAL_URL = "https://www.data.go.kr/data/15084296/openapi.do"
KDCA_QUARANTINE_OFFICIAL_URL = "https://www.data.go.kr/data/3074708/fileData.do"
KTO_TOURISM_OFFICIAL_URL = "https://www.data.go.kr/data/15136217/fileData.do"

SOURCE_DEFINITIONS = {
    "travel_warning": {
        "display_order": 1,
        "label": "외교부 여행경보",
        "organization": "외교부",
        "official_url": MOFA_TRAVEL_OFFICIAL_URL,
        "note": "국가별 여행유의, 여행자제, 출국권고, 여행금지 경보 정보",
        "refresh_cycle": "daily",
        "is_manually_verified": False,
    },
    "travel_ban": {
        "display_order": 2,
        "label": "외교부 여행금지",
        "organization": "외교부",
        "official_url": MOFA_TRAVEL_BAN_OFFICIAL_URL,
        "note": "국가별 여행금지 및 일부 금지 지역 정보",
        "refresh_cycle": "daily",
        "is_manually_verified": False,
    },
    "vaccination_reference": {
        "display_order": 3,
        "label": "질병관리청 예방접종 기준",
        "organization": "질병관리청",
        "official_url": KDCA_VACCINATION_OFFICIAL_URL,
        "note": "해외여행 전 확인할 수 있는 예방접종 대상 감염병 기준 목록",
        "refresh_cycle": "daily",
        "is_manually_verified": False,
    },
    "quarantine_region": {
        "display_order": 4,
        "label": "질병관리청 검역정보",
        "organization": "질병관리청",
        "official_url": KDCA_QUARANTINE_OFFICIAL_URL,
        "note": "국가별 검역·감염병 관련 원천 데이터",
        "refresh_cycle": "daily",
        "is_manually_verified": False,
    },
    "tourism_statistics": {
        "display_order": 5,
        "label": "한국관광공사 해외관광 통계",
        "organization": "한국관광공사",
        "official_url": KTO_TOURISM_OFFICIAL_URL,
        "note": "한국관광 데이터랩 기반 국민 해외관광객 월간 통계",
        "refresh_cycle": "monthly",
        "is_manually_verified": False,
    },
    "customs_manual": {
        "display_order": 6,
        "label": "관세청 여행자 휴대품 안내",
        "organization": "관세청",
        "official_url": CUSTOMS_OFFICIAL_URL,
        "note": "여행자 휴대품 규정은 공식 웹 안내 기준으로 수동 검수가 필요합니다.",
        "refresh_cycle": "manual",
        "is_manually_verified": True,
    },
}

CURRENT_SOURCE_KEYS = tuple(SOURCE_DEFINITIONS.keys())

VACCINATION_REFERENCE_LIMIT = 6

MANUAL_COUNTRY_CODE_ALIASES = {
    "palestine": "PS",
    "팔레스타인자치지역": "PS",
    "libya": "LY",
    "리비아": "LY",
    "syria": "SY",
    "시리아": "SY",
    "somalia": "SO",
    "소말리아": "SO",
    "iraq": "IQ",
    "이라크": "IQ",
    "afghanistan": "AF",
    "아프가니스탄": "AF",
    "yemen": "YE",
    "예멘": "YE",
    "azerbaijan": "AZ",
    "아제르바이잔": "AZ",
    "sudan": "SD",
    "수단": "SD",
    "myanmar": "MM",
    "미얀마": "MM",
    "philippines": "PH",
    "필리핀": "PH",
    "russia": "RU",
    "러시아": "RU",
    "belarus": "BY",
    "벨라루스": "BY",
    "armenia": "AM",
    "아르메니아": "AM",
    "israel": "IL",
    "이스라엘": "IL",
    "haiti": "HT",
    "아이티": "HT",
    "ukraine": "UA",
    "우크라이나": "UA",
    "laos": "LA",
    "라오스": "LA",
    "lebanon": "LB",
    "레바논": "LB",
    "democraticrepublicofthecongo": "CD",
    "콩고민주공화국": "CD",
}

NON_COUNTRY_TERRITORY_CODES = {
    "AC",
    "CP",
    "CQ",
    "DG",
    "EA",
    "EU",
    "EZ",
    "IC",
    "QO",
    "TA",
    "UN",
    "XA",
    "XB",
    "ZZ",
}
