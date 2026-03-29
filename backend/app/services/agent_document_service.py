import hashlib
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm_client import LLMClient
from app.models.knowledge_document import KnowledgeDocumentModel
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.schemas.agent import KnowledgeDocumentStatus
from app.services.s3_storage_service import S3StorageService


class AgentDocumentService:
    ALLOWED_EXTENSIONS = {".txt", ".md", ".html", ".htm", ".pdf"}
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

    def __init__(self, db: Session) -> None:
        self.repository = KnowledgeDocumentRepository(db)
        if not settings.aws_s3_bucket:
            raise RuntimeError("S3 storage is required. Set AWS_S3_BUCKET in environment.")
        self.s3_storage = S3StorageService()

    def save_uploaded_file(self, file: UploadFile) -> KnowledgeDocumentModel:
        filename = file.filename or "uploaded_file"
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file extension: {ext}. "
                    "Allowed: .txt, .md, .html, .htm, .pdf (text-based PDF only, no OCR)."
                ),
            )

        data = file.file.read()
        size_bytes = len(data)
        if size_bytes == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if size_bytes > self.MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="File exceeds max size of 5MB")

        checksum = hashlib.sha256(data).hexdigest()
        existing = self.repository.get_by_checksum(checksum)
        if existing is not None:
            if existing.storage_path.startswith("s3://") and self.s3_storage.object_exists(existing.storage_path):
                return existing

            mime_type = file.content_type or "text/plain"
            key = self.s3_storage.make_object_key(filename)
            storage_path = self.s3_storage.upload_bytes(
                data=data,
                key=key,
                content_type=mime_type,
            )
            updated = self.repository.update_after_reupload(
                existing.id,
                storage_path=storage_path,
                mime_type=mime_type,
                size_bytes=size_bytes,
                status=KnowledgeDocumentStatus.UPLOADED,
                error_message=None,
            )
            if updated is not None:
                return updated

        mime_type = file.content_type or "text/plain"
        key = self.s3_storage.make_object_key(filename)
        storage_path = self.s3_storage.upload_bytes(
            data=data,
            key=key,
            content_type=mime_type,
        )

        return self.repository.create(
            original_filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
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

    def read_document_text(self, document: KnowledgeDocumentModel) -> str:
        storage_path = document.storage_path

        if not storage_path.startswith("s3://"):
            raise ValueError(
                f"Invalid storage path for production mode: {storage_path}. Expected s3:// URI."
            )

        ext = Path(document.original_filename).suffix.lower()
        if ext == ".pdf":
            pdf_bytes = self.s3_storage.read_bytes(storage_path)
            return self._extract_pdf_text(pdf_bytes)

        raw = self.s3_storage.read_text(storage_path)

        if ext in {".html", ".htm"}:
            soup = BeautifulSoup(raw, "html.parser")
            text = soup.get_text("\n", strip=True)
            return "\n".join([line for line in text.splitlines() if line.strip()])

        return raw

    @staticmethod
    def _extract_pdf_text(pdf_bytes: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required for PDF uploads. Please install pypdf.") from exc

        reader = PdfReader(BytesIO(pdf_bytes))
        pages: list[str] = []
        for page in reader.pages:
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(text)

        extracted = "\n\n".join(pages).strip()
        if not extracted:
            raise ValueError(
                "No extractable text found in PDF. Only text-based PDFs are supported; "
                "scanned/image PDFs require OCR and are not supported."
            )
        return extracted

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
