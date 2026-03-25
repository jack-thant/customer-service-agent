from app.schemas.session import SessionState


class SessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    def save(self, state: SessionState) -> None:
        self._sessions[state.session_id] = state

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)