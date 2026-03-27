import os

from app.core.config import settings

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMClient:
    def __init__(self) -> None:
        self.api_key = settings.openai_api_key
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
        self.embedding_model = settings.embedding_model
        self.client = OpenAI(api_key=self.api_key) if OpenAI and self.api_key else None

    def embed_text(self, text: str) -> list[float]:
        if self.client is None:
            raise RuntimeError("OpenAI client is not configured for embeddings.")

        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=[text],
        )
        return response.data[0].embedding

    def generate_answer(self, system_prompt: str, user_prompt: str) -> str:
        if self.client is None:
            return (
                "Based on the knowledge base context, I found relevant information, "
                "but the LLM client is not configured yet."
            )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content or "I’m sorry, I could not generate a response."