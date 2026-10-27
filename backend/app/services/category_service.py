from sqlalchemy.orm import Session

from app.models import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Category]:
        return self.db.query(Category).order_by(Category.sort_order, Category.id).all()

    def get(self, category_id: str) -> Category | None:
        return self.db.get(Category, category_id)

    def create(self, payload: CategoryCreate) -> Category:
        category = Category(**payload.model_dump())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category, payload: CategoryUpdate) -> Category:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()

    def exists(self, category_id: str) -> bool:
        return self.db.get(Category, category_id) is not None
