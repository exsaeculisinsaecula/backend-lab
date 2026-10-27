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
    WrongAnswer,
)
from app.schemas.study import (
    CategoryProgress,
    DashboardOut,
    TimelineItem,
    WeakArea,
)


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def category_progress(self) -> list[CategoryProgress]:
        rows = self.db.query(Category).order_by(Category.sort_order, Category.id).all()
        result: list[CategoryProgress] = []
        for cat in rows:
            total = self.db.query(Concept).filter(Concept.category_id == cat.id).count()
            known = (
                self.db.query(Concept)
                .filter(Concept.category_id == cat.id, Concept.is_known.is_(True))
                .count()
            )
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

    def weak_areas(self, limit: int = 5) -> list[WeakArea]:
        rows = self.db.query(Category).order_by(Category.sort_order).all()
        areas: list[WeakArea] = []
        for cat in rows:
            open_wrong = (
                self.db.query(WrongAnswer)
                .filter(
                    WrongAnswer.category_id == cat.id,
                    WrongAnswer.mastered.is_(False),
                )
                .count()
            )
            unknown = (
                self.db.query(Concept)
                .filter(Concept.category_id == cat.id, Concept.is_known.is_(False))
                .count()
            )
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

    def timeline(self, days: int = 14) -> list[TimelineItem]:
        rows = (
            self.db.query(StudyProgress)
            .order_by(StudyProgress.date.desc())
            .limit(days)
            .all()
        )
        return [
            TimelineItem(date=r.date, answered=r.answered, correct=r.correct)
            for r in reversed(rows)
        ]

    def today(self) -> TimelineItem:
        day = date_cls.today().isoformat()
        row = self.db.query(StudyProgress).filter(StudyProgress.date == day).first()
        if not row:
            return TimelineItem(date=day, answered=0, correct=0)
        return TimelineItem(date=row.date, answered=row.answered, correct=row.correct)

    def dashboard(self) -> DashboardOut:
        total_concepts = self.db.query(Concept).count()
        known_concepts = self.db.query(Concept).filter(Concept.is_known.is_(True)).count()
        total_quiz = self.db.query(QuizQuestion).count()
        open_wrong = self.db.query(WrongAnswer).filter(WrongAnswer.mastered.is_(False)).count()
        mastered_wrong = self.db.query(WrongAnswer).filter(WrongAnswer.mastered.is_(True)).count()

        answered = 0
        correct = 0
        for r in self.db.query(StudyProgress).all():
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
            study_sessions=self.db.query(StudySession).count(),
            quiz_sessions=self.db.query(QuizSession).count(),
            today=self.today(),
            categories=self.category_progress(),
            weak_areas=self.weak_areas(),
        )
