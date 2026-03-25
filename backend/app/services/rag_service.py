from app.core.chroma_client import ChromaClientWrapper
from app.core.llm_client import LLMClient
from app.core.prompt import build_rag_system_prompt, build_rag_user_prompt
from app.schemas.chat import SourceItem
from app.schemas.config import BotConfig


class RagService:
    def __init__(self, chroma_client: ChromaClientWrapper, llm_client: LLMClient) -> None:
        self.chroma_client = chroma_client
        self.llm_client = llm_client

    def answer_with_rag(self, message: str, config: BotConfig) -> tuple[str, list[SourceItem]]:
        query_embedding = self.llm_client.embed_text(message)
        chunks = self.chroma_client.query_chunks(query_embedding=query_embedding, top_k=4)

        if not chunks:
            return (
                "I could not find enough information in the knowledge base to answer that.",
                [],
            )

        system_prompt = build_rag_system_prompt(config.additional_guidelines)
        user_prompt = build_rag_user_prompt(message, chunks)

        answer = self.llm_client.generate_answer(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        sources = [
            SourceItem(
                title=chunk.get("title"),
                url=chunk.get("url"),
                snippet=(chunk.get("text") or "")[:200],
            )
            for chunk in chunks
        ]

        return answer, sources