from __future__ import annotations

import re
import uuid

from sqlalchemy.orm import Session

from app.models import Concept, User, UserConceptState
from app.schemas.concept import ConceptCreate, ConceptOut, ConceptUpdate


class ConceptService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def generate_id(term: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-") or uuid.uuid4().hex[:8]
        return f"c-{slug}-{uuid.uuid4().hex[:6]}"

    def _known_map(self, user: User | None) -> dict[str, bool]:
        if not user:
            return {}
        rows = (
            self.db.query(UserConceptState)
            .filter(UserConceptState.user_id == user.id)
            .all()
        )
        return {r.concept_id: r.is_known for r in rows}

    def to_out(self, concept: Concept, user: User | None = None) -> ConceptOut:
        known = self._known_map(user).get(concept.id, False) if user else False
        return ConceptOut(
            id=concept.id,
            category_id=concept.category_id,
            term=concept.term,
            definition=concept.definition,
            example=concept.example,
            is_known=known,
            created_at=concept.created_at,
            updated_at=concept.updated_at,
        )

    def list(
        self,
        *,
        user: User | None = None,
        category_id: str | None = None,
        is_known: bool | None = None,
        q: str | None = None,
    ) -> list[ConceptOut]:
        query = self.db.query(Concept)
        if category_id:
            query = query.filter(Concept.category_id == category_id)
        if q:
            like = f"%{q}%"
            query = query.filter((Concept.term.like(like)) | (Concept.definition.like(like)))
        concepts = query.order_by(Concept.category_id, Concept.term).all()
        known_map = self._known_map(user)
        results = []
        for c in concepts:
            known = known_map.get(c.id, False)
            if is_known is not None and known != is_known:
                continue
            results.append(self.to_out(c, user))
        return results

    def get(self, concept_id: str) -> Concept | None:
        return self.db.get(Concept, concept_id)

    def get_raw_list(self, *, user: User | None = None, category_id: str | None = None) -> list[Concept]:
        query = self.db.query(Concept)
        if category_id:
            query = query.filter(Concept.category_id == category_id)
        return query.order_by(Concept.term).all()

    def is_known(self, user_id: str, concept_id: str) -> bool:
        row = (
            self.db.query(UserConceptState)
            .filter(
                UserConceptState.user_id == user_id,
                UserConceptState.concept_id == concept_id,
            )
            .first()
        )
        return bool(row.is_known) if row else False

    def set_known(self, user_id: str, concept_id: str, is_known: bool) -> None:
        row = (
            self.db.query(UserConceptState)
            .filter(
                UserConceptState.user_id == user_id,
                UserConceptState.concept_id == concept_id,
            )
            .first()
        )
        if row:
            row.is_known = is_known
        else:
            self.db.add(
                UserConceptState(
                    user_id=user_id,
                    concept_id=concept_id,
                    is_known=is_known,
                )
            )
        self.db.commit()

    def create(self, payload: ConceptCreate) -> Concept:
        data = payload.model_dump()
        concept_id = data.pop("id") or self.generate_id(payload.term)
        data.pop("is_known", None)
        concept = Concept(id=concept_id, **data)
        self.db.add(concept)
        self.db.commit()
        self.db.refresh(concept)
        return concept

    def update(self, concept: Concept, payload: ConceptUpdate) -> Concept:
        data = payload.model_dump(exclude_unset=True)
        data.pop("is_known", None)  # 암기 상태는 UserConceptState에서 관리
        for key, value in data.items():
            setattr(concept, key, value)
        self.db.commit()
        self.db.refresh(concept)
        return concept

    def delete(self, concept: Concept) -> None:
        self.db.delete(concept)
        self.db.commit()

    def reset_known(self, user_id: str) -> int:
        count = (
            self.db.query(UserConceptState)
            .filter(UserConceptState.user_id == user_id)
            .update({UserConceptState.is_known: False})
        )
        self.db.commit()
        return count

    def known_count(self, user_id: str) -> int:
        return (
            self.db.query(UserConceptState)
            .filter(
                UserConceptState.user_id == user_id,
                UserConceptState.is_known.is_(True),
            )
            .count()
        )
