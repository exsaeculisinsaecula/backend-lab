import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Category, Concept

router = APIRouter(prefix="/api/concepts", tags=["concepts"])


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


def get_concept_or_404(db: Session, concept_id: str) -> Concept:
    concept = db.get(Concept, concept_id)
    if not concept:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Concept not found")
    return concept


def ensure_category(db: Session, category_id: str) -> None:
    if not db.get(Category, category_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category_id: {category_id}")


@router.get("", response_model=list[schemas.ConceptOut])
def list_concepts(
    db: Session = Depends(get_db),
    category_id: str | None = Query(default=None),
    is_known: bool | None = Query(default=None),
    q: str | None = Query(default=None, description="term/definition 검색"),
) -> list[Concept]:
    query = db.query(Concept)
    if category_id:
        query = query.filter(Concept.category_id == category_id)
    if is_known is not None:
        query = query.filter(Concept.is_known == is_known)
    if q:
        like = f"%{q}%"
        query = query.filter((Concept.term.like(like)) | (Concept.definition.like(like)))
    return query.order_by(Concept.category_id, Concept.term).all()


@router.get("/{concept_id}", response_model=schemas.ConceptOut)
def get_concept(concept_id: str, db: Session = Depends(get_db)) -> Concept:
    return get_concept_or_404(db, concept_id)


@router.post("", response_model=schemas.ConceptOut, status_code=status.HTTP_201_CREATED)
def create_concept(payload: schemas.ConceptCreate, db: Session = Depends(get_db)) -> Concept:
    ensure_category(db, payload.category_id)
    data = payload.model_dump()
    concept_id = data.pop("id") or f"c-{slugify(payload.term)}-{uuid.uuid4().hex[:6]}"
    if db.get(Concept, concept_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Concept already exists")
    concept = Concept(id=concept_id, **data)
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return concept


@router.patch("/{concept_id}", response_model=schemas.ConceptOut)
def update_concept(
    concept_id: str, payload: schemas.ConceptUpdate, db: Session = Depends(get_db)
) -> Concept:
    concept = get_concept_or_404(db, concept_id)
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data:
        ensure_category(db, data["category_id"])
    for key, value in data.items():
        setattr(concept, key, value)
    db.commit()
    db.refresh(concept)
    return concept


@router.delete("/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept(concept_id: str, db: Session = Depends(get_db)) -> None:
    concept = get_concept_or_404(db, concept_id)
    db.delete(concept)
    db.commit()
