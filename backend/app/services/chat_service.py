import logging

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.config_service import ConfigService
from app.services.rag_service import RagService
from app.services.router_service import RouterService
from app.services.session_service import SessionService
from app.services.tool_service import ToolService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        config_service: ConfigService,
        session_service: SessionService,
        router_service: RouterService,
        rag_service: RagService,
        tool_service: ToolService,
    ) -> None:
        self.config_service = config_service
        self.session_service = session_service
        self.router_service = router_service
        self.rag_service = rag_service
        self.tool_service = tool_service

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        config = self.config_service.get_current_config()
        session = self.session_service.get_or_create_session(request.session_id)

        logger.info("session=%s received message=%s", request.session_id, request.message)

        # 1. Continue pending tool flow first
        if session.awaiting_field == "transaction_id" and session.pending_intent == "failed_transaction":
            logger.info("session=%s continuing pending failed_transaction flow", request.session_id)

            tx_id = self.router_service.extract_transaction_id(request.message)
            if not tx_id:
                return ChatResponse(
                    answer="Please provide a valid transaction ID, for example TX123.",
                    route="failed_transaction",
                    sources=[],
                    requires_followup=True,
                    followup_field="transaction_id",
                )

            answer = self.tool_service.get_transaction_status(tx_id)
            self.session_service.update_context(request.session_id, "last_transaction_id", tx_id)
            self.session_service.clear_pending(request.session_id)

            logger.info("session=%s completed failed_transaction with tx_id=%s", request.session_id, tx_id)

            return ChatResponse(
                answer=answer,
                route="failed_transaction",
                sources=[],
                requires_followup=False,
                followup_field=None,
            )

        # 2. Detect new route
        route = self.router_service.detect_route(request.message)
        logger.info("session=%s detected route=%s", request.session_id, route)

        # 3. Application status tool
        if route == "application_status":
            answer = self.tool_service.get_application_status()
            return ChatResponse(
                answer=answer,
                route="application_status",
                sources=[],
                requires_followup=False,
                followup_field=None,
            )

        # 4. Failed transaction tool
        if route == "failed_transaction":
            tx_id = self.router_service.extract_transaction_id(request.message)

            if tx_id:
                answer = self.tool_service.get_transaction_status(tx_id)
                self.session_service.update_context(request.session_id, "last_transaction_id", tx_id)

                logger.info("session=%s handled failed_transaction immediately with tx_id=%s", request.session_id, tx_id)

                return ChatResponse(
                    answer=answer,
                    route="failed_transaction",
                    sources=[],
                    requires_followup=False,
                    followup_field=None,
                )

            self.session_service.set_pending(
                session_id=request.session_id,
                intent="failed_transaction",
                field="transaction_id",
            )

            logger.info("session=%s awaiting transaction_id", request.session_id)

            return ChatResponse(
                answer="Please provide your transaction ID so I can check the failed transaction.",
                route="failed_transaction",
                sources=[],
                requires_followup=True,
                followup_field="transaction_id",
            )

        # 5. RAG route
        try:
            answer, sources = self.rag_service.answer_with_rag(
                message=request.message,
                config=config,
            )
            logger.info("session=%s completed rag with source_count=%s", request.session_id, len(sources))

            return ChatResponse(
                answer=answer,
                route="rag",
                sources=sources,
                requires_followup=False,
                followup_field=None,
            )
        except Exception as exc:
            logger.exception("session=%s rag failed: %s", request.session_id, exc)

            return ChatResponse(
                answer="I’m sorry, I couldn’t retrieve knowledge base information right now.",
                route="rag",
                sources=[],
                requires_followup=False,
                followup_field=None,
            )