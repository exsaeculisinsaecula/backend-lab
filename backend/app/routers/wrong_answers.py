import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import WrongAnswer

router = APIRouter(prefix="/api/wrong-answers", tags=["wrong-answers"])


def get_wrong_or_404(db: Session, wrong_id: str) -> WrongAnswer:
    item = db.get(WrongAnswer, wrong_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Wrong answer not found")
    return item


def to_out(row: WrongAnswer) -> schemas.WrongAnswerOut:
    return schemas.WrongAnswerOut(
        id=row.id,
        source_id=row.source_id,
        category_id=row.category_id,
        question_type=row.question_type,
        question=row.question,
        choices=json.loads(row.choices_json),
        correct_index=row.correct_index,
        my_index=row.my_index,
        explanation=row.explanation,
        mastered=row.mastered,
        count=row.count,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[schemas.WrongAnswerOut])
def list_wrong_answers(
    db: Session = Depends(get_db),
    mastered: bool | None = Query(default=None),
    category_id: str | None = Query(default=None),
) -> list[schemas.WrongAnswerOut]:
    query = db.query(WrongAnswer)
    if mastered is not None:
        query = query.filter(WrongAnswer.mastered == mastered)
    if category_id:
        query = query.filter(WrongAnswer.category_id == category_id)
    rows = query.order_by(WrongAnswer.updated_at.desc()).all()
    return [to_out(r) for r in rows]


@router.get("/{wrong_id}", response_model=schemas.WrongAnswerOut)
def get_wrong_answer(wrong_id: str, db: Session = Depends(get_db)) -> schemas.WrongAnswerOut:
    return to_out(get_wrong_or_404(db, wrong_id))


@router.post("", response_model=schemas.WrongAnswerOut, status_code=status.HTTP_201_CREATED)
def create_wrong_answer(
    payload: schemas.WrongAnswerCreate, db: Session = Depends(get_db)
) -> schemas.WrongAnswerOut:
    if payload.correct_index >= len(payload.choices):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "correct_index out of range")
    if payload.my_index >= len(payload.choices):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "my_index out of range")

    existing = (
        db.query(WrongAnswer)
        .filter(
            WrongAnswer.source_id == payload.source_id,
            WrongAnswer.question == payload.question,
        )
        .first()
    )
    if existing:
        existing.my_index = payload.my_index
        existing.mastered = False
        existing.count = (existing.count or 1) + 1
        db.commit()
        db.refresh(existing)
        return to_out(existing)

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
    db.add(row)
    db.commit()
    db.refresh(row)
    return to_out(row)


@router.patch("/{wrong_id}", response_model=schemas.WrongAnswerOut)
def update_wrong_answer(
    wrong_id: str, payload: schemas.WrongAnswerUpdate, db: Session = Depends(get_db)
) -> schemas.WrongAnswerOut:
    row = get_wrong_or_404(db, wrong_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return to_out(row)


@router.delete("/{wrong_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wrong_answer(wrong_id: str, db: Session = Depends(get_db)) -> None:
    row = get_wrong_or_404(db, wrong_id)
    db.delete(row)
    db.commit()


@router.delete("", response_model=schemas.MessageOut)
def clear_mastered_wrong_answers(
    mastered: bool = Query(default=True, description="true면 정복 완료만 삭제"),
    db: Session = Depends(get_db),
) -> schemas.MessageOut:
    query = db.query(WrongAnswer).filter(WrongAnswer.mastered.is_(mastered))
    count = query.count()
    query.delete(synchronize_session=False)
    db.commit()
    return schemas.MessageOut(message="cleared", detail={"deleted": count})
