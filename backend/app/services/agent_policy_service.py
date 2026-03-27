from sqlalchemy.orm import Session

from app.models.agent_spec import AgentSpecModel
from app.repositories.agent_spec_repository import AgentSpecRepository


class AgentPolicyService:
    def __init__(self, db: Session) -> None:
        self.repository = AgentSpecRepository(db)

    def get_active_spec(self) -> AgentSpecModel | None:
        return self.repository.get_active()

    def build_system_prompt(self, instruction_text: str) -> str:
        base = (
            "You are a customer service AI assistant. "
            "Answer only using the retrieved knowledge context. "
            "If context is insufficient, clearly say so."
        )
        if instruction_text.strip():
            return f"{base}\n\nManager instructions:\n{instruction_text.strip()}"
        return base
