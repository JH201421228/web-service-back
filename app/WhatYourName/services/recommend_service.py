from app.WhatYourName.schemas.name_schemas import NameRequest, NameResponse, CandidateName
from app.WhatYourName.core.inference import model_manager

def get_recommendations(request: NameRequest) -> NameResponse:
    # Get embedding
    embedding = model_manager.get_embedding(request.name, request.gender)
    
    # Get top 5
    top_k_results = model_manager.get_top_k(embedding, request.language, k=5)
    
    candidates = []
    for item in top_k_results:
        candidates.append(CandidateName(
            name=item["name"],
            gender=item["gender"],
            score=item["score"]
        ))
        
    return NameResponse(results=candidates)
