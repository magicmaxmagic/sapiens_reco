from datetime import date, datetime

from pydantic import BaseModel, Field


class ExperienceRead(BaseModel):
    id: int
    title: str
    company: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class ProfileBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    raw_text: str | None = None
    parsed_skills: list[str] = Field(default_factory=list)
    parsed_languages: list[str] = Field(default_factory=list)
    parsed_location: str | None = None
    parsed_seniority: str | None = None
    availability_status: str = "unknown"
    source: str = "upload"


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    parsed_skills: list[str] | None = None
    parsed_languages: list[str] | None = None
    parsed_location: str | None = None
    parsed_seniority: str | None = None
    availability_status: str | None = None
    raw_text: str | None = None


class ProfileRead(ProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime
    experiences: list[ExperienceRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
