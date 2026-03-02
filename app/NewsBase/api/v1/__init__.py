from fastapi import APIRouter

from app.NewsBase.api.v1 import auth
from app.NewsBase.api.v1 import news

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(news.router)
