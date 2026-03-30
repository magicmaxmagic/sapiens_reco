from pydantic import BaseModel, Field


class SearchProfilesResponse(BaseModel):
    total: int
    items: list[int] = Field(default_factory=list)
