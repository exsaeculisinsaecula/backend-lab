from fastapi import APIRouter, HTTPException, status

from app.deps import (
    ConceptServiceDep,
    CurrentUser,
    ProgressServiceDep,
    WrongAnswerServiceDep,
)
from app.schemas.common import MessageOut
from app.schemas.progress import ProgressOut, ProgressUpsert, StatsOut

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/progress", response_model=list[ProgressOut])
def list_progress(service: ProgressServiceDep, user: CurrentUser) -> list[ProgressOut]:
    return service.list(user)


@router.put("/progress", response_model=ProgressOut)
def upsert_progress(
    payload: ProgressUpsert,
    service: ProgressServiceDep,
    user: CurrentUser,
) -> ProgressOut:
    if payload.correct > payload.answered:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "correct cannot exceed answered")
    return service.upsert(user.id, payload)


@router.post("/progress/answer", response_model=ProgressOut)
def record_answer(
    payload: ProgressUpsert,
    service: ProgressServiceDep,
    user: CurrentUser,
) -> ProgressOut:
    return service.record_answer(user.id, payload)


@router.get("/stats", response_model=StatsOut)
def get_stats(service: ProgressServiceDep, user: CurrentUser) -> StatsOut:
    return service.stats(user)


@router.delete("/progress/reset", response_model=MessageOut)
def reset_progress(
    progress: ProgressServiceDep,
    wrong: WrongAnswerServiceDep,
    concepts: ConceptServiceDep,
    user: CurrentUser,
) -> MessageOut:
    progress.delete_all(user.id)
    wrong.delete_all(user.id)
    concepts.reset_known(user.id)
    return MessageOut(message="progress reset")
