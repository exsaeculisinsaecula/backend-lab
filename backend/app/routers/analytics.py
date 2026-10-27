from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import AnalyticsServiceDep, CurrentUser
from app.schemas.study import CategoryProgress, DashboardOut, TimelineItem, WeakArea

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(service: AnalyticsServiceDep, user: CurrentUser) -> DashboardOut:
    return service.dashboard(user)


@router.get("/categories", response_model=list[CategoryProgress])
def category_progress(
    service: AnalyticsServiceDep,
    user: CurrentUser,
) -> list[CategoryProgress]:
    return service.category_progress(user)


@router.get("/weak-areas", response_model=list[WeakArea])
def weak_areas(
    service: AnalyticsServiceDep,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> list[WeakArea]:
    return service.weak_areas(user, limit=limit)


@router.get("/timeline", response_model=list[TimelineItem])
def timeline(
    service: AnalyticsServiceDep,
    user: CurrentUser,
    days: Annotated[int, Query(ge=1, le=90)] = 14,
) -> list[TimelineItem]:
    return service.timeline(user, days=days)


@router.get("/today", response_model=TimelineItem)
def today(service: AnalyticsServiceDep, user: CurrentUser) -> TimelineItem:
    return service.today(user)
