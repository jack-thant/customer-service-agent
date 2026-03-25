from app.schemas.config import BotConfig

class ConfigRepository:
    def get_current_config(self) -> BotConfig:
        return BotConfig(
            kb_url="https://help.atome.ph/hc/en-gb/categories/4439682039065-Atome-Card",
            additional_guidelines=(
                "Be concise, helpful, and only answer from the provided knowledge base context "
                "for KB questions. If the context is insufficient, say so clearly."
            ),
        )