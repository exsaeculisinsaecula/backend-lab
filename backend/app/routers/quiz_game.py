from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.deps import QuizGameServiceDep
from app.schemas.study import (
    QuizAnswerIn,
    QuizAnswerResult,
    QuizGenerateIn,
    QuizQuestionOut,
    QuizSessionCreate,
    QuizSessionOut,
)

router = APIRouter(prefix="/api/quiz", tags=["quiz-game"])


def get_quiz_session_or_404(
    session_id: Annotated[str, Path()],
    service: QuizGameServiceDep,
):
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz session not found")
    return session


QuizSessionOr404 = Annotated[object, Depends(get_quiz_session_or_404)]


@router.post("/generate", response_model=list[QuizQuestionOut])
def generate_quiz(payload: QuizGenerateIn, service: QuizGameServiceDep) -> list[QuizQuestionOut]:
    """개념 카드에서 선다형 문항을 즉석 생성합니다(세션 없이)."""
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
) -> QuizSessionOut:
    """퀴즈 세션을 시작합니다. source=generated|db|wrong"""
    session = service.create_session(
        source=payload.source,
        size=payload.size,
        category_id=payload.category_id,
        include_advanced=payload.include_advanced,
    )
    return service.to_out(session)


@router.get("/sessions", response_model=list[QuizSessionOut])
def list_quiz_sessions(
    service: QuizGameServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[QuizSessionOut]:
    return [service.to_out(s) for s in service.list_sessions(limit=limit)]


@router.get("/sessions/{session_id}", response_model=QuizSessionOut)
def get_quiz_session(session: QuizSessionOr404, service: QuizGameServiceDep) -> QuizSessionOut:
    return service.to_out(session)


@router.post("/sessions/{session_id}/answer", response_model=QuizAnswerResult)
def answer_quiz(
    payload: QuizAnswerIn,
    session: QuizSessionOr404,
    service: QuizGameServiceDep,
) -> QuizAnswerResult:
    """답안을 제출합니다. 오답이면 오답노트에 자동 저장됩니다."""
    if payload.choice_index >= 4:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "choice_index out of range")
    return service.answer(session, payload.choice_index)


@router.get("/sessions/{session_id}/result")
def quiz_result(session: QuizSessionOr404, service: QuizGameServiceDep) -> dict:
    return service.result(session)
