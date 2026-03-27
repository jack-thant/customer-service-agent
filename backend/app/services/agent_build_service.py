import threading

from sqlalchemy.orm import Session

from app.core.chroma import get_chroma_client
from app.core.llm_client import LLMClient
from app.db.session import SessionLocal
from app.models.ingestion_job import IngestionJobModel
from app.repositories.agent_spec_repository import AgentSpecRepository
from app.repositories.ingestion_job_repository import IngestionJobRepository
from app.services.agent_document_service import AgentDocumentService
from app.services.agent_meta_service import AgentMetaService
from app.schemas.agent import AgentSpecStatus, IngestionJobStatus


class AgentBuildService:
    def __init__(self, db: Session, llm_client: LLMClient) -> None:
        self.db = db
        self.llm_client = llm_client
        self.spec_repository = AgentSpecRepository(db)
        self.job_repository = IngestionJobRepository(db)
        self.document_service = AgentDocumentService(db)
        self.meta_service = AgentMetaService(llm_client)

    def start_build(self, *, instruction_goal: str, document_ids: list[int]) -> IngestionJobModel:
        proposed_instructions = self.meta_service.propose_instructions(
            message=instruction_goal,
            current_instructions="",
        )
        spec = self.spec_repository.create(
            instruction_text=proposed_instructions,
            status=AgentSpecStatus.BUILDING,
        )

        documents = self.document_service.list_documents(document_ids)
        job = self.job_repository.create(agent_spec_version=spec.version, total_docs=len(documents))

        thread = threading.Thread(
            target=self._run_build_job,
            kwargs={
                "job_id": job.id,
                "spec_version": spec.version,
                "document_ids": [doc.id for doc in documents],
            },
            daemon=True,
        )
        thread.start()

        return job

    def get_job(self, job_id: int) -> IngestionJobModel | None:
        return self.job_repository.get_by_id(job_id)

    def activate_version(self, version: int):
        return self.spec_repository.activate_version(version)

    def append_fix_to_version(self, *, version: int, fix: str):
        spec = self.spec_repository.get_by_version(version)
        if spec is None:
            return None

        existing = (spec.instruction_text or "").strip()
        updated = f"{existing}\n\n## Learned fixes\n- {fix}" if existing else f"## Learned fixes\n- {fix}"
        return self.spec_repository.update_instruction_text(version, updated)

    def _run_build_job(self, *, job_id: int, spec_version: int, document_ids: list[int]) -> None:
        db = SessionLocal()
        try:
            llm_client = LLMClient()
            spec_repository = AgentSpecRepository(db)
            job_repository = IngestionJobRepository(db)
            document_service = AgentDocumentService(db)
            chroma_client = get_chroma_client()
            collection = chroma_client.get_or_create_collection(name=f"agent_v{spec_version}")

            job_repository.update(job_id, status=IngestionJobStatus.RUNNING, processed_docs=0)

            documents = document_service.list_documents(document_ids)
            processed_docs = 0

            for document in documents:
                try:
                    text = document_service.read_document_text(document)
                    chunks = document_service.chunk_text(text)
                    if not chunks:
                        document_service.mark_failed(document.id, "No readable text found")
                        processed_docs += 1
                        job_repository.update(job_id, processed_docs=processed_docs)
                        continue

                    embeddings = document_service.embed_chunks(llm_client, chunks)
                    ids = [f"doc_{document.id}_chunk_{idx}" for idx in range(len(chunks))]
                    metadatas = [
                        {
                            "document_id": document.id,
                            "original_filename": document.original_filename,
                            "source_path": document.storage_path,
                            "chunk_index": idx,
                            "title": document.original_filename,
                        }
                        for idx in range(len(chunks))
                    ]

                    collection.upsert(
                        ids=ids,
                        documents=chunks,
                        embeddings=embeddings,
                        metadatas=metadatas,
                    )

                    document_service.mark_processed(document.id)
                except Exception as exc:
                    document_service.mark_failed(document.id, str(exc))
                finally:
                    processed_docs += 1
                    job_repository.update(job_id, processed_docs=processed_docs)

            spec_repository.update_status(spec_version, AgentSpecStatus.READY)
            spec_repository.activate_version(spec_version)
            job_repository.update(job_id, status=IngestionJobStatus.COMPLETED)
        except Exception as exc:
            AgentSpecRepository(db).update_status(spec_version, AgentSpecStatus.FAILED)
            IngestionJobRepository(db).update(
                job_id,
                status=IngestionJobStatus.FAILED,
                error_summary=str(exc),
            )
        finally:
            db.close()
