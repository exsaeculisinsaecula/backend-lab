from pydantic import BaseModel, ConfigDict, Field


class ProgressUpsert(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    answered: int = Field(default=0, ge=0)
    correct: int = Field(default=0, ge=0)


class ProgressOut(BaseModel):
    date: str
    answered: int
    correct: int

    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    total_concepts: int
    known_concepts: int
    total_quiz_questions: int
    total_wrong: int
    open_wrong: int
    answered: int
    correct: int
    accuracy: float | None
