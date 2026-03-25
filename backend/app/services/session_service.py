from app.repositories.session_repository import SessionRepository
from app.schemas.session import SessionState


class SessionService:
    def __init__(self, session_repository: SessionRepository) -> None:
        self.session_repository = session_repository

    def get_or_create_session(self, session_id: str) -> SessionState:
        session = self.session_repository.get(session_id)
        if session is None:
            session = SessionState(session_id=session_id)
            self.session_repository.save(session)
        return session

    def set_pending(self, session_id: str, intent: str, field: str) -> SessionState:
        session = self.get_or_create_session(session_id)
        session.pending_intent = intent
        session.awaiting_field = field
        self.session_repository.save(session)
        return session

    def clear_pending(self, session_id: str) -> SessionState:
        session = self.get_or_create_session(session_id)
        session.pending_intent = None
        session.awaiting_field = None
        self.session_repository.save(session)
        return session

    def update_context(self, session_id: str, key: str, value) -> SessionState:
        session = self.get_or_create_session(session_id)
        session.context[key] = value
        self.session_repository.save(session)
        return session