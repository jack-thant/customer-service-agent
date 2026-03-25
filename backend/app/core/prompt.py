def build_rag_system_prompt(guidelines: str) -> str:
    return f"""
                You are a customer support assistant.

                Rules:
                1. Only answer KB questions using the provided context.
                2. Do not make up facts.
                3. If the context is insufficient, say that you could not find enough information in the knowledge base.
                4. Follow these additional guidelines:
                    {guidelines}
            """.strip()


def build_rag_user_prompt(question: str, context_chunks: list[dict]) -> str:
    formatted_context = "\n\n".join(
        [
            f"[Chunk {idx + 1}]\n"
            f"Title: {chunk.get('title') or 'N/A'}\n"
            f"URL: {chunk.get('url') or 'N/A'}\n"
            f"Content: {chunk.get('text', '')}"
            for idx, chunk in enumerate(context_chunks)
        ]
    )

    return f"""
                User question:
                {question}

                Knowledge base context:
                {formatted_context}

                Please answer the user's question using only the context above.
            """.strip()