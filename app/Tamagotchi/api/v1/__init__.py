from fastapi import APIRouter

from app.Tamagotchi.api.v1.tamagotchi import router as tamagotchi_router

api_router = APIRouter(prefix="/api/v1/tamagotchi")
api_router.include_router(tamagotchi_router)
