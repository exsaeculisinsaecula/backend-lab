from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import AnalyticsServiceDep
from app.schemas.study import CategoryProgress, DashboardOut, TimelineItem, WeakArea

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(service: AnalyticsServiceDep) -> DashboardOut:
    """대시보드에 필요한 학습 현황을 한 번에 반환합니다."""
    return service.dashboard()


@router.get("/categories", response_model=list[CategoryProgress])
def category_progress(service: AnalyticsServiceDep) -> list[CategoryProgress]:
    return service.category_progress()


@router.get("/weak-areas", response_model=list[WeakArea])
def weak_areas(
    service: AnalyticsServiceDep,
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> list[WeakArea]:
    """오답·미암기 개념이 많은 취약 카테고리를 우선순위로 반환합니다."""
    return service.weak_areas(limit=limit)


@router.get("/timeline", response_model=list[TimelineItem])
def timeline(
    service: AnalyticsServiceDep,
    days: Annotated[int, Query(ge=1, le=90)] = 14,
) -> list[TimelineItem]:
    return service.timeline(days=days)


@router.get("/today", response_model=TimelineItem)
def today(service: AnalyticsServiceDep) -> TimelineItem:
    return service.today()
