from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuizBase(BaseModel):
    category_id: str = Field(min_length=1, max_length=40)
    question: str = Field(min_length=1)
    choices: list[str] = Field(min_length=2)
    correct_index: int = Field(ge=0)
    explanation: str = ""


class QuizCreate(QuizBase):
    id: str | None = Field(default=None, max_length=60)


class QuizUpdate(BaseModel):
    category_id: str | None = None
    question: str | None = None
    choices: list[str] | None = None
    correct_index: int | None = Field(default=None, ge=0)
    explanation: str | None = None


class QuizOut(BaseModel):
    id: str
    category_id: str
    question: str
    choices: list[str]
    correct_index: int
    explanation: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
