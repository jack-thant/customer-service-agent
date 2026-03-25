from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MistakeStatus(str, Enum):
    OPEN = "open"
    PATCHED = "patched"
    FIXED = "fixed"
    ARCHIVED = "archived"


class CreateMistakeRequest(BaseModel):
    user_query: str = Field(..., min_length=1)
    bot_answer: str = Field(..., min_length=1)
    feedback: str = Field(..., min_length=1, max_length=5000)
    route: str | None = None
    session_id: str | None = None


class UpdateMistakeRequest(BaseModel):
    status: MistakeStatus


class MistakeResponse(BaseModel):
    id: int
    user_query: str
    bot_answer: str
    feedback: str
    route: str | None = None
    session_id: str | None = None
    status: MistakeStatus
    root_cause: str | None = None
    suggested_fix: str | None = None
    applied_fix: str | None = None
    rerun_answer: str | None = None
    created_at: datetime
    updated_at: datetime