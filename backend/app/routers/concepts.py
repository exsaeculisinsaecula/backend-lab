from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import (
    CategoryServiceDep,
    ConceptOr404,
    ConceptServiceDep,
    CurrentUser,
)
from app.schemas.concept import ConceptCreate, ConceptOut, ConceptUpdate

router = APIRouter(prefix="/api/concepts", tags=["concepts"])


@router.get("", response_model=list[ConceptOut])
def list_concepts(
    service: ConceptServiceDep,
    category_service: CategoryServiceDep,
    user: CurrentUser,
    category_id: Annotated[str | None, Query()] = None,
    is_known: Annotated[bool | None, Query()] = None,
    q: Annotated[str | None, Query(description="term/definition 검색")] = None,
) -> list[ConceptOut]:
    if category_id and not category_service.exists(category_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category_id: {category_id}")
    return service.list(user=user, category_id=category_id, is_known=is_known, q=q)


@router.get("/{concept_id}", response_model=ConceptOut)
def get_concept(
    concept: ConceptOr404,
    service: ConceptServiceDep,
    user: CurrentUser,
) -> ConceptOut:
    return service.to_out(concept, user)


@router.post("", response_model=ConceptOut, status_code=status.HTTP_201_CREATED)
def create_concept(
    payload: ConceptCreate,
    service: ConceptServiceDep,
    category_service: CategoryServiceDep,
    user: CurrentUser,
) -> ConceptOut:
    if not category_service.exists(payload.category_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category_id: {payload.category_id}")
    if payload.id and service.get(payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Concept already exists")
    return service.to_out(service.create(payload), user)


@router.patch("/{concept_id}", response_model=ConceptOut)
def update_concept(
    payload: ConceptUpdate,
    concept: ConceptOr404,
    service: ConceptServiceDep,
    category_service: CategoryServiceDep,
    user: CurrentUser,
) -> ConceptOut:
    if payload.category_id is not None and not category_service.exists(payload.category_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown category_id: {payload.category_id}",
        )
    return service.to_out(service.update(concept, payload), user)


@router.post("/{concept_id}/mark", response_model=ConceptOut)
def mark_concept(
    concept: ConceptOr404,
    service: ConceptServiceDep,
    user: CurrentUser,
    is_known: Annotated[bool, Query(description="외웠으면 true")],
) -> ConceptOut:
    """로그인한 사용자의 개념 암기 상태만 변경합니다."""
    service.set_known(user.id, concept.id, is_known)
    return service.to_out(concept, user)


@router.delete("/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept(
    concept: ConceptOr404,
    service: ConceptServiceDep,
    user: CurrentUser,
) -> None:
    service.delete(concept)
