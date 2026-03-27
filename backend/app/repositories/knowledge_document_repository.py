from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocumentModel
from app.schemas.agent import KnowledgeDocumentStatus


class KnowledgeDocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, document_id: int) -> KnowledgeDocumentModel | None:
        return self.db.query(KnowledgeDocumentModel).filter(KnowledgeDocumentModel.id == document_id).first()

    def get_by_checksum(self, checksum: str) -> KnowledgeDocumentModel | None:
        return (
            self.db.query(KnowledgeDocumentModel)
            .filter(KnowledgeDocumentModel.checksum == checksum)
            .first()
        )

    def create(
        self,
        *,
        original_filename: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        checksum: str,
        status: KnowledgeDocumentStatus,
    ) -> KnowledgeDocumentModel:
        doc = KnowledgeDocumentModel(
            original_filename=original_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            checksum=checksum,
            status=status.value,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list_by_ids(self, document_ids: list[int]) -> list[KnowledgeDocumentModel]:
        if not document_ids:
            return []
        return (
            self.db.query(KnowledgeDocumentModel)
            .filter(KnowledgeDocumentModel.id.in_(document_ids))
            .all()
        )

    def list_all(self) -> list[KnowledgeDocumentModel]:
        return self.db.query(KnowledgeDocumentModel).order_by(KnowledgeDocumentModel.id.asc()).all()

    def update_status(
        self,
        document_id: int,
        *,
        status: KnowledgeDocumentStatus,
        error_message: str | None = None,
    ) -> KnowledgeDocumentModel | None:
        doc = self.get_by_id(document_id)
        if doc is None:
            return None
        doc.status = status.value
        doc.error_message = error_message
        self.db.commit()
        self.db.refresh(doc)
        return doc
