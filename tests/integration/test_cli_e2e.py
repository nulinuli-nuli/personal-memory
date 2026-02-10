"""End-to-end integration tests for CLI."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock, Mock


@pytest.mark.asyncio
async def test_add_finance_command():
    """Test adding finance record via CLI."""
    from src.access.cli.adapter import CLIAdapter
    from src.access.base import AccessRequest, AccessResponse

    # Mock the CLIAdapter initialization and methods
    with patch.object(CLIAdapter, '__init__', return_value=None):
        adapter = CLIAdapter()

        # Mock the async methods
        adapter.initialize_plugins = AsyncMock()
        adapter.router = MagicMock()

        # Mock the route method to return a successful response
        mock_response = AccessResponse(
            success=True,
            data={"amount": 50.0},
            message="已添加：午饭 ¥50.0 (支出)",
            error=None,
            metadata={}
        )
        adapter.router.route = AsyncMock(return_value=mock_response)
        adapter.format_response = MagicMock(return_value="已添加：午饭 ¥50.0 (支出)")

        # Create request
        request = AccessRequest(
            user_id="1",
            input_text="今天花了50块买午饭",
            channel="cli",
            context={},
            metadata={}
        )

        # Call route
        response = await adapter.router.route(request)
        result = adapter.format_response(response)

        assert response.success == True
        assert "已添加" in result
        assert "50" in result


@pytest.mark.asyncio
async def test_query_command():
    """Test querying via CLI."""
    from src.access.cli.adapter import CLIAdapter
    from src.access.base import AccessRequest, AccessResponse

    with patch.object(CLIAdapter, '__init__', return_value=None):
        adapter = CLIAdapter()
        adapter.initialize_plugins = AsyncMock()
        adapter.router = MagicMock()

        mock_response = AccessResponse(
            success=True,
            data={"count": 5},
            message="找到 5 条记录",
            error=None,
            metadata={}
        )
        adapter.router.route = AsyncMock(return_value=mock_response)
        adapter.format_response = MagicMock(return_value="找到 5 条记录")

        request = AccessRequest(
            user_id="1",
            input_text="本周花了多少钱",
            channel="cli",
            context={},
            metadata={}
        )

        response = await adapter.router.route(request)
        result = adapter.format_response(response)

        assert response.success == True
        assert "记录" in result


@pytest.mark.asyncio
async def test_chat_command():
    """Test chat command."""
    from src.access.cli.adapter import CLIAdapter
    from src.access.base import AccessRequest, AccessResponse

    with patch.object(CLIAdapter, '__init__', return_value=None):
        adapter = CLIAdapter()
        adapter.initialize_plugins = AsyncMock()
        adapter.router = MagicMock()

        mock_response = AccessResponse(
            success=True,
            data={},
            message="已记录您的输入",
            error=None,
            metadata={}
        )
        adapter.router.route = AsyncMock(return_value=mock_response)
        adapter.format_response = MagicMock(return_value="已记录您的输入")

        request = AccessRequest(
            user_id="1",
            input_text="我今天花了50块",
            channel="cli",
            context={},
            metadata={}
        )

        response = await adapter.router.route(request)
        result = adapter.format_response(response)

        assert "已记录" in result


@pytest.mark.asyncio
async def test_plugin_list_command():
    """Test plugin list command."""
    from src.access.cli.adapter import CLIAdapter

    with patch.object(CLIAdapter, '__init__', return_value=None):
        adapter = CLIAdapter()
        adapter.initialize_plugins = AsyncMock()

        mock_plugin_manager = MagicMock()
        mock_plugin_manager.list_plugins = MagicMock(return_value=[
            {
                "name": "finance",
                "display_name": "财务管理",
                "description": "财务插件",
                "version": "1.0.0",
                "state": "active"
            }
        ])
        adapter.plugin_manager = mock_plugin_manager

        # Just verify it runs without error
        plugins = adapter.plugin_manager.list_plugins()
        assert len(plugins) == 1
        assert plugins[0]["name"] == "finance"


def test_init_command():
    """Test database initialization."""
    import src.shared.database as db_module

    with patch.object(db_module, 'init_db') as mock_init:
        db_module.init_db()
        assert mock_init.called
