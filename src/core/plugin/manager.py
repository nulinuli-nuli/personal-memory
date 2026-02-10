"""Plugin manager - handles plugin lifecycle and hot-reload."""
from typing import Dict, List, Optional, Any
from pathlib import Path
import importlib
import sys
import logging

from src.core.plugin.interface import IPlugin
from src.shared.config import get_project_root

logger = logging.getLogger(__name__)


class PluginManager:
    """Plugin manager supporting hot-reload."""

    def __init__(self, db_session, ai_provider, plugin_dir: str = "src/core/plugins"):
        self.db = db_session
        self.ai = ai_provider
        # Use absolute path to plugins directory
        self.plugin_dir = get_project_root() / plugin_dir
        self.plugins: Dict[str, IPlugin] = {}
        self.plugin_states: Dict[str, str] = {}

    async def discover_and_load_all(self) -> int:
        """
        Discover and load all plugins from the plugin directory.

        Returns:
            Number of plugins loaded
        """
        plugin_names = self._discover_plugins()
        loaded_count = 0

        for plugin_name in plugin_names:
            try:
                success = await self.load_plugin(plugin_name)
                if success:
                    loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load plugin '{plugin_name}': {e}")
                self.plugin_states[plugin_name] = "error"

        return loaded_count

    def _discover_plugins(self) -> List[str]:
        """Scan plugin directory."""
        plugin_names = []

        if not self.plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {self.plugin_dir}")
            return plugin_names

        for path in self.plugin_dir.iterdir():
            if path.is_dir() and (path / "plugin.py").exists():
                plugin_names.append(path.name)

        logger.info(f"Discovered {len(plugin_names)} plugins: {plugin_names}")
        return plugin_names

    async def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a plugin by name.

        Args:
            plugin_name: Name of the plugin directory

        Returns:
            True if loaded successfully
        """
        try:
            # Import the plugin module
            module_path = f"src.core.plugins.{plugin_name}.plugin"
            module = importlib.import_module(module_path)

            # Get the plugin class (expects class name like {Name}Plugin)
            plugin_class_name = f"{plugin_name.capitalize()}Plugin"
            if not hasattr(module, plugin_class_name):
                # Fallback: look for any class ending with Plugin
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                            attr_name.endswith("Plugin") and
                            attr_name != "BasePlugin" and
                            attr_name != "IPlugin"):
                        plugin_class = attr
                        break
                else:
                    raise AttributeError(f"No plugin class found in {module_path}")
            else:
                plugin_class = getattr(module, plugin_class_name)

            # Create plugin instance
            plugin_instance = plugin_class()

            # Initialize plugin
            await plugin_instance.initialize(self.db, self.ai)

            # Register plugin
            self.plugins[plugin_name] = plugin_instance
            self.plugin_states[plugin_name] = "active"

            logger.info(f"Loaded plugin: {plugin_instance.display_name} v{plugin_instance.version}")
            return True

        except Exception as e:
            logger.error(f"Error loading plugin '{plugin_name}': {e}", exc_info=True)
            self.plugin_states[plugin_name] = "error"
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if unloaded successfully
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin '{plugin_name}' not loaded")
            return False

        try:
            plugin = self.plugins[plugin_name]
            await plugin.shutdown()

            del self.plugins[plugin_name]
            self.plugin_states[plugin_name] = "unloaded"

            logger.info(f"Unloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Error unloading plugin '{plugin_name}': {e}", exc_info=True)
            self.plugin_states[plugin_name] = "error"
            return False

    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        Hot-reload a plugin.

        Args:
            plugin_name: Name of the plugin to reload

        Returns:
            True if reloaded successfully
        """
        logger.info(f"Reloading plugin: {plugin_name}")

        # Unload if already loaded
        if plugin_name in self.plugins:
            await self.unload_plugin(plugin_name)

        # Clear module cache
        module_key = f"src.core.plugins.{plugin_name}.plugin"
        if module_key in sys.modules:
            del sys.modules[module_key]

        # Also clear parent module caches
        parent_key = f"src.core.plugins.{plugin_name}"
        if parent_key in sys.modules:
            del sys.modules[parent_key]

        # Reload the plugin
        return await self.load_plugin(plugin_name)

    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """
        Get plugin instance by name.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin instance or None
        """
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all plugins with their information.

        Returns:
            List of plugin information dictionaries
        """
        result = []
        for name, plugin in self.plugins.items():
            result.append({
                "name": plugin.name,
                "display_name": plugin.display_name,
                "description": plugin.description,
                "version": plugin.version,
                "state": self.plugin_states.get(name, "unknown")
            })
        return result
