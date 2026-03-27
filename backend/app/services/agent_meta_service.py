from app.core.llm_client import LLMClient


class AgentMetaService:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def propose_instructions(self, *, message: str, current_instructions: str) -> str:
        system_prompt = (
            "You are a customer service manager assistant. "
            "Convert manager intent into clear operational instructions for a support AI. "
            "Return plain text only."
        )

        user_prompt = f"""
Current instructions:
{current_instructions or '(none)'}

Manager request:
{message}

Produce concise, actionable instructions for the support AI.
""".strip()

        return self.llm_client.generate_answer(system_prompt=system_prompt, user_prompt=user_prompt).strip()
