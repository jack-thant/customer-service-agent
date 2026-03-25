from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl

class BotConfig(BaseModel):
    kb_url: HttpUrl
    additional_guidelines: str = ""
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))

class UpdateConfigRequest(BaseModel):
    kb_url: HttpUrl
    additional_guidelines: str = Field(
        default="",
        description="Additional guidelines for the bot's behavior",
        max_length=10000,
    )

class ReingestConfigRequest(BaseModel):
    force_reingest: bool = Field(
        default=False,
        description="Whether to force re-ingestion of the knowledge base",
    )

class ReingestConfigResponse(BaseModel):
    message: str
    kb_url: HttpUrl
    force_reingest: bool
    articles_ingested: int | None = None