from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import CurrentUser, ReviewServiceDep
from app.schemas.common import MessageOut
from app.schemas.study import ReviewCompleteIn, ReviewQueueItem

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/queue", response_model=list[ReviewQueueItem])
def review_queue(
    service: ReviewServiceDep,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[ReviewQueueItem]:
    return service.queue(user, limit=limit)


@router.get("/stats")
def review_stats(service: ReviewServiceDep, user: CurrentUser) -> dict:
    return service.stats(user)


@router.post("/complete", response_model=MessageOut)
def complete_review(
    payload: ReviewCompleteIn,
    service: ReviewServiceDep,
    user: CurrentUser,
) -> MessageOut:
    ok = service.complete(user.id, payload)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review item not found")
    return MessageOut(
        message="ok",
        detail={"kind": payload.kind, "id": payload.id, "known": payload.known},
    )
