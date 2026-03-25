from app.repositories.config_repository import ConfigRepository
from app.schemas.config import BotConfig


class ConfigService:
    def __init__(self, config_repository: ConfigRepository) -> None:
        self.config_repository = config_repository

    def get_current_config(self) -> BotConfig:
        return self.config_repository.get_current_config()