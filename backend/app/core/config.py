from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"

    chroma_api_key: str
    chroma_tenant: str
    chroma_database: str
    chroma_collection_name: str = "atome_kb"
    
    database_url: str

    request_timeout_seconds: int = 20
    max_article_links: int = 1000
    chunk_size: int = 1200
    chunk_overlap: int = 200


settings = Settings()