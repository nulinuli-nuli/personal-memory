"""Feishu adapter - handles Feishu bot messages."""
from typing import Optional
import logging

from src.access.base import BaseAdapter, AccessRequest, AccessResponse
from src.routing.router import RouterService
from src.core.ai.providers import AIProviderFactory
from src.core.plugin.manager import PluginManager
from src.shared.config import settings

logger = logging.getLogger(__name__)


class FeishuAdapter(BaseAdapter):
    """Feishu adapter for bot messages."""

    def __init__(self, db):
        """
        Initialize Feishu adapter.

        Args:
            db: Database session
        """
        self.db = db
        self.ai = AIProviderFactory.create(
            provider_type=settings.ai_provider,
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model
        )

        self.plugin_manager = PluginManager(self.db, self.ai)
        self.router = RouterService(self.db, self.plugin_manager, self.ai)

    async def process_request(self, request: AccessRequest) -> AccessResponse:
        """
        Process Feishu message.

        Args:
            request: Access request

        Returns:
            Access response
        """
        return await self.router.route(request)

    def format_response(self, response: AccessResponse) -> dict:
        """
        Format response as Feishu message.

        Args:
            response: Access response

        Returns:
            Feishu message dictionary
        """
        if not response.success:
            return {
                "msg_type": "text",
                "content": {
                    "text": f"❌ {response.error}"
                }
            }

        # If response contains Markdown, convert to interactive card
        if response.metadata and "markdown" in response.metadata:
            return self._format_card(response)

        # Simple text response
        return {
            "msg_type": "text",
            "content": {
                "text": response.message
            }
        }

    def _format_card(self, response: AccessResponse) -> dict:
        """
        Format response as Feishu interactive card.

        Args:
            response: Access response with markdown

        Returns:
            Feishu card message dictionary
        """
        markdown_content = response.metadata["markdown"]

        # Convert Markdown table to card elements
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "content": "📊 查询结果",
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": markdown_content
                    }
                }
            ]
        }

        # Add summary if available
        if response.message:
            card["elements"].insert(0, {
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": response.message
                }
            })

        return {
            "msg_type": "interactive",
            "card": card
        }

    async def initialize_plugins(self):
        """Initialize all plugins."""
        count = await self.plugin_manager.discover_and_load_all()
        logger.info(f"Feishu adapter initialized {count} plugins")
        return count
