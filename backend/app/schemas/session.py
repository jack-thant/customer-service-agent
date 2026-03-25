from pydantic import BaseModel, Field


class SessionState(BaseModel):
    session_id: str
    pending_intent: str | None = None
    awaiting_field: str | None = None
    context: dict = Field(default_factory=dict)