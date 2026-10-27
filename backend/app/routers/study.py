from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.deps import DbSession, StudyServiceDep
from app.schemas.study import (
    StudyAnswerIn,
    StudyCardOut,
    StudySessionCreate,
    StudySessionOut,
)

router = APIRouter(prefix="/api/study", tags=["study-sessions"])


def get_study_session_or_404(
    session_id: Annotated[str, Path()],
    service: StudyServiceDep,
):
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Study session not found")
    return session


StudySessionOr404 = Annotated[object, Depends(get_study_session_or_404)]


@router.post("/sessions", response_model=StudySessionOut, status_code=status.HTTP_201_CREATED)
def create_study_session(
    payload: StudySessionCreate,
    service: StudyServiceDep,
) -> StudySessionOut:
    """카드 필터(카테고리/암기 여부)로 학습 세션을 시작합니다."""
    session = service.create_session(payload)
    return service.to_out(session)


@router.get("/sessions", response_model=list[StudySessionOut])
def list_study_sessions(
    service: StudyServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[StudySessionOut]:
    return [service.to_out(s, with_card=False) for s in service.list_sessions(limit=limit)]


@router.get("/sessions/{session_id}", response_model=StudySessionOut)
def get_study_session(session: StudySessionOr404, service: StudyServiceDep) -> StudySessionOut:
    return service.to_out(session)


@router.get("/sessions/{session_id}/current", response_model=StudyCardOut)
def get_current_card(session: StudySessionOr404, service: StudyServiceDep) -> StudyCardOut:
    card = service.current_card(session)
    if not card:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No current card")
    return card


@router.post("/sessions/{session_id}/answer", response_model=StudySessionOut)
def answer_card(
    payload: StudyAnswerIn,
    session: StudySessionOr404,
    service: StudyServiceDep,
) -> StudySessionOut:
    """현재 카드를 외웠는지 채점하고 다음 카드로 넘어갑니다."""
    session = service.answer(session, payload)
    return service.to_out(session)


@router.post("/sessions/{session_id}/complete", response_model=StudySessionOut)
def complete_study_session(
    session: StudySessionOr404,
    service: StudyServiceDep,
) -> StudySessionOut:
    return service.to_out(service.complete(session))
