from datetime import date, datetime

from pydantic import BaseModel, Field


class MissionBase(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=10)
    required_skills: list[str] = Field(default_factory=list)
    required_language: str | None = None
    required_location: str | None = None
    required_seniority: str | None = None
    desired_start_date: date | None = None


class MissionCreate(MissionBase):
    pass


class MissionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    required_skills: list[str] | None = None
    required_language: str | None = None
    required_location: str | None = None
    required_seniority: str | None = None
    desired_start_date: date | None = None


class MissionRead(MissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
