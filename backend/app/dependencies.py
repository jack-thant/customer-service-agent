from app.core.chroma_client import ChromaClientWrapper
from app.core.llm_client import LLMClient
from app.repositories.session_repository import SessionRepository
from app.services.chat_service import ChatService
from app.services.config_service import ConfigService
from app.services.rag_service import RagService
from app.services.router_service import RouterService
from app.services.session_service import SessionService
from app.services.tool_service import ToolService
from app.services.ingest_service import KBIngestService
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db

session_repository = SessionRepository()
session_service = SessionService(session_repository=session_repository)
router_service = RouterService()
tool_service = ToolService()

chroma_client = ChromaClientWrapper()
llm_client = LLMClient()
rag_service = RagService(chroma_client=chroma_client, llm_client=llm_client)

ingest_service = KBIngestService()

def get_config_service(db: Session = Depends(get_db)) -> ConfigService:
    return ConfigService(db)


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    config_service = ConfigService(db)
    return ChatService(
        config_service=config_service,
        session_service=session_service,
        router_service=router_service,
        rag_service=rag_service,
        tool_service=tool_service,
    )

def get_ingest_service() -> KBIngestService:
    return ingest_service