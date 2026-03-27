from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.agent_spec import AgentSpecModel
from app.schemas.agent import AgentSpecStatus


class AgentSpecRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active(self) -> AgentSpecModel | None:
        return (
            self.db.query(AgentSpecModel)
            .filter(AgentSpecModel.active.is_(True))
            .order_by(AgentSpecModel.version.desc())
            .first()
        )

    def get_by_version(self, version: int) -> AgentSpecModel | None:
        return self.db.query(AgentSpecModel).filter(AgentSpecModel.version == version).first()

    def get_next_version(self) -> int:
        current_max = self.db.query(func.max(AgentSpecModel.version)).scalar() or 0
        return int(current_max) + 1

    def create(self, *, instruction_text: str, status: AgentSpecStatus) -> AgentSpecModel:
        spec = AgentSpecModel(
            version=self.get_next_version(),
            instruction_text=instruction_text,
            status=status.value,
            active=False,
        )
        self.db.add(spec)
        self.db.commit()
        self.db.refresh(spec)
        return spec

    def update_status(self, version: int, status: AgentSpecStatus) -> AgentSpecModel | None:
        spec = self.get_by_version(version)
        if spec is None:
            return None
        spec.status = status.value
        self.db.commit()
        self.db.refresh(spec)
        return spec

    def update_instruction_text(self, version: int, instruction_text: str) -> AgentSpecModel | None:
        spec = self.get_by_version(version)
        if spec is None:
            return None
        spec.instruction_text = instruction_text
        self.db.commit()
        self.db.refresh(spec)
        return spec

    def activate_version(self, version: int) -> AgentSpecModel | None:
        target = self.get_by_version(version)
        if target is None:
            return None

        self.db.query(AgentSpecModel).update({AgentSpecModel.active: False})
        target.active = True
        self.db.commit()
        self.db.refresh(target)
        return target
