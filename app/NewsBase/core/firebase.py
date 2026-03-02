import firebase_admin
from firebase_admin import credentials

# from app.core.config import FIREBASE_CREDENTIALS_PATH

# # Firebase Admin SDK 초기화 (앱 시작 시 1회만 실행)
# cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)

from app.NewsBase.core.config import get_firebase_credentials

# Firebase Admin SDK 초기화 (앱 시작 시 1회만 실행)
cred = credentials.Certificate(get_firebase_credentials())

firebase_admin.initialize_app(cred)

