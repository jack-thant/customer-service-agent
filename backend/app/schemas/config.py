from pydantic import BaseModel

class BotConfig(BaseModel):
    kb_url: str
    additional_guidelines: str = ""