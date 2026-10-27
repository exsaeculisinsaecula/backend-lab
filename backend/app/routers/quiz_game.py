from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import CurrentUser, QuizGameServiceDep, QuizSessionOr404
from app.schemas.study import (
    QuizAnswerIn,
    QuizAnswerResult,
    QuizGenerateIn,
    QuizQuestionOut,
    QuizSessionCreate,
    QuizSessionOut,
)

router = APIRouter(prefix="/api/quiz", tags=["quiz-game"])


@router.post("/generate", response_model=list[QuizQuestionOut])
def generate_quiz(
    payload: QuizGenerateIn,
    service: QuizGameServiceDep,
    user: CurrentUser,
) -> list[QuizQuestionOut]:
    return service.generate_questions(
        size=payload.size,
        category_id=payload.category_id,
        include_advanced=payload.include_advanced,
        shuffle=payload.shuffle,
    )


@router.post("/sessions", response_model=QuizSessionOut, status_code=status.HTTP_201_CREATED)
def create_quiz_session(
    payload: QuizSessionCreate,
    service: QuizGameServiceDep,
    user: CurrentUser,
) -> QuizSessionOut:
    session = service.create_session(
        user,
        source=payload.source,
        size=payload.size,
        category_id=payload.category_id,
        include_advanced=payload.include_advanced,
    )
    return service.to_out(session)


@router.get("/sessions", response_model=list[QuizSessionOut])
def list_quiz_sessions(
    service: QuizGameServiceDep,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[QuizSessionOut]:
    return [service.to_out(s) for s in service.list_sessions(user.id, limit=limit)]


@router.get("/sessions/{session_id}", response_model=QuizSessionOut)
def get_quiz_session(
    session: QuizSessionOr404,
    service: QuizGameServiceDep,
    user: CurrentUser,
) -> QuizSessionOut:
    return service.to_out(session)


@router.post("/sessions/{session_id}/answer", response_model=QuizAnswerResult)
def answer_quiz(
    payload: QuizAnswerIn,
    session: QuizSessionOr404,
    service: QuizGameServiceDep,
    user: CurrentUser,
) -> QuizAnswerResult:
    if payload.choice_index >= 4:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "choice_index out of range")
    return service.answer(session, payload.choice_index)


@router.get("/sessions/{session_id}/result")
def quiz_result(
    session: QuizSessionOr404,
    service: QuizGameServiceDep,
    user: CurrentUser,
) -> dict:
    return service.result(session)
