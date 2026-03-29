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


TAMAGOTCHI_DB_HOST = env_with_fallback("TAMAGOTCHI_DB_HOST", "NEWSBASE_DB_HOST")
TAMAGOTCHI_DB_PORT = env_with_fallback("TAMAGOTCHI_DB_PORT", "NEWSBASE_DB_PORT")
TAMAGOTCHI_DB_USER = env_with_fallback("TAMAGOTCHI_DB_USER", "NEWSBASE_DB_USER")
TAMAGOTCHI_DB_PASSWORD = env_with_fallback(
    "TAMAGOTCHI_DB_PASSWORD",
    "NEWSBASE_DB_PASSWORD",
)
TAMAGOTCHI_DB_CHARSET = env_with_fallback(
    "TAMAGOTCHI_DB_CHARSET",
    "NEWSBASE_DB_CHARSET",
)
TAMAGOTCHI_DB_NAME = must_env("TAMAGOTCHI_DB_NAME")
TAMAGOTCHI_TIMEZONE = os.getenv("TAMAGOTCHI_TIMEZONE", "Asia/Seoul")


def build_tamagotchi_db_url(db_name: str = TAMAGOTCHI_DB_NAME) -> str:
    return (
        f"mysql+pymysql://{TAMAGOTCHI_DB_USER}:{TAMAGOTCHI_DB_PASSWORD}"
        f"@{TAMAGOTCHI_DB_HOST}:{TAMAGOTCHI_DB_PORT}/{db_name}"
        f"?charset={TAMAGOTCHI_DB_CHARSET}"
    )
