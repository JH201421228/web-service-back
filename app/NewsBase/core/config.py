import os
import json
from dotenv import load_dotenv


load_dotenv()


def must_env(key: str) -> str:
    v = os.getenv(key)
    
    if not v:
        raise RuntimeError(f"Missing env: {key}")
    
    return v
    

APP_ENV = os.getenv("APP_ENV")

DB_HOST = must_env("NEWSBASE_DB_HOST")
DB_PORT = must_env("NEWSBASE_DB_PORT")
DB_USER = must_env("NEWSBASE_DB_USER")
DB_PASSWORD = must_env("NEWSBASE_DB_PASSWORD")
DB_CHARSET = must_env("NEWSBASE_DB_CHARSET")

DB_NAME = must_env("NEWSBASE_DB_NAME")

# Firebase
# FIREBASE_CREDENTIALS_PATH = must_env("FIREBASE_CREDENTIALS_PATH")


def build_db_url(db_name: str=DB_NAME) -> str:
    return (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
        f"?charset={DB_CHARSET}"
    )

# Firebase 설정
def get_firebase_credentials():
    """
    Firebase 인증 정보를 가져옵니다.
    환경변수 FIREBASE_CREDENTIALS_JSON이 있으면 JSON 문자열을 파싱하고,
    없으면 FIREBASE_CREDENTIALS_PATH에서 파일 경로를 읽습니다.
    """
    # 환경변수에서 JSON 문자열로 제공되는 경우 (Cloudtype 등)
    firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if firebase_json:
        try:
            return json.loads(firebase_json)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid FIREBASE_CREDENTIALS_JSON: {e}")
    
    # 파일 경로로 제공되는 경우 (로컬 개발)
    # firebase_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    # if firebase_path:
    #     if not os.path.exists(firebase_path):
    #         raise RuntimeError(f"Firebase credentials file not found: {firebase_path}")
    #     with open(firebase_path, "r", encoding="utf-8") as f:
    #         return json.load(f)
    
    raise RuntimeError(
        "Firebase credentials not found. "
        "Set either FIREBASE_CREDENTIALS_JSON or FIREBASE_CREDENTIALS_PATH"
    )
