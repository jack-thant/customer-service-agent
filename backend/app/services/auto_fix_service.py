import json
import logging

from app.schemas.chat import ChatRequest
from app.schemas.config import UpdateConfigRequest
from app.schemas.mistake import MistakeRuntime, MistakeStatus
from app.services.agent_build_service import AgentBuildService
from app.services.agent_policy_service import AgentPolicyService
from app.services.chat_service import ChatService
from app.services.config_service import ConfigService
from app.services.evaluation_service import EvaluationService
from app.services.mistake_service import MistakeService
from app.core.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AutoFixService:
    def __init__(
        self,
        llm_client: LLMClient,
        config_service: ConfigService,
        mistake_service: MistakeService,
        chat_service: ChatService,
        evaluation_service: EvaluationService,
        agent_policy_service: AgentPolicyService,
        agent_build_service: AgentBuildService,
    ) -> None:
        self.llm_client = llm_client
        self.config_service = config_service
        self.mistake_service = mistake_service
        self.chat_service = chat_service
        self.evaluation_service = evaluation_service
        self.agent_policy_service = agent_policy_service
        self.agent_build_service = agent_build_service

    def process_mistake(self, mistake_id: int):
        mistake = self.mistake_service.get_mistake_model(mistake_id)
        if mistake is None:
            return None

        if mistake.runtime == MistakeRuntime.PART2.value:
            return self._process_part2_mistake(mistake_id)

        return self._process_part1_mistake(mistake_id)

    def _process_part1_mistake(self, mistake_id: int):
        mistake = self.mistake_service.get_mistake_model(mistake_id)
        if mistake is None:
            return None

        current_config = self.config_service.get_current_config()

        analysis = self._generate_analysis(
            user_query=mistake.user_query,
            bot_answer=mistake.bot_answer,
            feedback=mistake.feedback,
            current_guidelines=current_config.additional_guidelines,
            route=mistake.route,
        )

        root_cause = analysis.get("root_cause", "").strip()
        suggested_fix = analysis.get("suggested_fix", "").strip()

        applied_fix = self._build_guideline_patch(suggested_fix)

        updated_guidelines = self._append_fix(
            current_config.additional_guidelines,
            applied_fix,
        )

        self.config_service.update_config(
            UpdateConfigRequest(
                kb_url=current_config.kb_url,
                additional_guidelines=updated_guidelines,
            )
        )

        self.mistake_service.update_analysis_and_fix(
            mistake_id,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            applied_fix=applied_fix,
            status=MistakeStatus.PATCHED,
        )

        rerun_response = self.chat_service.handle_chat(
            ChatRequest(
                session_id=f"mistake-eval-{mistake_id}",
                message=mistake.user_query,
            )
        )

        improved = self.evaluation_service.is_improved(
            user_query=mistake.user_query,
            feedback=mistake.feedback,
            old_answer=mistake.bot_answer,
            new_answer=rerun_response.answer,
        )

        final_status = MistakeStatus.FIXED if improved else MistakeStatus.PATCHED

        return self.mistake_service.update_analysis_and_fix(
            mistake_id,
            rerun_answer=rerun_response.answer,
            status=final_status,
        )

    def _process_part2_mistake(self, mistake_id: int):
        mistake = self.mistake_service.get_mistake_model(mistake_id)
        if mistake is None:
            return None

        active_spec = self.agent_policy_service.get_active_spec()
        if active_spec is None:
            return self.mistake_service.update_analysis_and_fix(
                mistake_id,
                root_cause="No active generated agent available for patching.",
                suggested_fix="Build and activate a generated agent before running part2 auto-fix.",
                applied_fix=None,
                status=MistakeStatus.PATCHED,
            )

        target_version = mistake.agent_spec_version or active_spec.version
        current_guidelines = active_spec.instruction_text

        analysis = self._generate_analysis(
            user_query=mistake.user_query,
            bot_answer=mistake.bot_answer,
            feedback=mistake.feedback,
            current_guidelines=current_guidelines,
            route=mistake.route,
        )

        root_cause = analysis.get("root_cause", "").strip()
        suggested_fix = analysis.get("suggested_fix", "").strip()
        applied_fix = self._build_guideline_patch(suggested_fix)

        updated_spec = self.agent_build_service.append_fix_to_version(
            version=target_version,
            fix=applied_fix,
        )
        if updated_spec is None:
            return self.mistake_service.update_analysis_and_fix(
                mistake_id,
                root_cause=root_cause,
                suggested_fix=suggested_fix,
                applied_fix=None,
                status=MistakeStatus.PATCHED,
            )

        return self.mistake_service.update_analysis_and_fix(
            mistake_id,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            applied_fix=applied_fix,
            rerun_answer="Part 2 fix applied to generated agent instructions.",
            status=MistakeStatus.FIXED,
        )

    def _generate_analysis(
        self,
        *,
        user_query: str,
        bot_answer: str,
        feedback: str,
        current_guidelines: str,
        route: str | None,
    ) -> dict:
        system_prompt = (
            "You analyze support bot mistakes. "
            "Return only valid JSON with keys 'root_cause' and 'suggested_fix'. "
            "The suggested_fix must be one short, specific instruction. "
            "Do not rewrite the entire policy."
        )

        user_prompt = f"""
                        User query:
                        {user_query}

                        Bot answer:
                        {bot_answer}

                        User feedback:
                        {feedback}

                        Route:
                        {route or "unknown"}

                        Current guidelines:
                        {current_guidelines}

                        Return JSON only:
                        {{
                        "root_cause": "...",
                        "suggested_fix": "..."
                        }}
                        """.strip()

        raw = self.llm_client.generate_answer(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        try:
            return json.loads(raw)
        except Exception:
            logger.warning("Failed to parse analysis JSON. Raw output: %s", raw)
            return {
                "root_cause": "The answer did not sufficiently address the user's request.",
                "suggested_fix": "Ensure answers stay directly relevant to the user query and retrieved context.",
            }

    @staticmethod
    def _build_guideline_patch(suggested_fix: str) -> str:
        fallback = "Ensure answers stay directly relevant to the user query and retrieved context."
        cleaned = " ".join((suggested_fix or "").split()).strip()
        return cleaned or fallback
    
    @staticmethod
    def _append_fix(existing: str, fix: str) -> str:
        existing = (existing or "").strip()

        if "## Learned fixes" in existing:
            return f"{existing}\n- {fix}"

        if existing:
            return f"{existing}\n\n## Learned fixes\n- {fix}"

        return f"## Learned fixes\n- {fix}"
