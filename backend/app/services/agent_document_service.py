import hashlib
import uuid
from pathlib import Path

from bs4 import BeautifulSoup
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.llm_client import LLMClient
from app.models.knowledge_document import KnowledgeDocumentModel
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.schemas.agent import KnowledgeDocumentStatus


class AgentDocumentService:
    ALLOWED_EXTENSIONS = {".txt", ".md", ".html", ".htm"}
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

    def __init__(self, db: Session) -> None:
        self.repository = KnowledgeDocumentRepository(db)
        self.upload_dir = Path(__file__).resolve().parents[3] / "data" / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(self, file: UploadFile) -> KnowledgeDocumentModel:
        filename = file.filename or "uploaded_file"
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")

        data = file.file.read()
        size_bytes = len(data)
        if size_bytes == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if size_bytes > self.MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="File exceeds max size of 5MB")

        checksum = hashlib.sha256(data).hexdigest()
        existing = self.repository.get_by_checksum(checksum)
        if existing is not None:
            return existing

        unique_name = f"{uuid.uuid4().hex}{ext}"
        storage_path = self.upload_dir / unique_name
        with open(storage_path, "wb") as f:
            f.write(data)

        mime_type = file.content_type or "text/plain"
        return self.repository.create(
            original_filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=str(storage_path),
            checksum=checksum,
            status=KnowledgeDocumentStatus.UPLOADED,
        )

    def list_documents(self, document_ids: list[int]) -> list[KnowledgeDocumentModel]:
        if document_ids:
            return self.repository.list_by_ids(document_ids)
        return self.repository.list_all()

    def mark_processed(self, document_id: int) -> None:
        self.repository.update_status(document_id, status=KnowledgeDocumentStatus.PROCESSED)

    def mark_failed(self, document_id: int, error_message: str) -> None:
        self.repository.update_status(
            document_id,
            status=KnowledgeDocumentStatus.FAILED,
            error_message=error_message,
        )

    @staticmethod
    def read_document_text(document: KnowledgeDocumentModel) -> str:
        path = Path(document.storage_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {document.storage_path}")

        ext = path.suffix.lower()
        raw = path.read_text(encoding="utf-8", errors="ignore")

        if ext in {".html", ".htm"}:
            soup = BeautifulSoup(raw, "html.parser")
            text = soup.get_text("\n", strip=True)
            return "\n".join([line for line in text.splitlines() if line.strip()])

        return raw

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1200, chunk_overlap: int = 200) -> list[str]:
        normalized = " ".join(text.split())
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        step = max(1, chunk_size - chunk_overlap)

        while start < len(normalized):
            end = min(len(normalized), start + chunk_size)
            chunks.append(normalized[start:end])
            if end >= len(normalized):
                break
            start += step

        return chunks

    @staticmethod
    def embed_chunks(llm_client: LLMClient, chunks: list[str]) -> list[list[float]]:
        return [llm_client.embed_text(chunk) for chunk in chunks]
