from sqlalchemy.orm import Session

from app.models.ingestion_job import IngestionJobModel
from app.schemas.agent import IngestionJobStatus


class IngestionJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, job_id: int) -> IngestionJobModel | None:
        return self.db.query(IngestionJobModel).filter(IngestionJobModel.id == job_id).first()

    def create(self, *, agent_spec_version: int, total_docs: int) -> IngestionJobModel:
        job = IngestionJobModel(
            agent_spec_version=agent_spec_version,
            status=IngestionJobStatus.QUEUED.value,
            total_docs=total_docs,
            processed_docs=0,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update(
        self,
        job_id: int,
        *,
        status: IngestionJobStatus | None = None,
        processed_docs: int | None = None,
        error_summary: str | None = None,
    ) -> IngestionJobModel | None:
        job = self.get_by_id(job_id)
        if job is None:
            return None

        if status is not None:
            job.status = status.value
        if processed_docs is not None:
            job.processed_docs = processed_docs
        if error_summary is not None:
            job.error_summary = error_summary

        self.db.commit()
        self.db.refresh(job)
        return job
