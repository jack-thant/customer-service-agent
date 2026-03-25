from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.mistake_repository import MistakeRepository, to_response
from app.schemas.mistake import (
    CreateMistakeRequest,
    MistakeResponse,
    MistakeStatus,
)


class MistakeService:
    def __init__(self, db: Session) -> None:
        self.repository = MistakeRepository(db)

    def create_mistake(self, payload: CreateMistakeRequest) -> MistakeResponse:
        mistake = self.repository.create(payload)
        return to_response(mistake)

    def get_mistake_model(self, mistake_id: int):
        return self.repository.get_by_id(mistake_id)

    def get_mistake(self, mistake_id: int) -> MistakeResponse:
        mistake = self.repository.get_by_id(mistake_id)
        if mistake is None:
            raise HTTPException(status_code=404, detail="Mistake not found")
        return to_response(mistake)

    def list_mistakes(self, status: MistakeStatus | None = None) -> list[MistakeResponse]:
        mistakes = self.repository.list(status=status)
        return [to_response(m) for m in mistakes]

    def update_status(self, mistake_id: int, status: MistakeStatus) -> MistakeResponse:
        mistake = self.repository.update_status(mistake_id, status)
        if mistake is None:
            raise HTTPException(status_code=404, detail="Mistake not found")
        return to_response(mistake)

    def update_analysis_and_fix(
        self,
        mistake_id: int,
        *,
        root_cause: str | None = None,
        suggested_fix: str | None = None,
        applied_fix: str | None = None,
        rerun_answer: str | None = None,
        status: MistakeStatus | None = None,
    ) -> MistakeResponse:
        mistake = self.repository.update_analysis_and_fix(
            mistake_id,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            applied_fix=applied_fix,
            rerun_answer=rerun_answer,
            status=status,
        )
        if mistake is None:
            raise HTTPException(status_code=404, detail="Mistake not found")
        return to_response(mistake)