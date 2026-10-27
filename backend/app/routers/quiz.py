from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import CategoryServiceDep, QuizOr404, QuizServiceDep
from app.schemas.quiz import QuizCreate, QuizOut, QuizUpdate

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


def ensure_choices(choices: list[str], correct_index: int) -> None:
    if correct_index >= len(choices):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"correct_index {correct_index} is out of range for {len(choices)} choices",
        )


@router.get("", response_model=list[QuizOut])
def list_quiz_questions(
    service: QuizServiceDep,
    category_id: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
) -> list[QuizOut]:
    rows = service.list(category_id=category_id, q=q)
    return [
        QuizOut(
            id=row.id,
            category_id=row.category_id,
            question=row.question,
            choices=service.to_choices(row),
            correct_index=row.correct_index,
            explanation=row.explanation,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz_question(row: QuizOr404, service: QuizServiceDep) -> QuizOut:
    return QuizOut(
        id=row.id,
        category_id=row.category_id,
        question=row.question,
        choices=service.to_choices(row),
        correct_index=row.correct_index,
        explanation=row.explanation,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post("", response_model=QuizOut, status_code=status.HTTP_201_CREATED)
def create_quiz_question(
    payload: QuizCreate,
    service: QuizServiceDep,
    category_service: CategoryServiceDep,
) -> QuizOut:
    if not category_service.exists(payload.category_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown category_id: {payload.category_id}")
    ensure_choices(payload.choices, payload.correct_index)
    if payload.id and service.exists(payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Quiz question already exists")
    row = service.create(payload)
    return QuizOut(
        id=row.id,
        category_id=row.category_id,
        question=row.question,
        choices=service.to_choices(row),
        correct_index=row.correct_index,
        explanation=row.explanation,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.patch("/{quiz_id}", response_model=QuizOut)
def update_quiz_question(
    payload: QuizUpdate,
    row: QuizOr404,
    service: QuizServiceDep,
    category_service: CategoryServiceDep,
) -> QuizOut:
    if payload.category_id is not None and not category_service.exists(payload.category_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown category_id: {payload.category_id}",
        )
    choices = payload.choices if payload.choices is not None else service.to_choices(row)
    correct_index = (
        payload.correct_index if payload.correct_index is not None else row.correct_index
    )
    ensure_choices(choices, correct_index)
    updated = service.update(row, payload)
    return QuizOut(
        id=updated.id,
        category_id=updated.category_id,
        question=updated.question,
        choices=service.to_choices(updated),
        correct_index=updated.correct_index,
        explanation=updated.explanation,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz_question(row: QuizOr404, service: QuizServiceDep) -> None:
    service.delete(row)
