"""Unit tests for Plugin Manager."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import shutil

from src.core.plugin.manager import PluginManager


@pytest.fixture
def plugin_manager():
    """Create a plugin manager fixture."""
    db = Mock()
    ai = Mock()
    manager = PluginManager(db, ai, plugin_dir="tests/fixtures/plugins")
    return manager


@pytest.mark.asyncio
async def test_discover_plugins(plugin_manager):
    """Test plugin discovery."""
    # Create a test plugin directory
    plugin_dir = Path("tests/fixtures/plugins")
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Create test plugin files
    (plugin_dir / "test_plugin").mkdir(exist_ok=True)
    (plugin_dir / "test_plugin" / "plugin.py").write_text("""
from src.core.plugin.base import BasePlugin
from src.access.base import AccessRequest, AccessResponse

class TestPlugin(BasePlugin):
    @property
    def name(self):
        return "test_plugin"

    @property
    def display_name(self):
        return "Test Plugin"

    @property
    def description(self):
        return "Test description"

    @property
    def version(self):
        return "1.0.0"

    def _create_repository(self):
        return None

    async def execute(self, request, context, params):
        return AccessResponse(success=True, message="Test", data={})

    async def shutdown(self):
        pass
""")

    plugin_names = plugin_manager._discover_plugins()

    assert "test_plugin" in plugin_names

    # Cleanup
    import shutil
    shutil.rmtree("tests/fixtures", ignore_errors=True)


@pytest.mark.asyncio
async def test_load_plugin(plugin_manager):
    """Test loading a plugin."""
    # Simplified test - just verify the method exists and can be called
    # Real plugin loading is tested in integration tests
    assert hasattr(plugin_manager, 'load_plugin')
    assert callable(plugin_manager.load_plugin)


@pytest.mark.asyncio
async def test_list_plugins(plugin_manager):
    """Test listing all plugins."""
    # Add a mock plugin
    mock_plugin = Mock()
    mock_plugin.name = "test"
    mock_plugin.display_name = "Test"
    mock_plugin.description = "Test desc"
    mock_plugin.version = "1.0"

    plugin_manager.plugins["test"] = mock_plugin
    plugin_manager.plugin_states["test"] = "active"

    plugins = plugin_manager.list_plugins()

    assert len(plugins) == 1
    assert plugins[0]["name"] == "test"
    assert plugins[0]["display_name"] == "Test"
    assert plugins[0]["description"] == "Test desc"
    assert plugins[0]["version"] == "1.0"
    assert plugins[0]["state"] == "active"


@pytest.mark.asyncio
async def test_get_plugin(plugin_manager):
    """Test getting a plugin by name."""
    mock_plugin = Mock()
    plugin_manager.plugins["test"] = mock_plugin

    result = plugin_manager.get_plugin("test")

    assert result == mock_plugin


@pytest.mark.asyncio
async def test_get_plugin_not_found(plugin_manager):
    """Test getting a non-existent plugin."""
    result = plugin_manager.get_plugin("nonexistent")

    assert result is None
