"""Router service - AI-driven plugin routing."""
from typing import Dict, List, Any
from pathlib import Path
import logging

from src.access.base import AccessRequest, AccessResponse
from src.core.plugin.manager import PluginManager
from src.storage.context.repository import ContextRepository
from src.shared.config import get_project_root

logger = logging.getLogger(__name__)


class RouterService:
    """AI-driven intelligent plugin routing service."""

    def __init__(self, db_session, plugin_manager: PluginManager, ai_provider):
        """
        Initialize router service.

        Args:
            db_session: Database session
            plugin_manager: Plugin manager instance
            ai_provider: AI provider instance
        """
        self.db = db_session
        self.plugin_manager = plugin_manager
        self.ai = ai_provider
        self.context_repo = ContextRepository(db_session)
        # Use absolute path to prompts directory
        self.prompts_dir = get_project_root() / "prompts"

    async def route(self, request: AccessRequest) -> AccessResponse:
        """
        Route request to appropriate plugin.

        Args:
            request: Access request

        Returns:
            Access response
        """
        try:
            # 1. Get context
            context = self.context_repo.get_context(int(request.user_id))
            recent_turns = self.context_repo.get_recent_turns(int(request.user_id), limit=3)

            # 2. AI decides which plugin to call
            plugin_decision = await self._decide_plugin(
                request.input_text,
                recent_turns
            )

            if not plugin_decision.get("success"):
                return AccessResponse(
                    success=False,
                    error=plugin_decision.get("error", "路由决策失败"),
                    message="",
                    data=None,
                    metadata={}
                )

            # 3. Get plugin
            plugin = self.plugin_manager.get_plugin(plugin_decision["plugin_name"])
            if not plugin:
                return AccessResponse(
                    success=False,
                    error=f"未找到插件: {plugin_decision['plugin_name']}",
                    message="",
                    data=None,
                    metadata={}
                )

            # 4. Call plugin to handle request
            # Merge action into params for easier access in plugins
            plugin_params = plugin_decision.get("params", {})
            plugin_params["action"] = plugin_decision.get("action", "add")

            response = await plugin.execute(
                request,
                context.__dict__ if context else {},
                plugin_params
            )

            # 5. Update context
            self.context_repo.add_turn(
                user_id=int(request.user_id),
                turn_data={
                    "user_input": request.input_text,
                    "intent": plugin_decision.get("action"),
                    "domain": plugin_decision["plugin_name"],
                    "response": response.message,
                    "metadata": plugin_decision.get("metadata", {})
                }
            )

            return response

        except Exception as e:
            logger.error(f"Routing error: {e}", exc_info=True)
            return AccessResponse(
                success=False,
                error=f"路由失败: {str(e)}",
                message="",
                data=None,
                metadata={}
            )

    async def _decide_plugin(self, input_text: str, recent_turns: List) -> Dict:
        """
        Use AI to decide which plugin to call.

        Args:
            input_text: User input text
            recent_turns: Recent conversation turns

        Returns:
            Plugin decision dictionary
        """
        # Get all available plugins
        available_plugins = self.plugin_manager.list_plugins()

        # Build AI prompt
        prompt = self._build_router_prompt(
            input_text,
            recent_turns,
            available_plugins
        )

        # Call AI
        try:
            response = await self.ai.chat(prompt)
            return response
        except Exception as e:
            logger.error(f"AI decision failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"AI决策失败: {str(e)}"
            }

    def _build_router_prompt(
        self,
        input_text: str,
        recent_turns: List,
        plugins: List[Dict]
    ) -> str:
        """
        Build AI prompt for routing decision.

        Args:
            input_text: User input text
            recent_turns: Recent conversation turns
            plugins: Available plugins list

        Returns:
            Formatted prompt
        """
        plugin_descriptions = "\n".join([
            f"- {p['name']}: {p['description']}"
            for p in plugins
        ])

        context_str = self._format_context(recent_turns)

        # Load prompt template
        prompt_template = (self.prompts_dir / "router_decision.txt").read_text(encoding="utf-8")

        return prompt_template.format(
            input_text=input_text,
            plugins=plugin_descriptions,
            context=context_str
        )

    def _format_context(self, recent_turns: List) -> str:
        """
        Format conversation context.

        Args:
            recent_turns: Recent conversation turns

        Returns:
            Formatted context string
        """
        if not recent_turns:
            return "（无历史对话）"

        formatted = []
        for turn in recent_turns:
            formatted.append(f"用户: {turn.user_input}")
            formatted.append(f"系统: {turn.response} [{turn.domain or 'Unknown'}]")

        return "\n".join(formatted)
