import re
import uuid

from sqlalchemy.orm import Session

from app.models import Concept
from app.schemas.concept import ConceptCreate, ConceptUpdate


class ConceptService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def generate_id(term: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-") or uuid.uuid4().hex[:8]
        return f"c-{slug}-{uuid.uuid4().hex[:6]}"

    def list(
        self,
        *,
        category_id: str | None = None,
        is_known: bool | None = None,
        q: str | None = None,
    ) -> list[Concept]:
        query = self.db.query(Concept)
        if category_id:
            query = query.filter(Concept.category_id == category_id)
        if is_known is not None:
            query = query.filter(Concept.is_known == is_known)
        if q:
            like = f"%{q}%"
            query = query.filter((Concept.term.like(like)) | (Concept.definition.like(like)))
        return query.order_by(Concept.category_id, Concept.term).all()

    def get(self, concept_id: str) -> Concept | None:
        return self.db.get(Concept, concept_id)

    def create(self, payload: ConceptCreate) -> Concept:
        data = payload.model_dump()
        concept_id = data.pop("id") or self.generate_id(payload.term)
        concept = Concept(id=concept_id, **data)
        self.db.add(concept)
        self.db.commit()
        self.db.refresh(concept)
        return concept

    def update(self, concept: Concept, payload: ConceptUpdate) -> Concept:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(concept, key, value)
        self.db.commit()
        self.db.refresh(concept)
        return concept

    def delete(self, concept: Concept) -> None:
        self.db.delete(concept)
        self.db.commit()

    def reset_known(self) -> int:
        count = self.db.query(Concept).filter(Concept.is_known.is_(True)).update(
            {Concept.is_known: False}
        )
        self.db.commit()
        return count
