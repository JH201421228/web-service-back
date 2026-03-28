import os

from dotenv import load_dotenv

load_dotenv()


def must_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing env: {key}")
    return value


def env_with_fallback(key: str, fallback_key: str) -> str:
    value = os.getenv(key) or os.getenv(fallback_key)
    if not value:
        raise RuntimeError(f"Missing env: {key} (fallback: {fallback_key})")
    return value


TOURIST_DB_HOST = env_with_fallback("TOURIST_DB_HOST", "NEWSBASE_DB_HOST")
TOURIST_DB_PORT = env_with_fallback("TOURIST_DB_PORT", "NEWSBASE_DB_PORT")
TOURIST_DB_USER = env_with_fallback("TOURIST_DB_USER", "NEWSBASE_DB_USER")
TOURIST_DB_PASSWORD = env_with_fallback("TOURIST_DB_PASSWORD", "NEWSBASE_DB_PASSWORD")
TOURIST_DB_CHARSET = env_with_fallback("TOURIST_DB_CHARSET", "NEWSBASE_DB_CHARSET")
TOURIST_DB_NAME = must_env("TOURIST_DB_NAME")


def build_tourist_db_url(db_name: str = TOURIST_DB_NAME) -> str:
    return (
        f"mysql+pymysql://{TOURIST_DB_USER}:{TOURIST_DB_PASSWORD}@{TOURIST_DB_HOST}:{TOURIST_DB_PORT}/{db_name}"
        f"?charset={TOURIST_DB_CHARSET}"
    )


TRAVEL_WARNING_SERVICE_KEY = must_env("TOURIST_TRAVEL_WARNING_SERVICE_KEY")
TRAVEL_BAN_SERVICE_KEY = must_env("TOURIST_TRAVEL_BAN_SERVICE_KEY")
VACCINATION_SERVICE_KEY = env_with_fallback(
    "TOURIST_VACCINATION_SERVICE_KEY",
    "TOURIST_TRAVEL_WARNING_SERVICE_KEY",
)
QUARANTINE_REGION_SERVICE_KEY = must_env("TOURIST_QUARANTINE_REGION_SERVICE_KEY")
ODCLOUD_API_KEY = must_env("TOURIST_ODCLOUD_API_KEY")

PUBLIC_DATA_TIMEOUT_SECONDS = int(os.getenv("TOURIST_PUBLIC_DATA_TIMEOUT_SECONDS", "30"))
SCHEDULER_TIMEZONE = os.getenv("TOURIST_SCHEDULER_TIMEZONE", "Asia/Seoul")
KTO_DATALAB_BASE_URL = os.getenv(
    "TOURIST_KTO_DATALAB_BASE_URL",
    "https://datalab.visitkorea.or.kr",
)
KTO_DATALAB_MENU_GROUP = os.getenv("TOURIST_KTO_DATALAB_MENU_GROUP", "1")
KTO_DATALAB_MENU_CODE = os.getenv(
    "TOURIST_KTO_DATALAB_MENU_CODE",
    "10501020000002020120611",
)

TRAVEL_WARNING_ENDPOINTS = [
    "http://apis.data.go.kr/1262000/TravelAlarmService0404/getTravelAlarm0404List",
    "http://apis.data.go.kr/1262000/TravelWarningServiceV3/getTravelWarningListV3",
]
TRAVEL_BAN_ENDPOINT = "http://apis.data.go.kr/1262000/TravelBanService/getTravelBanList"
VACCINATION_REFERENCE_ENDPOINT = "http://apis.data.go.kr/1790387/vcninfo/getCondVcnCd"
QUARANTINE_REGION_ENDPOINT = (
    "https://api.odcloud.kr/api/3074708/v1/"
    "uddi:c2ecefdb-79b0-4c29-9307-98b04a678369"
)
KTO_DATALAB_DATE_INIT_ENDPOINT = f"{KTO_DATALAB_BASE_URL}/portal/getSrchDteDivInitVal.do"
KTO_DATALAB_GRID_ENDPOINT = f"{KTO_DATALAB_BASE_URL}/visualize/getGridData.do"
KTO_TOURISM_GENDER_QID = os.getenv("TOURIST_KTO_TOURISM_GENDER_QID", "TS_01_17_004_New")

LEGACY_COUNTRY_OVERVIEW_SERVICE_KEY = os.getenv("TOURIST_COUNTRY_OVERVIEW_SERVICE_KEY")
LEGACY_ENTRANCE_VISA_SERVICE_KEY = os.getenv("TOURIST_ENTRANCE_VISA_SERVICE_KEY")
LEGACY_COUNTRY_OVERVIEW_ENDPOINT = (
    "http://apis.data.go.kr/1262000/OverviewKorRelationService/getOverviewKorRelationList"
)
LEGACY_ENTRANCE_VISA_ENDPOINT = "http://apis.data.go.kr/1262000/EntranceVisaService2/getEntranceVisaList2"
