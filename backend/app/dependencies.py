from app.core.chroma_client import ChromaClientWrapper
from app.core.llm_client import LLMClient
from app.repositories.config_repository import ConfigRepository
from app.repositories.session_repository import SessionRepository
from app.services.chat_service import ChatService
from app.services.config_service import ConfigService
from app.services.rag_service import RagService
from app.services.router_service import RouterService
from app.services.session_service import SessionService
from app.services.tool_service import ToolService

session_repository = SessionRepository()
config_repository = ConfigRepository()

config_service = ConfigService(config_repository=config_repository)
session_service = SessionService(session_repository=session_repository)
router_service = RouterService()
tool_service = ToolService()

chroma_client = ChromaClientWrapper()
llm_client = LLMClient()
rag_service = RagService(chroma_client=chroma_client, llm_client=llm_client)

chat_service = ChatService(
    config_service=config_service,
    session_service=session_service,
    router_service=router_service,
    rag_service=rag_service,
    tool_service=tool_service,
)


def get_chat_service() -> ChatService:
    return chat_service