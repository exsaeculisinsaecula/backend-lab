from __future__ import annotations

from datetime import date as date_cls

from sqlalchemy.orm import Session

from app.models import Concept, QuizQuestion, QuizSession, StudyProgress, StudySession, User, WrongAnswer
from app.schemas.progress import ProgressUpsert, StatsOut


class ProgressService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, user: User) -> list[StudyProgress]:
        return (
            self.db.query(StudyProgress)
            .filter(StudyProgress.user_id == user.id)
            .order_by(StudyProgress.date.desc())
            .all()
        )

    def get_by_date(self, user_id: str, date: str) -> StudyProgress | None:
        return (
            self.db.query(StudyProgress)
            .filter(StudyProgress.user_id == user_id, StudyProgress.date == date)
            .first()
        )

    def upsert(self, user_id: str, payload: ProgressUpsert) -> StudyProgress:
        row = self.get_by_date(user_id, payload.date)
        if row:
            row.answered = payload.answered
            row.correct = payload.correct
        else:
            row = StudyProgress(
                user_id=user_id,
                date=payload.date,
                answered=payload.answered,
                correct=payload.correct,
            )
            self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def record_answer(self, user_id: str, payload: ProgressUpsert) -> StudyProgress:
        row = self.get_by_date(user_id, payload.date)
        if not row:
            row = StudyProgress(user_id=user_id, date=payload.date, answered=0, correct=0)
            self.db.add(row)
        row.answered += 1
        if payload.correct > 0:
            row.correct += 1
        self.db.commit()
        self.db.refresh(row)
        return row

    def stats(self, user: User) -> StatsOut:
        from app.services.concept_service import ConceptService

        concept_svc = ConceptService(self.db)
        total_concepts = self.db.query(Concept).count()
        known_concepts = concept_svc.known_count(user.id)
        total_quiz = self.db.query(QuizQuestion).count()
        total_wrong = self.db.query(WrongAnswer).filter(WrongAnswer.user_id == user.id).count()
        open_wrong = (
            self.db.query(WrongAnswer)
            .filter(
                WrongAnswer.user_id == user.id,
                WrongAnswer.mastered.is_(False),
            )
            .count()
        )

        answered = 0
        correct = 0
        for row in self.db.query(StudyProgress).filter(StudyProgress.user_id == user.id).all():
            answered += row.answered
            correct += row.correct

        return StatsOut(
            total_concepts=total_concepts,
            known_concepts=known_concepts,
            total_quiz_questions=total_quiz,
            total_wrong=total_wrong,
            open_wrong=open_wrong,
            answered=answered,
            correct=correct,
            accuracy=round(correct / answered * 100, 2) if answered else None,
        )

    def delete_all(self, user_id: str) -> int:
        count = (
            self.db.query(StudyProgress)
            .filter(StudyProgress.user_id == user_id)
            .delete()
        )
        self.db.commit()
        return count
