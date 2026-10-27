from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    icon: Mapped[str] = mapped_column(String(16), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    concepts: Mapped[list["Concept"]] = relationship(back_populates="category", cascade="all, delete-orphan")
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    term: Mapped[str] = mapped_column(String(200), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    example: Mapped[str] = mapped_column(Text, default="")
    is_known: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    category: Mapped[Category] = relationship(back_populates="concepts")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    choices_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of strings
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    category: Mapped[Category] = relationship(back_populates="quiz_questions")


class WrongAnswer(Base):
    __tablename__ = "wrong_answers"
    __table_args__ = (UniqueConstraint("source_id", "question", name="uq_wrong_source_question"),)

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(60), default="")
    category_id: Mapped[str] = mapped_column(String(40), default="")
    question_type: Mapped[str] = mapped_column(String(30), default="")
    question: Mapped[str] = mapped_column(Text, nullable=False)
    choices_json: Mapped[str] = mapped_column(Text, nullable=False)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    my_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, default="")
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class StudyProgress(Base):
    __tablename__ = "study_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)  # YYYY-MM-DD
    answered: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)


class StudySession(Base):
    """플래시카드 학습 세션"""

    __tablename__ = "study_sessions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    filter_json: Mapped[str] = mapped_column(Text, default="{}")
    concept_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    current_index: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list["StudySessionAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class StudySessionAnswer(Base):
    __tablename__ = "study_session_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False
    )
    concept_id: Mapped[str] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False
    )
    is_known: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    session: Mapped[StudySession] = relationship(back_populates="answers")


class QuizSession(Base):
    """퀴즈 게임 세션"""

    __tablename__ = "quiz_sessions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    source: Mapped[str] = mapped_column(String(20), default="generated")  # generated | db | wrong
    filter_json: Mapped[str] = mapped_column(Text, default="{}")
    questions_json: Mapped[str] = mapped_column(Text, default="[]")
    current_index: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list["QuizSessionAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class QuizSessionAnswer(Base):
    __tablename__ = "quiz_session_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_key: Mapped[str] = mapped_column(String(80), default="")
    my_index: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    session: Mapped[QuizSession] = relationship(back_populates="answers")
