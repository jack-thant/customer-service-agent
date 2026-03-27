from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import (
    get_agent_build_service,
    get_agent_document_service,
    get_agent_meta_service,
    get_agent_policy_service,
    get_agent_runtime_chat_service,
)
from app.schemas.agent import (
    ActivateAgentSpecResponse,
    ActiveAgentSpecResponse,
    AgentChatRequest,
    AgentChatResponse,
    AgentMetaChatRequest,
    AgentMetaChatResponse,
    AgentSpecStatus,
    BuildAgentRequest,
    BuildAgentResponse,
    IngestionJobResponse,
    IngestionJobStatus,
    UploadDocumentResponse,
    KnowledgeDocumentStatus,
)
from app.services.agent_build_service import AgentBuildService
from app.services.agent_document_service import AgentDocumentService
from app.services.agent_meta_service import AgentMetaService
from app.services.agent_policy_service import AgentPolicyService
from app.services.agent_runtime_chat_service import AgentRuntimeChatService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/docs", response_model=UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_service: AgentDocumentService = Depends(get_agent_document_service),
) -> UploadDocumentResponse:
    doc = document_service.save_uploaded_file(file)
    return UploadDocumentResponse(
        id=doc.id,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        size_bytes=doc.size_bytes,
        checksum=doc.checksum,
        status=KnowledgeDocumentStatus(doc.status),
        created_at=doc.created_at,
    )


@router.post("/build", response_model=BuildAgentResponse)
async def build_agent(
    request: BuildAgentRequest,
    build_service: AgentBuildService = Depends(get_agent_build_service),
) -> BuildAgentResponse:
    job = build_service.start_build(
        instruction_goal=request.instruction_goal,
        document_ids=request.document_ids,
    )
    return BuildAgentResponse(
        job_id=job.id,
        agent_spec_version=job.agent_spec_version,
        status=IngestionJobStatus(job.status),
    )


@router.get("/build/{job_id}", response_model=IngestionJobResponse)
async def get_build_status(
    job_id: int,
    build_service: AgentBuildService = Depends(get_agent_build_service),
) -> IngestionJobResponse:
    job = build_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Build job not found")

    return IngestionJobResponse(
        id=job.id,
        agent_spec_version=job.agent_spec_version,
        status=IngestionJobStatus(job.status),
        total_docs=job.total_docs,
        processed_docs=job.processed_docs,
        error_summary=job.error_summary,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/meta-chat", response_model=AgentMetaChatResponse)
async def meta_chat(
    request: AgentMetaChatRequest,
    meta_service: AgentMetaService = Depends(get_agent_meta_service),
) -> AgentMetaChatResponse:
    proposed = meta_service.propose_instructions(
        message=request.message,
        current_instructions=request.current_instructions,
    )
    return AgentMetaChatResponse(proposed_instructions=proposed)


@router.get("/spec/active", response_model=ActiveAgentSpecResponse)
async def get_active_spec(
    policy_service: AgentPolicyService = Depends(get_agent_policy_service),
) -> ActiveAgentSpecResponse:
    spec = policy_service.get_active_spec()
    if spec is None:
        raise HTTPException(status_code=404, detail="No active generated agent")

    return ActiveAgentSpecResponse(
        version=spec.version,
        instruction_text=spec.instruction_text,
        status=AgentSpecStatus(spec.status),
        active=spec.active,
        updated_at=spec.updated_at,
    )


@router.post("/spec/{version}/activate", response_model=ActivateAgentSpecResponse)
async def activate_spec(
    version: int,
    build_service: AgentBuildService = Depends(get_agent_build_service),
) -> ActivateAgentSpecResponse:
    spec = build_service.activate_version(version)
    if spec is None:
        raise HTTPException(status_code=404, detail="Agent spec version not found")

    return ActivateAgentSpecResponse(version=spec.version, active=spec.active)


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    runtime_chat_service: AgentRuntimeChatService = Depends(get_agent_runtime_chat_service),
) -> AgentChatResponse:
    return runtime_chat_service.handle_chat(message=request.message)
