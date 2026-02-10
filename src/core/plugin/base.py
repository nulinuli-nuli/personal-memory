"""Base plugin class with common functionality."""
from typing import Optional
from src.core.plugin.interface import IPlugin


class BasePlugin(IPlugin):
    """Base plugin class providing common functionality."""

    def __init__(self):
        self.db = None
        self.ai = None
        self.repository = None

    async def initialize(self, db_session, ai_provider):
        """Initialize plugin."""
        self.db = db_session
        self.ai = ai_provider
        self.repository = self._create_repository()

    def _create_repository(self):
        """Subclass implements repository creation."""
        raise NotImplementedError

    async def shutdown(self):
        """Shutdown plugin - subclasses can override for cleanup."""
        pass
