"""CLI adapter - handles CLI channel requests."""
import asyncio
from typing import Optional
import logging

from src.access.base import BaseAdapter, AccessRequest, AccessResponse
from src.routing.router import RouterService
from src.shared.database import get_db
from src.core.ai.providers import AIProviderFactory
from src.core.plugin.manager import PluginManager
from src.shared.config import settings

logger = logging.getLogger(__name__)


class CLIAdapter(BaseAdapter):
    """CLI adapter for command-line interface."""

    def __init__(self):
        """Initialize CLI adapter."""
        from src.shared.database import SessionLocal
        self.db = SessionLocal()
        self.ai = AIProviderFactory.create(
            provider_type=settings.ai_provider,
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model
        )

        # Initialize plugin manager
        self.plugin_manager = PluginManager(self.db, self.ai)

        # Initialize router service
        self.router = RouterService(self.db, self.plugin_manager, self.ai)

    async def process_request(self, request: AccessRequest) -> AccessResponse:
        """
        Process request.

        Args:
            request: Access request

        Returns:
            Access response
        """
        return await self.router.route(request)

    def format_response(self, response: AccessResponse) -> str:
        """
        Format response for CLI output.

        Args:
            response: Access response

        Returns:
            Formatted string
        """
        if not response.success:
            return f"错误: {response.error}"

        # If response contains Markdown, render it
        if response.metadata and "markdown" in response.metadata:
            from rich.console import Console
            from rich.markdown import Markdown

            console = Console()
            md_content = response.metadata["markdown"]

            # Print summary
            if response.message:
                console.print(f"\n{response.message}\n")

            # Print Markdown table
            console.print(Markdown(md_content))

            return ""  # Already printed

        return response.message

    def sync_process(self, user_id: str, input_text: str) -> str:
        """
        Synchronous processing for CLI commands.

        Args:
            user_id: User ID
            input_text: Input text

        Returns:
            Formatted response string
        """
        async def _process():
            request = AccessRequest(
                user_id=user_id,
                input_text=input_text,
                channel="cli",
                context={},
                metadata={}
            )
            response = await self.process_request(request)
            return self.format_response(response)

        return asyncio.run(_process())

    async def initialize_plugins(self):
        """Initialize all plugins."""
        count = await self.plugin_manager.discover_and_load_all()
        logger.info(f"Initialized {count} plugins")
        return count
