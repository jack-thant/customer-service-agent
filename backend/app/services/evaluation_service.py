import json
import logging

from app.core.llm_client import LLMClient

logger = logging.getLogger(__name__)


class EvaluationService:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def is_improved(
        self,
        *,
        user_query: str,
        feedback: str,
        old_answer: str,
        new_answer: str,
    ) -> bool:
        system_prompt = (
            "You are an evaluator for customer support bot improvements. "
            "Return only valid JSON with key 'improved' as a boolean."
        )

        user_prompt = f"""
                        User query:
                        {user_query}

                        User feedback about the original answer:
                        {feedback}

                        Original answer:
                        {old_answer}

                        New answer:
                        {new_answer}

                        Decide whether the new answer better addresses the user's feedback than the original answer.

                        Return JSON only:
                        {{"improved": true}}
                        """.strip()

        try:
            raw = self.llm_client.generate_answer(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            data = json.loads(raw)
            return bool(data.get("improved", False))
        except Exception as exc:
            logger.warning("Evaluation failed, defaulting to False: %s", exc)
            return False