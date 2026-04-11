import os
import json
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


REAPER_DB_HOST = env_with_fallback("REAPER_DB_HOST", "NEWSBASE_DB_HOST")
REAPER_DB_PORT = env_with_fallback("REAPER_DB_PORT", "NEWSBASE_DB_PORT")
REAPER_DB_USER = env_with_fallback("REAPER_DB_USER", "NEWSBASE_DB_USER")
REAPER_DB_PASSWORD = env_with_fallback("REAPER_DB_PASSWORD", "NEWSBASE_DB_PASSWORD")
REAPER_DB_CHARSET = env_with_fallback("REAPER_DB_CHARSET", "NEWSBASE_DB_CHARSET")
REAPER_DB_NAME = must_env("REAPER_DB_NAME")

REAPER_FIREBASE_DATABASE_URL = os.getenv(
    "REAPER_FIREBASE_DATABASE_URL",
    "https://reapear-game-default-rtdb.asia-southeast1.firebasedatabase.app"
)
REAPER_FIREBASE_CREDENTIALS_JSON = os.getenv("REAPER_FIREBASE_CREDENTIALS_JSON", "")
REAPER_FIREBASE_CREDENTIALS_PATH = os.getenv("REAPER_FIREBASE_CREDENTIALS_PATH", "")


def build_reaper_db_url(db_name: str = REAPER_DB_NAME) -> str:
    return (
        f"mysql+pymysql://{REAPER_DB_USER}:{REAPER_DB_PASSWORD}"
        f"@{REAPER_DB_HOST}:{REAPER_DB_PORT}/{db_name}"
        f"?charset={REAPER_DB_CHARSET}"
    )


def get_reaper_firebase_credentials():
    if REAPER_FIREBASE_CREDENTIALS_JSON:
        try:
            return json.loads(REAPER_FIREBASE_CREDENTIALS_JSON)
        except json.JSONDecodeError:
            return None
    if REAPER_FIREBASE_CREDENTIALS_PATH and os.path.exists(REAPER_FIREBASE_CREDENTIALS_PATH):
        with open(REAPER_FIREBASE_CREDENTIALS_PATH) as f:
            return json.load(f)
    return None
