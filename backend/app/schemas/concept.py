from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConceptBase(BaseModel):
    category_id: str = Field(min_length=1, max_length=40)
    term: str = Field(min_length=1, max_length=200)
    definition: str = Field(min_length=1)
    example: str = ""
    is_known: bool = False


class ConceptCreate(ConceptBase):
    id: str | None = Field(default=None, max_length=60)


class ConceptUpdate(BaseModel):
    category_id: str | None = None
    term: str | None = Field(default=None, min_length=1, max_length=200)
    definition: str | None = None
    example: str | None = None
    is_known: bool | None = None


class ConceptOut(ConceptBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
