from datetime import datetime

from pydantic import BaseModel, Field


class SkillTaxonomyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    synonyms: list[str] = Field(default_factory=list)


class SkillTaxonomyCreate(SkillTaxonomyBase):
    pass


class SkillTaxonomyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    synonyms: list[str] | None = Field(default=None)


class SkillTaxonomyRead(SkillTaxonomyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
