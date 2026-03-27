from typing import Any

from app.core.chroma import get_chroma_client
from app.core.config import settings

class ChromaClientWrapper:
    def __init__(self) -> None:
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name
        )

    def query_chunks(self, query_embedding: list[float], top_k: int = 4) -> list[dict[str, Any]]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] if results.get("distances") else []
        ids = results.get("ids", [[]])[0] if results.get("ids") else []

        normalized_chunks: list[dict[str, Any]] = []

        for idx, doc in enumerate(documents):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            distance = distances[idx] if idx < len(distances) else None
            chunk_id = ids[idx] if idx < len(ids) else None

            normalized_chunks.append(
                {
                    "id": chunk_id,
                    "text": doc,
                    "title": metadata.get("article_title"),
                    "url": metadata.get("source_url"),
                    "score": distance,
                    "metadata": metadata,
                }
            )

        return normalized_chunks
