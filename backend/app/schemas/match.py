from datetime import datetime

from pydantic import BaseModel, Field


class MatchResultRead(BaseModel):
    id: int
    mission_id: int
    profile_id: int
    structured_score: float
    semantic_score: float
    business_score: float
    final_score: float
    explanation_tags: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchScoreBreakdown(BaseModel):
    structured_score: float
    semantic_score: float
    business_score: float
    final_score: float
    explanation_tags: list[str] = Field(default_factory=list)
