from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Concept, User, UserConceptState, WrongAnswer
from app.schemas.study import ReviewCompleteIn, ReviewQueueItem


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _known_map(self, user_id: str) -> dict[str, bool]:
        rows = (
            self.db.query(UserConceptState)
            .filter(UserConceptState.user_id == user_id)
            .all()
        )
        return {r.concept_id: r.is_known for r in rows}

    def queue(self, user: User, *, limit: int = 30) -> list[ReviewQueueItem]:
        items: list[ReviewQueueItem] = []

        wrongs = (
            self.db.query(WrongAnswer)
            .filter(
                WrongAnswer.user_id == user.id,
                WrongAnswer.mastered.is_(False),
            )
            .order_by(WrongAnswer.count.desc(), WrongAnswer.updated_at.desc())
            .limit(limit)
            .all()
        )
        for w in wrongs:
            items.append(
                ReviewQueueItem(
                    kind="wrong",
                    id=w.id,
                    title=w.question[:80],
                    description=w.explanation or "오답노트 항목",
                    category_id=w.category_id,
                    priority=100 + (w.count or 1),
                )
            )

        remaining = max(0, limit - len(items))
        if remaining:
            known_map = self._known_map(user.id)
            concepts = self.db.query(Concept).order_by(Concept.term).all()
            unknown = [c for c in concepts if not known_map.get(c.id, False)]
            for c in unknown[:remaining]:
                items.append(
                    ReviewQueueItem(
                        kind="concept",
                        id=c.id,
                        title=c.term,
                        description=c.definition,
                        category_id=c.category_id,
                        priority=50,
                    )
                )

        items.sort(key=lambda x: x.priority, reverse=True)
        return items[:limit]

    def complete(self, user_id: str, payload: ReviewCompleteIn) -> bool:
        if payload.kind == "concept":
            concept = self.db.get(Concept, payload.id)
            if not concept:
                return False
            row = (
                self.db.query(UserConceptState)
                .filter(
                    UserConceptState.user_id == user_id,
                    UserConceptState.concept_id == payload.id,
                )
                .first()
            )
            if row:
                row.is_known = payload.known
            else:
                self.db.add(
                    UserConceptState(
                        user_id=user_id,
                        concept_id=payload.id,
                        is_known=payload.known,
                    )
                )
            self.db.commit()
            return True

        wrong = self.db.get(WrongAnswer, payload.id)
        if not wrong or wrong.user_id != user_id:
            return False
        wrong.mastered = payload.known
        self.db.commit()
        return True

    def stats(self, user: User) -> dict:
        open_wrong = (
            self.db.query(WrongAnswer)
            .filter(
                WrongAnswer.user_id == user.id,
                WrongAnswer.mastered.is_(False),
            )
            .count()
        )
        mastered = (
            self.db.query(WrongAnswer)
            .filter(
                WrongAnswer.user_id == user.id,
                WrongAnswer.mastered.is_(True),
            )
            .count()
        )
        known_map = self._known_map(user.id)
        unknown = sum(1 for v in known_map.values() if not v)
        known = sum(1 for v in known_map.values() if v)
        return {
            "open_wrong": open_wrong,
            "mastered_wrong": mastered,
            "unknown_concepts": unknown,
            "known_concepts": known,
            "queue_size": open_wrong + unknown,
        }
