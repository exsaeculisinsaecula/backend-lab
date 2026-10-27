from fastapi import APIRouter, status

from app.deps import CurrentUser, TransferServiceDep
from app.schemas.study import ExportOut, ImportIn, ImportResult

router = APIRouter(prefix="/api/data", tags=["data-transfer"])


@router.get("/export", response_model=ExportOut)
def export_data(service: TransferServiceDep, user: CurrentUser) -> ExportOut:
    """로그인한 사용자의 학습 데이터를 JSON으로 내보냅니다."""
    return service.export(user)


@router.post("/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
def import_data(
    payload: ImportIn,
    service: TransferServiceDep,
    user: CurrentUser,
) -> ImportResult:
    return service.import_data(user, payload)
