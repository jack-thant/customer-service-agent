from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class SourceItem(BaseModel):
    title: str | None = None
    url: str | None = None
    snippet: str | None = None


class ChatResponse(BaseModel):
    answer: str
    route: str
    sources: list[SourceItem] = []
    requires_followup: bool = False
    followup_field: str | None = None