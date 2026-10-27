from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
