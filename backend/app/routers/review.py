from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import ReviewServiceDep
from app.schemas.common import MessageOut
from app.schemas.study import ReviewCompleteIn, ReviewQueueItem

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/queue", response_model=list[ReviewQueueItem])
def review_queue(
    service: ReviewServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[ReviewQueueItem]:
    """오답(우선) + 모르는 개념으로 구성된 복습 큐를 반환합니다."""
    return service.queue(limit=limit)


@router.get("/stats")
def review_stats(service: ReviewServiceDep) -> dict:
    return service.stats()


@router.post("/complete", response_model=MessageOut)
def complete_review(payload: ReviewCompleteIn, service: ReviewServiceDep) -> MessageOut:
    ok = service.complete(payload)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review item not found")
    return MessageOut(
        message="ok",
        detail={"kind": payload.kind, "id": payload.id, "known": payload.known},
    )
