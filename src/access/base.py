"""Base classes for access layer adapters."""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


@dataclass
class AccessRequest:
    """Unified access request format."""
    user_id: str
    input_text: str
    channel: str  # "cli" | "feishu"
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessResponse:
    """Unified response format."""
    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAdapter(ABC):
    """Adapter base class for different access channels."""

    @abstractmethod
    async def process_request(self, request: AccessRequest) -> AccessResponse:
        """Process request and return response."""
        pass

    @abstractmethod
    def format_response(self, response: AccessResponse) -> Any:
        """Format response for specific channel."""
        pass
