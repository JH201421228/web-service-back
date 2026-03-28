from fastapi import APIRouter

from app.Tourist.api.v1.tourist import router as tourist_router

api_router = APIRouter(prefix="/api/v1/tourist")
api_router.include_router(tourist_router)
