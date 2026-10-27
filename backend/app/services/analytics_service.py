from __future__ import annotations

from datetime import date as date_cls

from sqlalchemy.orm import Session

from app.models import (
    Category,
    Concept,
    QuizQuestion,
    QuizSession,
    StudyProgress,
    StudySession,
    User,
    UserConceptState,
    WrongAnswer,
)
from app.schemas.study import CategoryProgress, DashboardOut, TimelineItem, WeakArea


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _known_map(self, user_id: str) -> dict[str, bool]:
        rows = (
            self.db.query(UserConceptState)
            .filter(UserConceptState.user_id == user_id)
            .all()
        )
        return {r.concept_id: r.is_known for r in rows}

    def category_progress(self, user: User) -> list[CategoryProgress]:
        known_map = self._known_map(user.id)
        rows = self.db.query(Category).order_by(Category.sort_order, Category.id).all()
        result: list[CategoryProgress] = []
        for cat in rows:
            total = self.db.query(Concept).filter(Concept.category_id == cat.id).count()
            known = sum(1 for cid, k in known_map.items() if k and self._in_category(cid, cat.id))
            # 정확한 계산
            concept_ids = [
                c.id
                for c in self.db.query(Concept).filter(Concept.category_id == cat.id).all()
            ]
            known = sum(1 for cid in concept_ids if known_map.get(cid, False))
            percent = round(known / total * 100) if total else 0
            result.append(
                CategoryProgress(
                    category_id=cat.id,
                    name=cat.name,
                    icon=cat.icon,
                    total=total,
                    known=known,
                    percent=percent,
                )
            )
        return result

    def _in_category(self, concept_id: str, category_id: str) -> bool:
        c = self.db.get(Concept, concept_id)
        return bool(c and c.category_id == category_id)

    def weak_areas(self, user: User, limit: int = 5) -> list[WeakArea]:
        known_map = self._known_map(user.id)
        rows = self.db.query(Category).order_by(Category.sort_order).all()
        areas: list[WeakArea] = []
        for cat in rows:
            open_wrong = (
                self.db.query(WrongAnswer)
                .filter(
                    WrongAnswer.user_id == user.id,
                    WrongAnswer.category_id == cat.id,
                    WrongAnswer.mastered.is_(False),
                )
                .count()
            )
            concepts = self.db.query(Concept).filter(Concept.category_id == cat.id).all()
            unknown = sum(1 for c in concepts if not known_map.get(c.id, False))
            if open_wrong == 0 and unknown == 0:
                continue
            areas.append(
                WeakArea(
                    category_id=cat.id,
                    name=cat.name,
                    open_wrong=open_wrong,
                    unknown_concepts=unknown,
                    score=open_wrong * 2 + unknown,
                )
            )
        areas.sort(key=lambda a: a.score, reverse=True)
        return areas[:limit]

    def timeline(self, user: User, days: int = 14) -> list[TimelineItem]:
        rows = (
            self.db.query(StudyProgress)
            .filter(StudyProgress.user_id == user.id)
            .order_by(StudyProgress.date.desc())
            .limit(days)
            .all()
        )
        return [
            TimelineItem(date=r.date, answered=r.answered, correct=r.correct)
            for r in reversed(rows)
        ]

    def today(self, user: User) -> TimelineItem:
        day = date_cls.today().isoformat()
        row = (
            self.db.query(StudyProgress)
            .filter(StudyProgress.user_id == user.id, StudyProgress.date == day)
            .first()
        )
        if not row:
            return TimelineItem(date=day, answered=0, correct=0)
        return TimelineItem(date=row.date, answered=row.answered, correct=row.correct)

    def dashboard(self, user: User) -> DashboardOut:
        total_concepts = self.db.query(Concept).count()
        known_map = self._known_map(user.id)
        known_concepts = sum(1 for v in known_map.values() if v)
        total_quiz = self.db.query(QuizQuestion).count()
        open_wrong = (
            self.db.query(WrongAnswer)
            .filter(WrongAnswer.user_id == user.id, WrongAnswer.mastered.is_(False))
            .count()
        )
        mastered_wrong = (
            self.db.query(WrongAnswer)
            .filter(WrongAnswer.user_id == user.id, WrongAnswer.mastered.is_(True))
            .count()
        )

        answered = 0
        correct = 0
        for r in self.db.query(StudyProgress).filter(StudyProgress.user_id == user.id).all():
            answered += r.answered
            correct += r.correct

        return DashboardOut(
            total_concepts=total_concepts,
            known_concepts=known_concepts,
            known_percent=round(known_concepts / total_concepts * 100) if total_concepts else 0,
            total_quiz_questions=total_quiz,
            open_wrong=open_wrong,
            mastered_wrong=mastered_wrong,
            answered=answered,
            correct=correct,
            accuracy=round(correct / answered * 100, 2) if answered else None,
            study_sessions=self.db.query(StudySession)
            .filter(StudySession.user_id == user.id)
            .count(),
            quiz_sessions=self.db.query(QuizSession)
            .filter(QuizSession.user_id == user.id)
            .count(),
            today=self.today(user),
            categories=self.category_progress(user),
            weak_areas=self.weak_areas(user),
        )
