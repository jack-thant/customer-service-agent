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

    # S3 settings for Part 2 uploaded documents
    aws_region: str = "ap-southeast-2"
    aws_s3_bucket: str = ""
    aws_s3_prefix: str = "agent-uploads"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""


settings = Settings()
