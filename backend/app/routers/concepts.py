from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import CategoryServiceDep, ConceptOr404, ConceptServiceDep
from app.schemas.concept import ConceptCreate, ConceptOut, ConceptUpdate

router = APIRouter(prefix="/api/concepts", tags=["concepts"])


@router.get("", response_model=list[ConceptOut])
def list_concepts(
    service: ConceptServiceDep,
    category_service: CategoryServiceDep,
    category_id: Annotated[str | None, Query()] = None,
    is_known: Annotated[bool | None, Query()] = None,
    q: Annotated[str | None, Query(description="term/definition 검색")] = None,
) -> list[ConceptOut]:
    if category_id and not category_service.exists(category_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category_id: {category_id}")
    return service.list(category_id=category_id, is_known=is_known, q=q)


@router.get("/{concept_id}", response_model=ConceptOut)
def get_concept(concept: ConceptOr404) -> ConceptOut:
    return concept


@router.post("", response_model=ConceptOut, status_code=status.HTTP_201_CREATED)
def create_concept(
    payload: ConceptCreate,
    service: ConceptServiceDep,
    category_service: CategoryServiceDep,
) -> ConceptOut:
    if not category_service.exists(payload.category_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category_id: {payload.category_id}")
    if payload.id and service.get(payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Concept already exists")
    return service.create(payload)


@router.patch("/{concept_id}", response_model=ConceptOut)
def update_concept(
    payload: ConceptUpdate,
    concept: ConceptOr404,
    service: ConceptServiceDep,
    category_service: CategoryServiceDep,
) -> ConceptOut:
    if payload.category_id is not None and not category_service.exists(payload.category_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown category_id: {payload.category_id}",
        )
    return service.update(concept, payload)


@router.delete("/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept(concept: ConceptOr404, service: ConceptServiceDep) -> None:
    service.delete(concept)
