from fastapi import APIRouter, status

from app.deps import TransferServiceDep
from app.schemas.study import ExportOut, ImportIn, ImportResult

router = APIRouter(prefix="/api/data", tags=["data-transfer"])


@router.get("/export", response_model=ExportOut)
def export_data(service: TransferServiceDep) -> ExportOut:
    """전체 학습 데이터를 JSON으로 내보냅니다(백업)."""
    return service.export()


@router.post("/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
def import_data(payload: ImportIn, service: TransferServiceDep) -> ImportResult:
    """JSON 백업을 가져옵니다. 기존 ID가 있으면 건너뜁니다."""
    return service.import_data(payload)
