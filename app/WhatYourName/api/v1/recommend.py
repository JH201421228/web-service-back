from fastapi import APIRouter
from app.WhatYourName.schemas.name_schemas import NameRequest, NameResponse
from app.WhatYourName.services.recommend_service import get_recommendations

router = APIRouter()

@router.post("/recommend", response_model=NameResponse)
def recommend_names(request: NameRequest):
    return get_recommendations(request)
