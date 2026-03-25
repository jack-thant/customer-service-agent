from app.db.session import Base, engine
from app.models.config import ConfigModel
from app.models.mistake import MistakeModel

def init_db() -> None:
    Base.metadata.create_all(bind=engine)