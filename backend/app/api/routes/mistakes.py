from fastapi import APIRouter, Depends, Query

from app.dependencies import get_auto_fix_service, get_mistake_service
from app.schemas.mistake import (
    CreateMistakeRequest,
    MistakeResponse,
    MistakeStatus,
    UpdateMistakeRequest,
)
from app.services.auto_fix_service import AutoFixService
from app.services.mistake_service import MistakeService

router = APIRouter(prefix="/mistakes", tags=["mistakes"])


@router.post("", response_model=MistakeResponse)
async def create_mistake(
    request: CreateMistakeRequest,
    mistake_service: MistakeService = Depends(get_mistake_service),
    auto_fix_service: AutoFixService = Depends(get_auto_fix_service),
) -> MistakeResponse:
    created = mistake_service.create_mistake(request)
    processed = auto_fix_service.process_mistake(created.id)
    return mistake_service.get_mistake(created.id) if processed is None else mistake_service.get_mistake(processed.id)


@router.get("", response_model=list[MistakeResponse])
async def list_mistakes(
    status: MistakeStatus | None = Query(default=None),
    mistake_service: MistakeService = Depends(get_mistake_service),
) -> list[MistakeResponse]:
    return mistake_service.list_mistakes(status=status)


@router.patch("/{mistake_id}", response_model=MistakeResponse)
async def update_mistake_status(
    mistake_id: int,
    request: UpdateMistakeRequest,
    mistake_service: MistakeService = Depends(get_mistake_service),
) -> MistakeResponse:
    return mistake_service.update_status(mistake_id, request.status)