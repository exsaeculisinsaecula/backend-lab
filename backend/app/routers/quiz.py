import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Category, QuizQuestion

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


def get_quiz_or_404(db: Session, quiz_id: str) -> QuizQuestion:
    item = db.get(QuizQuestion, quiz_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz question not found")
    return item


def ensure_category(db: Session, category_id: str) -> None:
    if not db.get(Category, category_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category_id: {category_id}")


def to_out(row: QuizQuestion) -> schemas.QuizOut:
    return schemas.QuizOut(
        id=row.id,
        category_id=row.category_id,
        question=row.question,
        choices=json.loads(row.choices_json),
        correct_index=row.correct_index,
        explanation=row.explanation,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def validate_choices(choices: list[str], correct_index: int) -> None:
    if correct_index >= len(choices):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"correct_index {correct_index} is out of range for {len(choices)} choices",
        )


@router.get("", response_model=list[schemas.QuizOut])
def list_quiz_questions(
    db: Session = Depends(get_db),
    category_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> list[schemas.QuizOut]:
    query = db.query(QuizQuestion)
    if category_id:
        query = query.filter(QuizQuestion.category_id == category_id)
    if q:
        query = query.filter(QuizQuestion.question.like(f"%{q}%"))
    rows = query.order_by(QuizQuestion.category_id, QuizQuestion.id).all()
    return [to_out(r) for r in rows]


@router.get("/{quiz_id}", response_model=schemas.QuizOut)
def get_quiz_question(quiz_id: str, db: Session = Depends(get_db)) -> schemas.QuizOut:
    return to_out(get_quiz_or_404(db, quiz_id))


@router.post("", response_model=schemas.QuizOut, status_code=status.HTTP_201_CREATED)
def create_quiz_question(
    payload: schemas.QuizCreate, db: Session = Depends(get_db)
) -> schemas.QuizOut:
    ensure_category(db, payload.category_id)
    validate_choices(payload.choices, payload.correct_index)
    quiz_id = payload.id or f"q-{uuid.uuid4().hex[:10]}"
    if db.get(QuizQuestion, quiz_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Quiz question already exists")
    row = QuizQuestion(
        id=quiz_id,
        category_id=payload.category_id,
        question=payload.question,
        choices_json=json.dumps(payload.choices, ensure_ascii=False),
        correct_index=payload.correct_index,
        explanation=payload.explanation,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return to_out(row)


@router.patch("/{quiz_id}", response_model=schemas.QuizOut)
def update_quiz_question(
    quiz_id: str, payload: schemas.QuizUpdate, db: Session = Depends(get_db)
) -> schemas.QuizOut:
    row = get_quiz_or_404(db, quiz_id)
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data:
        ensure_category(db, data["category_id"])

    choices = data.pop("choices", None)
    correct_index = data.get("correct_index", row.correct_index)
    if choices is None:
        choices = json.loads(row.choices_json)
    validate_choices(choices, correct_index)

    if choices is not None:
        row.choices_json = json.dumps(choices, ensure_ascii=False)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return to_out(row)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz_question(quiz_id: str, db: Session = Depends(get_db)) -> None:
    row = get_quiz_or_404(db, quiz_id)
    db.delete(row)
    db.commit()
