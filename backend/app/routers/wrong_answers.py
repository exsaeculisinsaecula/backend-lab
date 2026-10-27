from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import WrongAnswerServiceDep, WrongOr404
from app.schemas.common import MessageOut
from app.schemas.wrong_answer import WrongAnswerCreate, WrongAnswerOut, WrongAnswerUpdate

router = APIRouter(prefix="/api/wrong-answers", tags=["wrong-answers"])


def to_out(row, service: WrongAnswerServiceDep) -> WrongAnswerOut:
    return WrongAnswerOut(
        id=row.id,
        source_id=row.source_id,
        category_id=row.category_id,
        question_type=row.question_type,
        question=row.question,
        choices=service.to_choices(row),
        correct_index=row.correct_index,
        my_index=row.my_index,
        explanation=row.explanation,
        mastered=row.mastered,
        count=row.count,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[WrongAnswerOut])
def list_wrong_answers(
    service: WrongAnswerServiceDep,
    mastered: Annotated[bool | None, Query()] = None,
    category_id: Annotated[str | None, Query()] = None,
) -> list[WrongAnswerOut]:
    return [to_out(row, service) for row in service.list(mastered=mastered, category_id=category_id)]


@router.get("/{wrong_id}", response_model=WrongAnswerOut)
def get_wrong_answer(row: WrongOr404, service: WrongAnswerServiceDep) -> WrongAnswerOut:
    return to_out(row, service)


@router.post("", response_model=WrongAnswerOut, status_code=status.HTTP_201_CREATED)
def create_wrong_answer(
    payload: WrongAnswerCreate,
    service: WrongAnswerServiceDep,
) -> WrongAnswerOut:
    if not service.validate_indexes(payload.choices, payload.correct_index, payload.my_index):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "index out of range")
    return to_out(service.create(payload), service)


@router.patch("/{wrong_id}", response_model=WrongAnswerOut)
def update_wrong_answer(
    payload: WrongAnswerUpdate,
    row: WrongOr404,
    service: WrongAnswerServiceDep,
) -> WrongAnswerOut:
    return to_out(service.update(row, payload), service)


@router.delete("/{wrong_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wrong_answer(row: WrongOr404, service: WrongAnswerServiceDep) -> None:
    service.delete(row)


@router.delete("", response_model=MessageOut)
def clear_mastered_wrong_answers(
    service: WrongAnswerServiceDep,
    mastered: Annotated[bool, Query(description="true면 정복 완료만 삭제")] = True,
) -> MessageOut:
    deleted = service.clear_by_mastered(mastered)
    return MessageOut(message="cleared", detail={"deleted": deleted})
