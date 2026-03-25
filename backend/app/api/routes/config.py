from fastapi import APIRouter, Depends

from app.dependencies import get_config_service, get_ingest_service
from app.schemas.config import (
    BotConfig,
    ReingestConfigRequest,
    ReingestConfigResponse,
    UpdateConfigRequest,
)
from app.services.config_service import ConfigService
from app.services.ingest_service import KBIngestService

router = APIRouter(prefix="/config", tags=["config"])

@router.get("", response_model=BotConfig)
async def get_config(
    config_service: ConfigService = Depends(get_config_service),
) -> BotConfig:
    return config_service.get_current_config()

@router.put("", response_model=BotConfig)
async def update_config(
    request: UpdateConfigRequest,
    config_service: ConfigService = Depends(get_config_service),
) -> BotConfig:
    return config_service.update_config(request)

@router.post("/reingest", response_model=ReingestConfigResponse)
async def reingest_from_config(
    request: ReingestConfigRequest,
    config_service: ConfigService = Depends(get_config_service),
    ingest_service: KBIngestService = Depends(get_ingest_service),
) -> ReingestConfigResponse:
    config = config_service.get_current_config()

    result = ingest_service.ingest_category(
        category_url=str(config.kb_url),
        force_reingest=request.force_reingest,
    )

    return ReingestConfigResponse(
        message="Re-ingestion completed successfully.",
        kb_url=config.kb_url,
        force_reingest=request.force_reingest,
        articles_ingested=result.get("articles_ingested"),
    )