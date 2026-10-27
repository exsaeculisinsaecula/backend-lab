from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Concept, WrongAnswer
from app.schemas.study import ReviewCompleteIn, ReviewQueueItem


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def queue(self, *, limit: int = 30) -> list[ReviewQueueItem]:
        """오답(우선) + 모르는 개념을 복습 큐로 반환한다."""
        items: list[ReviewQueueItem] = []

        wrongs = (
            self.db.query(WrongAnswer)
            .filter(WrongAnswer.mastered.is_(False))
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
            concepts = (
                self.db.query(Concept)
                .filter(Concept.is_known.is_(False))
                .order_by(Concept.term)
                .limit(remaining)
                .all()
            )
            for c in concepts:
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

    def complete(self, payload: ReviewCompleteIn) -> bool:
        if payload.kind == "concept":
            concept = self.db.get(Concept, payload.id)
            if not concept:
                return False
            concept.is_known = payload.known
            self.db.commit()
            return True

        wrong = self.db.get(WrongAnswer, payload.id)
        if not wrong:
            return False
        wrong.mastered = payload.known
        self.db.commit()
        return True

    def stats(self) -> dict:
        open_wrong = self.db.query(WrongAnswer).filter(WrongAnswer.mastered.is_(False)).count()
        mastered = self.db.query(WrongAnswer).filter(WrongAnswer.mastered.is_(True)).count()
        unknown = self.db.query(Concept).filter(Concept.is_known.is_(False)).count()
        known = self.db.query(Concept).filter(Concept.is_known.is_(True)).count()
        return {
            "open_wrong": open_wrong,
            "mastered_wrong": mastered,
            "unknown_concepts": unknown,
            "known_concepts": known,
            "queue_size": open_wrong + unknown,
        }
