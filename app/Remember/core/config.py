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


REMEMBER_DB_HOST = env_with_fallback("REMEMBER_DB_HOST", "NEWSBASE_DB_HOST")
REMEMBER_DB_PORT = env_with_fallback("REMEMBER_DB_PORT", "NEWSBASE_DB_PORT")
REMEMBER_DB_USER = env_with_fallback("REMEMBER_DB_USER", "NEWSBASE_DB_USER")
REMEMBER_DB_PASSWORD = env_with_fallback("REMEMBER_DB_PASSWORD", "NEWSBASE_DB_PASSWORD")
REMEMBER_DB_CHARSET = env_with_fallback("REMEMBER_DB_CHARSET", "NEWSBASE_DB_CHARSET")
REMEMBER_DB_NAME = must_env("REMEMBER_DB_NAME")
REMEMBER_TIMEZONE = os.getenv("REMEMBER_TIMEZONE", "Asia/Seoul")
REMEMBER_DEFAULT_NICKNAME = os.getenv("REMEMBER_DEFAULT_NICKNAME", "Memory Runner")


def build_remember_db_url(db_name: str = REMEMBER_DB_NAME) -> str:
    return (
        f"mysql+pymysql://{REMEMBER_DB_USER}:{REMEMBER_DB_PASSWORD}@{REMEMBER_DB_HOST}:{REMEMBER_DB_PORT}/{db_name}"
        f"?charset={REMEMBER_DB_CHARSET}"
    )
