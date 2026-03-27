from typing import Any

from app.core.chroma import get_chroma_client
from app.core.llm_client import LLMClient
from app.schemas.agent import AgentChatResponse, AgentSourceItem
from app.services.agent_policy_service import AgentPolicyService


class AgentRuntimeChatService:
    def __init__(self, policy_service: AgentPolicyService, llm_client: LLMClient) -> None:
        self.policy_service = policy_service
        self.llm_client = llm_client
        self.chroma_client = get_chroma_client()

    def handle_chat(self, *, message: str) -> AgentChatResponse:
        active_spec = self.policy_service.get_active_spec()
        if active_spec is None:
            return AgentChatResponse(
                answer="No generated agent is active yet. Please upload docs and run a build first.",
                sources=[],
                agent_spec_version=None,
            )

        collection_name = f"agent_v{active_spec.version}"
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
        except Exception:
            return AgentChatResponse(
                answer="The active agent has no indexed knowledge yet. Please rebuild the agent.",
                sources=[],
                agent_spec_version=active_spec.version,
            )

        query_embedding = self.llm_client.embed_text(message)
        result = collection.query(query_embeddings=[query_embedding], n_results=4)

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]

        chunks: list[dict[str, Any]] = []
        for idx, doc in enumerate(documents):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            chunks.append(
                {
                    "text": doc,
                    "title": metadata.get("title") or metadata.get("original_filename"),
                    "url": metadata.get("source_path"),
                }
            )

        if not chunks:
            return AgentChatResponse(
                answer="I could not find enough information in the generated agent knowledge base.",
                sources=[],
                agent_spec_version=active_spec.version,
            )

        context_lines = []
        for idx, chunk in enumerate(chunks, start=1):
            context_lines.append(f"[{idx}] {chunk['text']}")

        system_prompt = self.policy_service.build_system_prompt(active_spec.instruction_text)
        user_prompt = (
            f"User question:\n{message}\n\n"
            f"Retrieved context:\n{chr(10).join(context_lines)}\n\n"
            "Answer the user question using only the context above."
        )

        answer = self.llm_client.generate_answer(system_prompt=system_prompt, user_prompt=user_prompt)

        sources = [
            AgentSourceItem(
                title=chunk.get("title"),
                url=chunk.get("url"),
                snippet=(chunk.get("text") or "")[:200],
            )
            for chunk in chunks
        ]

        return AgentChatResponse(
            answer=answer,
            sources=sources,
            agent_spec_version=active_spec.version,
        )
