from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Category ────────────────────────────────────────────────
class CategoryBase(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=80)
    icon: str = Field(default="", max_length=16)
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    icon: str | None = Field(default=None, max_length=16)
    sort_order: int | None = None


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)


# ── Concept ─────────────────────────────────────────────────
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


# ── Quiz ────────────────────────────────────────────────────
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


# ── Wrong answers ───────────────────────────────────────────
class WrongAnswerBase(BaseModel):
    source_id: str = ""
    category_id: str = ""
    question_type: str = ""
    question: str = Field(min_length=1)
    choices: list[str] = Field(min_length=2)
    correct_index: int = Field(ge=0)
    my_index: int = Field(ge=0)
    explanation: str = ""
    mastered: bool = False
    count: int = Field(default=1, ge=1)


class WrongAnswerCreate(WrongAnswerBase):
    pass


class WrongAnswerUpdate(BaseModel):
    my_index: int | None = Field(default=None, ge=0)
    mastered: bool | None = None
    explanation: str | None = None
    count: int | None = Field(default=None, ge=1)


class WrongAnswerOut(BaseModel):
    id: str
    source_id: str
    category_id: str
    question_type: str
    question: str
    choices: list[str]
    correct_index: int
    my_index: int
    explanation: str
    mastered: bool
    count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Progress ────────────────────────────────────────────────
class ProgressUpsert(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    answered: int = Field(default=0, ge=0)
    correct: int = Field(default=0, ge=0)


class ProgressOut(BaseModel):
    date: str
    answered: int
    correct: int

    model_config = ConfigDict(from_attributes=True)


# ── Stats ───────────────────────────────────────────────────
class StatsOut(BaseModel):
    total_concepts: int
    known_concepts: int
    total_quiz_questions: int
    total_wrong: int
    open_wrong: int
    answered: int
    correct: int
    accuracy: float | None


# ── Bulk / misc ─────────────────────────────────────────────
class MessageOut(BaseModel):
    message: str
    detail: dict[str, Any] | None = None
