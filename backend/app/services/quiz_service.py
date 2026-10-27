import json
import uuid

from sqlalchemy.orm import Session

from app.models import QuizQuestion
from app.schemas.quiz import QuizCreate, QuizUpdate


class QuizService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def to_choices(row: QuizQuestion) -> list[str]:
        return json.loads(row.choices_json)

    @staticmethod
    def validate_choices(choices: list[str], correct_index: int) -> bool:
        return 0 <= correct_index < len(choices)

    def list(self, *, category_id: str | None = None, q: str | None = None) -> list[QuizQuestion]:
        query = self.db.query(QuizQuestion)
        if category_id:
            query = query.filter(QuizQuestion.category_id == category_id)
        if q:
            query = query.filter(QuizQuestion.question.like(f"%{q}%"))
        return query.order_by(QuizQuestion.category_id, QuizQuestion.id).all()

    def get(self, quiz_id: str) -> QuizQuestion | None:
        return self.db.get(QuizQuestion, quiz_id)

    def create(self, payload: QuizCreate) -> QuizQuestion:
        row = QuizQuestion(
            id=payload.id or f"q-{uuid.uuid4().hex[:10]}",
            category_id=payload.category_id,
            question=payload.question,
            choices_json=json.dumps(payload.choices, ensure_ascii=False),
            correct_index=payload.correct_index,
            explanation=payload.explanation,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: QuizQuestion, payload: QuizUpdate) -> QuizQuestion:
        data = payload.model_dump(exclude_unset=True)
        choices = data.pop("choices", None)
        correct_index = data.get("correct_index", row.correct_index)
        if choices is None:
            choices = self.to_choices(row)
        row.choices_json = json.dumps(choices, ensure_ascii=False)
        for key, value in data.items():
            setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return row

    def delete(self, row: QuizQuestion) -> None:
        self.db.delete(row)
        self.db.commit()

    def exists(self, quiz_id: str) -> bool:
        return self.get(quiz_id) is not None
