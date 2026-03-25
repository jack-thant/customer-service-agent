from sqlalchemy.orm import Session

from app.repositories.config_repository import ConfigRepository
from app.schemas.config import BotConfig, UpdateConfigRequest


class ConfigService:
    def __init__(self, db: Session) -> None:
        self.config_repository = ConfigRepository(db)

    def get_current_config(self) -> BotConfig:
        return self.config_repository.get_current_config()

    def update_config(self, payload: UpdateConfigRequest) -> BotConfig:
        return self.config_repository.update_config(payload)