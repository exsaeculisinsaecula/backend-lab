from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Study session ───────────────────────────────────────────
class StudySessionCreate(BaseModel):
    category_id: str | None = None
    only_unknown: bool = False
    only_known: bool = False
    shuffle: bool = True
    limit: int = Field(default=20, ge=1, le=200)


class StudyAnswerIn(BaseModel):
    is_known: bool


class StudyCardOut(BaseModel):
    index: int
    total: int
    concept_id: str
    term: str
    definition: str
    example: str
    category_id: str
    is_known: bool


class StudySessionOut(BaseModel):
    id: str
    category_id: str | None
    current_index: int
    total: int
    answered: int
    known: int
    unknown: int
    is_completed: bool
    started_at: datetime
    completed_at: datetime | None
    current_card: StudyCardOut | None = None

    model_config = ConfigDict(from_attributes=True)


# ── Quiz game ───────────────────────────────────────────────
class QuizGenerateIn(BaseModel):
    size: int = Field(default=10, ge=1, le=50)
    category_id: str | None = None
    include_advanced: bool = True
    shuffle: bool = True


class QuizSessionCreate(BaseModel):
    size: int = Field(default=10, ge=1, le=50)
    category_id: str | None = None
    source: str = Field(default="generated", pattern="^(generated|db|wrong)$")
    include_advanced: bool = True


class QuizQuestionOut(BaseModel):
    key: str
    type: str
    question: str
    choices: list[str]
    correct_index: int
    explanation: str
    category_id: str


class QuizAnswerIn(BaseModel):
    choice_index: int = Field(ge=0)


class QuizAnswerResult(BaseModel):
    correct: bool
    correct_index: int
    selected_index: int
    explanation: str
    score: int
    total: int
    next_question: QuizQuestionOut | None = None
    is_completed: bool = False
    accuracy: float | None = None


class QuizSessionOut(BaseModel):
    id: str
    source: str
    current_index: int
    total: int
    score: int
    answered: int
    is_completed: bool
    started_at: datetime
    completed_at: datetime | None
    current_question: QuizQuestionOut | None = None
    accuracy: float | None = None


# ── Review ──────────────────────────────────────────────────
class ReviewQueueItem(BaseModel):
    kind: str  # concept | wrong
    id: str
    title: str
    description: str
    category_id: str
    priority: int


class ReviewCompleteIn(BaseModel):
    kind: str = Field(pattern="^(concept|wrong)$")
    id: str
    known: bool = True


# ── Analytics ───────────────────────────────────────────────
class CategoryProgress(BaseModel):
    category_id: str
    name: str
    icon: str
    total: int
    known: int
    percent: int


class WeakArea(BaseModel):
    category_id: str
    name: str
    open_wrong: int
    unknown_concepts: int
    score: int


class TimelineItem(BaseModel):
    date: str
    answered: int
    correct: int


class DashboardOut(BaseModel):
    total_concepts: int
    known_concepts: int
    known_percent: int
    total_quiz_questions: int
    open_wrong: int
    mastered_wrong: int
    answered: int
    correct: int
    accuracy: float | None
    study_sessions: int
    quiz_sessions: int
    today: TimelineItem
    categories: list[CategoryProgress]
    weak_areas: list[WeakArea]


# ── Search ──────────────────────────────────────────────────
class SearchHit(BaseModel):
    kind: str  # concept | quiz | wrong
    id: str
    title: str
    snippet: str
    category_id: str
    score: float


class SearchOut(BaseModel):
    query: str
    total: int
    hits: list[SearchHit]


# ── Transfer ────────────────────────────────────────────────
class ExportOut(BaseModel):
    exported_at: datetime
    categories: list[dict]
    concepts: list[dict]
    quiz_questions: list[dict]
    wrong_answers: list[dict]
    progress: list[dict]


class ImportIn(BaseModel):
    categories: list[dict] = Field(default_factory=list)
    concepts: list[dict] = Field(default_factory=list)
    quiz_questions: list[dict] = Field(default_factory=list)
    wrong_answers: list[dict] = Field(default_factory=list)
    progress: list[dict] = Field(default_factory=list)


class ImportResult(BaseModel):
    categories: int
    concepts: int
    quiz_questions: int
    wrong_answers: int
    progress: int
    skipped: int
