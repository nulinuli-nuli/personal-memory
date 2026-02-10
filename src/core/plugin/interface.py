"""Plugin interface - all plugins must implement this."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.access.base import AccessRequest, AccessResponse


class IPlugin(ABC):
    """Plugin interface - all plugins must implement this interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin unique identifier."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Plugin display name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Plugin functionality description (used for AI routing decisions)."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass

    @abstractmethod
    async def initialize(self, db_session, ai_provider):
        """Initialize plugin with database session and AI provider."""
        pass

    @abstractmethod
    async def execute(
        self,
        request: AccessRequest,
        context: Optional[Dict[str, Any]],
        params: Dict[str, Any]
    ) -> AccessResponse:
        """
        Execute plugin functionality.

        Args:
            request: User request
            context: Conversation context
            params: Parameters passed from routing layer (AI-parsed parameters)

        Returns:
            Response result
        """
        pass

    @abstractmethod
    async def shutdown(self):
        """Shutdown plugin and cleanup resources."""
        pass
