from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.chroma_client import ChromaClientWrapper
from app.core.llm_client import LLMClient
from app.db.session import get_db
from app.repositories.session_repository import SessionRepository
from app.services.auto_fix_service import AutoFixService
from app.services.chat_service import ChatService
from app.services.config_service import ConfigService
from app.services.evaluation_service import EvaluationService
from app.services.ingest_service import KBIngestService
from app.services.mistake_service import MistakeService
from app.services.rag_service import RagService
from app.services.router_service import RouterService
from app.services.session_service import SessionService
from app.services.tool_service import ToolService

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


def get_mistake_service(db: Session = Depends(get_db)) -> MistakeService:
    return MistakeService(db)


def get_evaluation_service() -> EvaluationService:
    return EvaluationService(llm_client=llm_client)


def get_auto_fix_service(db: Session = Depends(get_db)) -> AutoFixService:
    config_service = ConfigService(db)
    mistake_service = MistakeService(db)
    chat_service = ChatService(
        config_service=config_service,
        session_service=session_service,
        router_service=router_service,
        rag_service=rag_service,
        tool_service=tool_service,
    )
    evaluation_service = EvaluationService(llm_client=llm_client)

    return AutoFixService(
        llm_client=llm_client,
        config_service=config_service,
        mistake_service=mistake_service,
        chat_service=chat_service,
        evaluation_service=evaluation_service,
    )