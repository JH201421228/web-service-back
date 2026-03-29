from fastapi import APIRouter

from app.Remember.api.v1.remember import router as remember_router

api_router = APIRouter(prefix="/api/v1/remember")
api_router.include_router(remember_router)
