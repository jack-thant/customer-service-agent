import chromadb

from app.core.config import settings

def get_chroma_client():
    if settings.chroma_api_key:
        return chromadb.CloudClient(
            api_key=settings.chroma_api_key,
            tenant=settings.chroma_tenant,
            database=settings.chroma_database,
        )
    return chromadb.PersistentClient(path="./chroma_data")