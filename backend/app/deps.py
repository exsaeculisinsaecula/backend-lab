from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Concept, QuizQuestion, StudySession, QuizSession, User, WrongAnswer
from app.security import decode_access_token
from app.services import (
    AnalyticsService,
    AuthService,
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

# ── Auth ────────────────────────────────────────────────────
_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: DbSession,
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "인증 정보가 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get(User, payload["sub"])
    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# ── Services (Depends) ──────────────────────────────────────
def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)


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


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
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


def get_wrong_or_404(
    wrong_id: str,
    service: WrongAnswerServiceDep,
    user: CurrentUser,
) -> WrongAnswer:
    """자신의 오답만 접근 가능"""
    row = service.get(wrong_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Wrong answer not found")
    if row.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "접근 권한이 없습니다")
    return row


def get_study_session_or_404(
    session_id: str,
    service: StudyServiceDep,
    user: CurrentUser,
) -> StudySession:
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Study session not found")
    if session.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "접근 권한이 없습니다")
    return session


def get_quiz_session_or_404(
    session_id: str,
    service: QuizGameServiceDep,
    user: CurrentUser,
) -> QuizSession:
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz session not found")
    if session.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "접근 권한이 없습니다")
    return session


CategoryOr404 = Annotated[Category, Depends(get_category_or_404)]
ConceptOr404 = Annotated[Concept, Depends(get_concept_or_404)]
QuizOr404 = Annotated[QuizQuestion, Depends(get_quiz_or_404)]
WrongOr404 = Annotated[WrongAnswer, Depends(get_wrong_or_404)]
StudySessionOr404 = Annotated[StudySession, Depends(get_study_session_or_404)]
QuizSessionOr404 = Annotated[QuizSession, Depends(get_quiz_session_or_404)]
