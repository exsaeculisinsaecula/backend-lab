from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Concept, QuizQuestion, WrongAnswer
from app.services import (
    AnalyticsService,
    CategoryService,
    ConceptService,
    ProgressService,
    QuizGameService,
    QuizService,
    ReviewService,
    SearchService,
    StudyService,
    TransferService,
    WrongAnswerService,
)

# ── DB ──────────────────────────────────────────────────────
DbSession = Annotated[Session, Depends(get_db)]


# ── Services (Depends) ──────────────────────────────────────
def get_category_service(db: DbSession) -> CategoryService:
    return CategoryService(db)


def get_concept_service(db: DbSession) -> ConceptService:
    return ConceptService(db)


def get_quiz_service(db: DbSession) -> QuizService:
    return QuizService(db)


def get_wrong_service(db: DbSession) -> WrongAnswerService:
    return WrongAnswerService(db)


def get_progress_service(db: DbSession) -> ProgressService:
    return ProgressService(db)


def get_study_service(db: DbSession) -> StudyService:
    return StudyService(db)


def get_quiz_game_service(db: DbSession) -> QuizGameService:
    return QuizGameService(db)


def get_review_service(db: DbSession) -> ReviewService:
    return ReviewService(db)


def get_analytics_service(db: DbSession) -> AnalyticsService:
    return AnalyticsService(db)


def get_search_service(db: DbSession) -> SearchService:
    return SearchService(db)


def get_transfer_service(db: DbSession) -> TransferService:
    return TransferService(db)


CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
ConceptServiceDep = Annotated[ConceptService, Depends(get_concept_service)]
QuizServiceDep = Annotated[QuizService, Depends(get_quiz_service)]
WrongAnswerServiceDep = Annotated[WrongAnswerService, Depends(get_wrong_service)]
ProgressServiceDep = Annotated[ProgressService, Depends(get_progress_service)]
StudyServiceDep = Annotated[StudyService, Depends(get_study_service)]
QuizGameServiceDep = Annotated[QuizGameService, Depends(get_quiz_game_service)]
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
TransferServiceDep = Annotated[TransferService, Depends(get_transfer_service)]


# ── Path entity loaders (Depends) ───────────────────────────
def get_category_or_404(category_id: str, service: CategoryServiceDep) -> Category:
    category = service.get(category_id)
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return category


def get_concept_or_404(concept_id: str, service: ConceptServiceDep) -> Concept:
    concept = service.get(concept_id)
    if not concept:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Concept not found")
    return concept


def get_quiz_or_404(quiz_id: str, service: QuizServiceDep) -> QuizQuestion:
    row = service.get(quiz_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz question not found")
    return row


def get_wrong_or_404(wrong_id: str, service: WrongAnswerServiceDep) -> WrongAnswer:
    row = service.get(wrong_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Wrong answer not found")
    return row


CategoryOr404 = Annotated[Category, Depends(get_category_or_404)]
ConceptOr404 = Annotated[Concept, Depends(get_concept_or_404)]
QuizOr404 = Annotated[QuizQuestion, Depends(get_quiz_or_404)]
WrongOr404 = Annotated[WrongAnswer, Depends(get_wrong_or_404)]
