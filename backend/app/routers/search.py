from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import CurrentUser, SearchServiceDep
from app.schemas.study import SearchOut

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=SearchOut)
def search(
    service: SearchServiceDep,
    user: CurrentUser,
    q: Annotated[str, Query(min_length=1, description="검색어")],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> SearchOut:
    return service.search(user, q, limit=limit)
