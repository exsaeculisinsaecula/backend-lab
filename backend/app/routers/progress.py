from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Concept, QuizQuestion, StudyProgress, WrongAnswer

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/progress", response_model=list[schemas.ProgressOut])
def list_progress(db: Session = Depends(get_db)) -> list[StudyProgress]:
    return db.query(StudyProgress).order_by(StudyProgress.date.desc()).all()


@router.put("/progress", response_model=schemas.ProgressOut)
def upsert_progress(payload: schemas.ProgressUpsert, db: Session = Depends(get_db)) -> StudyProgress:
    if payload.correct > payload.answered:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "correct cannot exceed answered")
    row = db.query(StudyProgress).filter(StudyProgress.date == payload.date).first()
    if row:
        row.answered = payload.answered
        row.correct = payload.correct
    else:
        row = StudyProgress(
            date=payload.date,
            answered=payload.answered,
            correct=payload.correct,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/progress/answer", response_model=schemas.ProgressOut)
def record_answer(
    payload: schemas.ProgressUpsert,
    db: Session = Depends(get_db),
) -> StudyProgress:
    """오늘 날짜 기준으로 문항 1건을 누적합니다. date는 선택적으로 덮어쓰기용입니다."""
    row = db.query(StudyProgress).filter(StudyProgress.date == payload.date).first()
    if not row:
        row = StudyProgress(date=payload.date, answered=0, correct=0)
        db.add(row)
    row.answered += 1
    if payload.correct > 0:
        row.correct += 1
    db.commit()
    db.refresh(row)
    return row


@router.get("/stats", response_model=schemas.StatsOut)
def get_stats(db: Session = Depends(get_db)) -> schemas.StatsOut:
    total_concepts = db.query(Concept).count()
    known_concepts = db.query(Concept).filter(Concept.is_known.is_(True)).count()
    total_quiz = db.query(QuizQuestion).count()
    total_wrong = db.query(WrongAnswer).count()
    open_wrong = db.query(WrongAnswer).filter(WrongAnswer.mastered.is_(False)).count()

    answered = 0
    correct = 0
    for row in db.query(StudyProgress).all():
        answered += row.answered
        correct += row.correct

    accuracy = round(correct / answered * 100, 2) if answered else None
    return schemas.StatsOut(
        total_concepts=total_concepts,
        known_concepts=known_concepts,
        total_quiz_questions=total_quiz,
        total_wrong=total_wrong,
        open_wrong=open_wrong,
        answered=answered,
        correct=correct,
        accuracy=accuracy,
    )


@router.delete("/progress/reset", response_model=schemas.MessageOut)
def reset_progress(db: Session = Depends(get_db)) -> schemas.MessageOut:
    """암기 상태·오답·진도를 초기화합니다(카테고리/개념/퀴즈 데이터는 유지)."""
    db.query(StudyProgress).delete()
    db.query(WrongAnswer).delete()
    db.query(Concept).update({Concept.is_known: False})
    db.commit()
    return schemas.MessageOut(message="progress reset")
