from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import SearchServiceDep
from app.schemas.study import SearchOut

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=SearchOut)
def search(
    service: SearchServiceDep,
    q: Annotated[str, Query(min_length=1, description="검색어")],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> SearchOut:
    """개념 · 퀴즈 · 오답노트를 한 번에 검색합니다."""
    return service.search(q, limit=limit)
