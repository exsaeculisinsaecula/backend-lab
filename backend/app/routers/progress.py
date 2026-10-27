from fastapi import APIRouter, HTTPException, status

from app.deps import ConceptServiceDep, ProgressServiceDep, WrongAnswerServiceDep
from app.schemas.common import MessageOut
from app.schemas.progress import ProgressOut, ProgressUpsert, StatsOut

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/progress", response_model=list[ProgressOut])
def list_progress(service: ProgressServiceDep) -> list[ProgressOut]:
    return service.list()


@router.put("/progress", response_model=ProgressOut)
def upsert_progress(
    payload: ProgressUpsert,
    service: ProgressServiceDep,
) -> ProgressOut:
    if payload.correct > payload.answered:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "correct cannot exceed answered")
    return service.upsert(payload)


@router.post("/progress/answer", response_model=ProgressOut)
def record_answer(
    payload: ProgressUpsert,
    service: ProgressServiceDep,
) -> ProgressOut:
    return service.record_answer(payload)


@router.get("/stats", response_model=StatsOut)
def get_stats(service: ProgressServiceDep) -> StatsOut:
    return service.stats()


@router.delete("/progress/reset", response_model=MessageOut)
def reset_progress(
    progress: ProgressServiceDep,
    wrong: WrongAnswerServiceDep,
    concepts: ConceptServiceDep,
) -> MessageOut:
    progress.delete_all()
    wrong.delete_all()
    concepts.reset_known()
    return MessageOut(message="progress reset")
