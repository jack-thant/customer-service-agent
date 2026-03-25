from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.config import ConfigModel
from app.schemas.config import BotConfig, UpdateConfigRequest


DEFAULT_KB_URL = "https://help.atome.ph/hc/en-gb/categories/4439682039065-Atome-Card"
DEFAULT_GUIDELINES = (
    "Be concise, helpful, and only answer from the provided knowledge base context "
    "for KB questions. If the context is insufficient, say so clearly."
)


class ConfigRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_current_config(self) -> BotConfig:
        config = self.db.query(ConfigModel).filter(ConfigModel.id == 1).first()

        if config is None:
            config = ConfigModel(
                id=1,
                kb_url=DEFAULT_KB_URL,
                additional_guidelines=DEFAULT_GUIDELINES,
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)

        return BotConfig(
            kb_url=config.kb_url,
            additional_guidelines=config.additional_guidelines,
            updated_at=config.updated_at,
        )

    def update_config(self, payload: UpdateConfigRequest) -> BotConfig:
        config = self.db.query(ConfigModel).filter(ConfigModel.id == 1).first()

        if config is None:
            config = ConfigModel(
                id=1,
                kb_url=str(payload.kb_url),
                additional_guidelines=payload.additional_guidelines,
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(config)
        else:
            config.kb_url = str(payload.kb_url)
            config.additional_guidelines = payload.additional_guidelines
            config.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(config)

        return BotConfig(
            kb_url=config.kb_url,
            additional_guidelines=config.additional_guidelines,
            updated_at=config.updated_at,
        )