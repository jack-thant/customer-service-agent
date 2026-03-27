from app.db.session import Base, engine
from app.models.agent_spec import AgentSpecModel
from app.models.config import ConfigModel
from app.models.ingestion_job import IngestionJobModel
from app.models.knowledge_document import KnowledgeDocumentModel
from app.models.mistake import MistakeModel

def init_db() -> None:
    Base.metadata.create_all(bind=engine)
