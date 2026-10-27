from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Category, Concept, QuizQuestion, StudyProgress, User, UserConceptState, WrongAnswer
from app.schemas.study import ExportOut, ImportIn, ImportResult


class TransferService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def export(self, user: User) -> ExportOut:
        categories = [
            {
                "id": c.id,
                "name": c.name,
                "icon": c.icon,
                "sort_order": c.sort_order,
            }
            for c in self.db.query(Category).order_by(Category.sort_order).all()
        ]

        known_map = {
            r.concept_id: r.is_known
            for r in self.db.query(UserConceptState)
            .filter(UserConceptState.user_id == user.id)
            .all()
        }
        concepts = [
            {
                "id": c.id,
                "category_id": c.category_id,
                "term": c.term,
                "definition": c.definition,
                "example": c.example,
                "is_known": known_map.get(c.id, False),
            }
            for c in self.db.query(Concept).all()
        ]
        quiz_questions = [
            {
                "id": q.id,
                "category_id": q.category_id,
                "question": q.question,
                "choices": json.loads(q.choices_json),
                "correct_index": q.correct_index,
                "explanation": q.explanation,
            }
            for q in self.db.query(QuizQuestion).all()
        ]
        wrong_answers = [
            {
                "id": w.id,
                "source_id": w.source_id,
                "category_id": w.category_id,
                "question_type": w.question_type,
                "question": w.question,
                "choices": json.loads(w.choices_json),
                "correct_index": w.correct_index,
                "my_index": w.my_index,
                "explanation": w.explanation,
                "mastered": w.mastered,
                "count": w.count,
            }
            for w in self.db.query(WrongAnswer)
            .filter(WrongAnswer.user_id == user.id)
            .all()
        ]
        progress = [
            {
                "date": p.date,
                "answered": p.answered,
                "correct": p.correct,
            }
            for p in self.db.query(StudyProgress)
            .filter(StudyProgress.user_id == user.id)
            .all()
        ]

        return ExportOut(
            exported_at=datetime.now(timezone.utc),
            categories=categories,
            concepts=concepts,
            quiz_questions=quiz_questions,
            wrong_answers=wrong_answers,
            progress=progress,
        )

    def import_data(self, user: User, payload: ImportIn) -> ImportResult:
        counts = {
            "categories": 0,
            "concepts": 0,
            "quiz_questions": 0,
            "wrong_answers": 0,
            "progress": 0,
        }
        skipped = 0

        for item in payload.categories:
            if self.db.get(Category, item.get("id")):
                skipped += 1
                continue
            self.db.add(
                Category(
                    id=item["id"],
                    name=item["name"],
                    icon=item.get("icon", ""),
                    sort_order=int(item.get("sort_order", 0)),
                )
            )
            counts["categories"] += 1

        known_flags: list[tuple[str, bool]] = []
        for item in payload.concepts:
            if self.db.get(Concept, item.get("id")):
                skipped += 1
                continue
            self.db.add(
                Concept(
                    id=item["id"],
                    category_id=item["category_id"],
                    term=item["term"],
                    definition=item["definition"],
                    example=item.get("example", ""),
                )
            )
            if item.get("is_known"):
                known_flags.append((item["id"], True))
            counts["concepts"] += 1

        for item in payload.quiz_questions:
            if self.db.get(QuizQuestion, item.get("id")):
                skipped += 1
                continue
            self.db.add(
                QuizQuestion(
                    id=item["id"],
                    category_id=item["category_id"],
                    question=item["question"],
                    choices_json=json.dumps(item["choices"], ensure_ascii=False),
                    correct_index=int(item["correct_index"]),
                    explanation=item.get("explanation", ""),
                )
            )
            counts["quiz_questions"] += 1

        for item in payload.wrong_answers:
            if self.db.get(WrongAnswer, item.get("id")):
                skipped += 1
                continue
            self.db.add(
                WrongAnswer(
                    id=item["id"],
                    user_id=user.id,
                    source_id=item.get("source_id", ""),
                    category_id=item.get("category_id", ""),
                    question_type=item.get("question_type", ""),
                    question=item["question"],
                    choices_json=json.dumps(item["choices"], ensure_ascii=False),
                    correct_index=int(item["correct_index"]),
                    my_index=int(item.get("my_index", 0)),
                    explanation=item.get("explanation", ""),
                    mastered=bool(item.get("mastered", False)),
                    count=int(item.get("count", 1)),
                )
            )
            counts["wrong_answers"] += 1

        for item in payload.progress:
            existing = (
                self.db.query(StudyProgress)
                .filter(
                    StudyProgress.user_id == user.id,
                    StudyProgress.date == item.get("date"),
                )
                .first()
            )
            if existing:
                skipped += 1
                continue
            self.db.add(
                StudyProgress(
                    user_id=user.id,
                    date=item["date"],
                    answered=int(item.get("answered", 0)),
                    correct=int(item.get("correct", 0)),
                )
            )
            counts["progress"] += 1

        for concept_id, is_known in known_flags:
            self.db.add(
                UserConceptState(
                    user_id=user.id,
                    concept_id=concept_id,
                    is_known=is_known,
                )
            )

        self.db.commit()
        return ImportResult(**counts, skipped=skipped)
