import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Category

router = APIRouter(prefix="/api/categories", tags=["categories"])


def get_category_or_404(db: Session, category_id: str) -> Category:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return category


@router.get("", response_model=list[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return db.query(Category).order_by(Category.sort_order, Category.id).all()


@router.get("/{category_id}", response_model=schemas.CategoryOut)
def get_category(category_id: str, db: Session = Depends(get_db)) -> Category:
    return get_category_or_404(db, category_id)


@router.post("", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db)) -> Category:
    if db.get(Category, payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Category already exists")
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=schemas.CategoryOut)
def update_category(
    category_id: str, payload: schemas.CategoryUpdate, db: Session = Depends(get_db)
) -> Category:
    category = get_category_or_404(db, category_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, db: Session = Depends(get_db)) -> None:
    category = get_category_or_404(db, category_id)
    db.delete(category)
    db.commit()
