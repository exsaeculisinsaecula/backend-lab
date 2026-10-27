from fastapi import APIRouter, HTTPException, status

from app.deps import CategoryOr404, CategoryServiceDep, CurrentUser
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    service: CategoryServiceDep,
    user: CurrentUser,
) -> list[CategoryOut]:
    return service.list()


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category: CategoryOr404, user: CurrentUser) -> CategoryOut:
    return category


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    service: CategoryServiceDep,
    user: CurrentUser,
) -> CategoryOut:
    if service.get(payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Category already exists")
    return service.create(payload)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    payload: CategoryUpdate,
    category: CategoryOr404,
    service: CategoryServiceDep,
    user: CurrentUser,
) -> CategoryOut:
    return service.update(category, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category: CategoryOr404,
    service: CategoryServiceDep,
    user: CurrentUser,
) -> None:
    service.delete(category)
