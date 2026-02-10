"""Plugin registry for managing plugin metadata."""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PluginInfo:
    """Plugin metadata."""
    name: str
    display_name: str
    description: str
    version: str
    author: Optional[str] = None
    dependencies: Optional[List[str]] = None


class PluginRegistry:
    """Registry for plugin metadata."""

    def __init__(self):
        self._plugins: Dict[str, PluginInfo] = {}

    def register(self, info: PluginInfo):
        """Register plugin metadata."""
        self._plugins[info.name] = info

    def get(self, name: str) -> Optional[PluginInfo]:
        """Get plugin metadata by name."""
        return self._plugins.get(name)

    def list_all(self) -> List[PluginInfo]:
        """List all registered plugins."""
        return list(self._plugins.values())

    def unregister(self, name: str) -> bool:
        """Unregister plugin."""
        if name in self._plugins:
            del self._plugins[name]
            return True
        return False
