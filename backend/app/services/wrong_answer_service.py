import json
import uuid

from sqlalchemy.orm import Session

from app.models import WrongAnswer
from app.schemas.wrong_answer import WrongAnswerCreate, WrongAnswerUpdate


class WrongAnswerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def to_choices(row: WrongAnswer) -> list[str]:
        return json.loads(row.choices_json)

    @staticmethod
    def validate_indexes(choices: list[str], correct_index: int, my_index: int) -> bool:
        return correct_index < len(choices) and my_index < len(choices)

    def list(
        self,
        *,
        mastered: bool | None = None,
        category_id: str | None = None,
    ) -> list[WrongAnswer]:
        query = self.db.query(WrongAnswer)
        if mastered is not None:
            query = query.filter(WrongAnswer.mastered == mastered)
        if category_id:
            query = query.filter(WrongAnswer.category_id == category_id)
        return query.order_by(WrongAnswer.updated_at.desc()).all()

    def get(self, wrong_id: str) -> WrongAnswer | None:
        return self.db.get(WrongAnswer, wrong_id)

    def find_duplicate(self, source_id: str, question: str) -> WrongAnswer | None:
        return (
            self.db.query(WrongAnswer)
            .filter(
                WrongAnswer.source_id == source_id,
                WrongAnswer.question == question,
            )
            .first()
        )

    def create(self, payload: WrongAnswerCreate) -> WrongAnswer:
        existing = self.find_duplicate(payload.source_id, payload.question)
        if existing:
            existing.my_index = payload.my_index
            existing.mastered = False
            existing.count = (existing.count or 1) + 1
            self.db.commit()
            self.db.refresh(existing)
            return existing

        row = WrongAnswer(
            id=f"w-{uuid.uuid4().hex[:12]}",
            source_id=payload.source_id,
            category_id=payload.category_id,
            question_type=payload.question_type,
            question=payload.question,
            choices_json=json.dumps(payload.choices, ensure_ascii=False),
            correct_index=payload.correct_index,
            my_index=payload.my_index,
            explanation=payload.explanation,
            mastered=payload.mastered,
            count=payload.count,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: WrongAnswer, payload: WrongAnswerUpdate) -> WrongAnswer:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: WrongAnswer) -> None:
        self.db.delete(row)
        self.db.commit()

    def clear_by_mastered(self, mastered: bool = True) -> int:
        query = self.db.query(WrongAnswer).filter(WrongAnswer.mastered.is_(mastered))
        count = query.count()
        query.delete(synchronize_session=False)
        self.db.commit()
        return count

    def delete_all(self) -> int:
        count = self.db.query(WrongAnswer).count()
        self.db.query(WrongAnswer).delete()
        self.db.commit()
        return count
