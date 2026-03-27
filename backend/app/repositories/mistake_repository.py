from sqlalchemy.orm import Session

from app.models.mistake import MistakeModel
from app.schemas.mistake import (
    CreateMistakeRequest,
    MistakeResponse,
    MistakeRuntime,
    MistakeStatus,
)


class MistakeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: CreateMistakeRequest) -> MistakeModel:
        mistake = MistakeModel(
            user_query=payload.user_query,
            bot_answer=payload.bot_answer,
            feedback=payload.feedback,
            route=payload.route,
            session_id=payload.session_id,
            runtime=payload.runtime.value,
            agent_spec_version=payload.agent_spec_version,
            status=MistakeStatus.OPEN.value,
        )
        self.db.add(mistake)
        self.db.commit()
        self.db.refresh(mistake)
        return mistake

    def get_by_id(self, mistake_id: int) -> MistakeModel | None:
        return self.db.query(MistakeModel).filter(MistakeModel.id == mistake_id).first()

    def list(self, status: MistakeStatus | None = None) -> list[MistakeModel]:
        query = self.db.query(MistakeModel)
        if status is not None:
            query = query.filter(MistakeModel.status == status.value)
        return query.order_by(MistakeModel.created_at.desc()).all()

    def update_status(self, mistake_id: int, status: MistakeStatus) -> MistakeModel | None:
        mistake = self.get_by_id(mistake_id)
        if mistake is None:
            return None

        mistake.status = status.value
        self.db.commit()
        self.db.refresh(mistake)
        return mistake

    def update_analysis_and_fix(
        self,
        mistake_id: int,
        *,
        root_cause: str | None = None,
        suggested_fix: str | None = None,
        applied_fix: str | None = None,
        rerun_answer: str | None = None,
        status: MistakeStatus | None = None,
    ) -> MistakeModel | None:
        mistake = self.get_by_id(mistake_id)
        if mistake is None:
            return None

        if root_cause is not None:
            mistake.root_cause = root_cause
        if suggested_fix is not None:
            mistake.suggested_fix = suggested_fix
        if applied_fix is not None:
            mistake.applied_fix = applied_fix
        if rerun_answer is not None:
            mistake.rerun_answer = rerun_answer
        if status is not None:
            mistake.status = status.value

        self.db.commit()
        self.db.refresh(mistake)
        return mistake


def to_response(m: MistakeModel) -> MistakeResponse:
    return MistakeResponse(
        id=m.id,
        user_query=m.user_query,
        bot_answer=m.bot_answer,
        feedback=m.feedback,
        route=m.route,
        session_id=m.session_id,
        runtime=MistakeRuntime(m.runtime),
        agent_spec_version=m.agent_spec_version,
        status=MistakeStatus(m.status),
        root_cause=m.root_cause,
        suggested_fix=m.suggested_fix,
        applied_fix=m.applied_fix,
        rerun_answer=m.rerun_answer,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )
