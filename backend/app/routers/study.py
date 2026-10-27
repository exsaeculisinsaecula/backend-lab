from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.deps import CurrentUser, StudyServiceDep, StudySessionOr404
from app.schemas.study import (
    StudyAnswerIn,
    StudyCardOut,
    StudySessionCreate,
    StudySessionOut,
)

router = APIRouter(prefix="/api/study", tags=["study-sessions"])


@router.post("/sessions", response_model=StudySessionOut, status_code=status.HTTP_201_CREATED)
def create_study_session(
    payload: StudySessionCreate,
    service: StudyServiceDep,
    user: CurrentUser,
) -> StudySessionOut:
    session = service.create_session(user, payload)
    return service.to_out(session)


@router.get("/sessions", response_model=list[StudySessionOut])
def list_study_sessions(
    service: StudyServiceDep,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[StudySessionOut]:
    return [
        service.to_out(s, with_card=False)
        for s in service.list_sessions(user.id, limit=limit)
    ]


@router.get("/sessions/{session_id}", response_model=StudySessionOut)
def get_study_session(
    session: StudySessionOr404,
    service: StudyServiceDep,
    user: CurrentUser,
) -> StudySessionOut:
    return service.to_out(session)


@router.get("/sessions/{session_id}/current", response_model=StudyCardOut)
def get_current_card(
    session: StudySessionOr404,
    service: StudyServiceDep,
    user: CurrentUser,
) -> StudyCardOut:
    card = service.current_card(session)
    if not card:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No current card")
    return card


@router.post("/sessions/{session_id}/answer", response_model=StudySessionOut)
def answer_card(
    payload: StudyAnswerIn,
    session: StudySessionOr404,
    service: StudyServiceDep,
    user: CurrentUser,
) -> StudySessionOut:
    session = service.answer(session, payload)
    return service.to_out(session)


@router.post("/sessions/{session_id}/complete", response_model=StudySessionOut)
def complete_study_session(
    session: StudySessionOr404,
    service: StudyServiceDep,
    user: CurrentUser,
) -> StudySessionOut:
    return service.to_out(service.complete(session))
