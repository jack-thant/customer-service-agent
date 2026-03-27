from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AgentSpecStatus(str, Enum):
    DRAFT = "draft"
    BUILDING = "building"
    READY = "ready"
    FAILED = "failed"


class IngestionJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeDocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSED = "processed"
    FAILED = "failed"


class UploadDocumentResponse(BaseModel):
    id: int
    original_filename: str
    mime_type: str
    size_bytes: int
    checksum: str
    status: KnowledgeDocumentStatus
    created_at: datetime


class BuildAgentRequest(BaseModel):
    instruction_goal: str = Field(..., min_length=1, max_length=10000)
    document_ids: list[int] = Field(default_factory=list)


class BuildAgentResponse(BaseModel):
    job_id: int
    agent_spec_version: int
    status: IngestionJobStatus


class IngestionJobResponse(BaseModel):
    id: int
    agent_spec_version: int
    status: IngestionJobStatus
    total_docs: int
    processed_docs: int
    error_summary: str | None = None
    created_at: datetime
    updated_at: datetime


class ActiveAgentSpecResponse(BaseModel):
    version: int
    instruction_text: str
    status: AgentSpecStatus
    active: bool
    updated_at: datetime


class ActivateAgentSpecResponse(BaseModel):
    version: int
    active: bool


class AgentMetaChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    current_instructions: str = ""


class AgentMetaChatResponse(BaseModel):
    proposed_instructions: str


class AgentChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class AgentSourceItem(BaseModel):
    title: str | None = None
    url: str | None = None
    snippet: str | None = None


class AgentChatResponse(BaseModel):
    answer: str
    route: str = "agent_rag"
    sources: list[AgentSourceItem] = []
    requires_followup: bool = False
    followup_field: str | None = None
    agent_spec_version: int | None = None
