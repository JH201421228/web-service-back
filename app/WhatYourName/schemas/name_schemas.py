from pydantic import BaseModel, Field
from typing import List

class NameRequest(BaseModel):
    name: str = Field(..., description="Korean name to embed")
    gender: str = Field(..., description="Gender: 'M', 'F', 'U', or 'UNK'")
    language: str = Field(..., description="Target language: 'en', 'es', 'ja', 'zh'")

class CandidateName(BaseModel):
    name: str
    gender: str
    score: float

class NameResponse(BaseModel):
    results: List[CandidateName]
