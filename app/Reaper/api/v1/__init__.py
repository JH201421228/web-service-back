from fastapi import APIRouter

from app.Reaper.api.v1.game import router as game_router

api_router = APIRouter(prefix="/api/v1/reaper")
api_router.include_router(game_router)
