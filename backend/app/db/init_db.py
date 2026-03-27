from sqlalchemy import inspect, text

from app.db.session import Base, engine
from app.models.agent_spec import AgentSpecModel
from app.models.config import ConfigModel
from app.models.ingestion_job import IngestionJobModel
from app.models.knowledge_document import KnowledgeDocumentModel
from app.models.mistake import MistakeModel


def _patch_mistakes_table_columns() -> None:
    inspector = inspect(engine)
    if "mistakes" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("mistakes")}

    alter_statements: list[str] = []
    if "runtime" not in existing_columns:
        alter_statements.append(
            "ALTER TABLE mistakes ADD COLUMN runtime TEXT NOT NULL DEFAULT 'part1'"
        )
    if "agent_spec_version" not in existing_columns:
        alter_statements.append("ALTER TABLE mistakes ADD COLUMN agent_spec_version INTEGER")
    if "root_cause" not in existing_columns:
        alter_statements.append("ALTER TABLE mistakes ADD COLUMN root_cause TEXT")
    if "suggested_fix" not in existing_columns:
        alter_statements.append("ALTER TABLE mistakes ADD COLUMN suggested_fix TEXT")
    if "applied_fix" not in existing_columns:
        alter_statements.append("ALTER TABLE mistakes ADD COLUMN applied_fix TEXT")
    if "rerun_answer" not in existing_columns:
        alter_statements.append("ALTER TABLE mistakes ADD COLUMN rerun_answer TEXT")

    if not alter_statements:
        return

    with engine.begin() as connection:
        for statement in alter_statements:
            connection.execute(text(statement))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _patch_mistakes_table_columns()
