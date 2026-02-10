"""Unit tests for Router service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.routing.router import RouterService
from src.access.base import AccessRequest, AccessResponse
from src.core.plugin.manager import PluginManager


@pytest.fixture
def router_service():
    """Create a router service fixture."""
    db = Mock()
    plugin_manager = Mock()
    ai_provider = Mock()

    # Mock plugin manager
    mock_plugin = Mock()
    mock_plugin.name = "finance"
    mock_plugin.execute = AsyncMock(return_value=AccessResponse(
        success=True,
        message="测试成功",
        data={},
        error=None,
        metadata={}
    ))
    plugin_manager.get_plugin = Mock(return_value=mock_plugin)
    plugin_manager.list_plugins = Mock(return_value=[
        {
            "name": "finance",
            "description": "财务管理"
        },
        {
            "name": "work",
            "description": "工作管理"
        }
    ])

    # Mock AI
    ai_provider.chat = AsyncMock(return_value={
        "success": True,
        "plugin_name": "finance",
        "action": "add",
        "params": {},
        "reasoning": "测试"
    })

    # Mock context repository
    with patch('src.routing.router.ContextRepository'):
        service = RouterService(db, plugin_manager, ai_provider)
        return service


@pytest.mark.asyncio
async def test_route_to_finance_plugin(router_service):
    """Test routing to finance plugin."""
    request = AccessRequest(
        user_id="1",
        input_text="今天花了50块",
        channel="cli",
        context={},
        metadata={}
    )

    # Mock context repo methods
    router_service.context_repo.get_context = Mock(return_value=None)
    router_service.context_repo.get_recent_turns = Mock(return_value=[])
    router_service.context_repo.add_turn = Mock()

    response = await router_service.route(request)

    assert response.success == True
    assert "测试成功" in response.message
    router_service.plugin_manager.get_plugin.assert_called_once_with("finance")


@pytest.mark.asyncio
async def test_route_ai_decision_failure(router_service):
    """Test routing when AI decision fails."""
    request = AccessRequest(
        user_id="1",
        input_text="测试",
        channel="cli",
        context={},
        metadata={}
    )

    # Mock AI failure
    router_service.ai.chat = AsyncMock(return_value={
        "success": False,
        "error": "AI错误"
    })

    # Mock context repo methods
    router_service.context_repo.get_context = Mock(return_value=None)
    router_service.context_repo.get_recent_turns = Mock(return_value=[])

    response = await router_service.route(request)

    assert response.success == False
    assert "路由决策失败" in response.error or "AI错误" in response.error


@pytest.mark.asyncio
async def test_route_plugin_not_found(router_service):
    """Test routing when plugin is not found."""
    request = AccessRequest(
        user_id="1",
        input_text="测试",
        channel="cli",
        context={},
        metadata={}
    )

    # Mock AI returns non-existent plugin
    router_service.ai.chat = AsyncMock(return_value={
        "success": True,
        "plugin_name": "nonexistent",
        "action": "add",
        "params": {}
    })

    router_service.plugin_manager.get_plugin = Mock(return_value=None)
    router_service.context_repo.get_context = Mock(return_value=None)
    router_service.context_repo.get_recent_turns = Mock(return_value=[])

    response = await router_service.route(request)

    assert response.success == False
    assert "未找到插件" in response.error


@pytest.mark.asyncio
async def test_build_router_prompt(router_service):
    """Test router prompt building."""
    plugins = [
        {"name": "finance", "description": "财务管理"},
        {"name": "work", "description": "工作管理"}
    ]

    prompt = router_service._build_router_prompt(
        "今天花了50块",
        [],
        plugins
    )

    assert "今天花了50块" in prompt
    assert "finance" in prompt
    assert "work" in prompt
    assert "财务管理" in prompt


@pytest.mark.asyncio
async def test_format_context(router_service):
    """Test context formatting."""
    from src.shared.models import ConversationTurn
    from datetime import datetime

    turns = [
        Mock(
            spec=ConversationTurn,
            user_input="花了50块",
            response="已记录",
            domain="finance"
        ),
        Mock(
            spec=ConversationTurn,
            user_input="工作了8小时",
            response="已记录",
            domain="work"
        )
    ]

    formatted = router_service._format_context(turns)

    assert "花了50块" in formatted
    assert "工作了8小时" in formatted
    assert "[finance]" in formatted
    assert "[work]" in formatted
