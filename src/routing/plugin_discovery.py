"""Plugin discovery and loading."""
from pathlib import Path
from typing import List
import importlib
import logging

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Plugin discovery and loading."""

    def __init__(self, plugin_dir: str = "src/core/plugins"):
        """
        Initialize plugin discovery.

        Args:
            plugin_dir: Plugin directory path
        """
        self.plugin_dir = Path(plugin_dir)

    def discover_plugins(self) -> List[str]:
        """
        Scan plugin directory.

        Returns:
            List of plugin names
        """
        plugin_names = []

        if not self.plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {self.plugin_dir}")
            return plugin_names

        for path in self.plugin_dir.iterdir():
            if path.is_dir() and (path / "plugin.py").exists():
                plugin_names.append(path.name)

        logger.info(f"Discovered {len(plugin_names)} plugins: {plugin_names}")
        return plugin_names

    def load_plugin_module(self, plugin_name: str):
        """
        Dynamically load plugin module.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin module
        """
        module_path = f"src.core.plugins.{plugin_name}.plugin"
        try:
            return importlib.import_module(module_path)
        except ImportError as e:
            logger.error(f"Failed to import plugin module '{module_path}': {e}")
            raise
