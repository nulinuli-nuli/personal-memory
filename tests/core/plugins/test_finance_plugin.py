"""Unit tests for Finance plugin."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from src.core.plugins.finance.plugin import FinancePlugin
from src.access.base import AccessRequest, AccessResponse


@pytest.fixture
def finance_plugin():
    """Create a finance plugin fixture."""
    plugin = FinancePlugin()
    plugin.db = Mock()
    plugin.ai = Mock()
    plugin.repository = Mock()
    return plugin


@pytest.mark.asyncio
async def test_plugin_properties(finance_plugin):
    """Test plugin properties."""
    assert finance_plugin.name == "finance"
    assert finance_plugin.display_name == "财务管理"
    assert "财务" in finance_plugin.description
    assert finance_plugin.version == "1.0.0"


@pytest.mark.asyncio
async def test_add_record_success(finance_plugin):
    """Test successful record addition."""
    request = AccessRequest(
        user_id="1",
        input_text="今天花了50块买午饭",
        channel="cli",
        context={},
        metadata={}
    )

    # Mock AI parsing result
    finance_plugin.ai.parse = Mock(return_value={
        "type": "expense",
        "amount": 50.0,
        "primary_category": "餐饮",
        "description": "午饭",
        "action": "add"
    })

    # Mock repository create
    mock_record = Mock()
    mock_record.id = 1
    mock_record.amount = Decimal("50.00")
    mock_record.description = "午饭"
    mock_record.primary_category = "餐饮"
    mock_record.type = "expense"
    finance_plugin.repository.create = Mock(return_value=mock_record)

    response = await finance_plugin.execute(request, {}, {})

    assert response.success == True
    assert "已添加" in response.message
    assert response.data["amount"] == 50.0


@pytest.mark.asyncio
async def test_add_record_invalid_type(finance_plugin):
    """Test record addition with invalid type."""
    request = AccessRequest(
        user_id="1",
        input_text="测试",
        channel="cli",
        context={},
        metadata={}
    )

    finance_plugin.ai.parse = Mock(return_value={
        "type": "invalid",
        "amount": 50.0,
        "action": "add"
    })

    response = await finance_plugin.execute(request, {}, {})

    assert response.success == False
    assert "无效的记录类型" in response.error


@pytest.mark.asyncio
async def test_add_record_invalid_amount(finance_plugin):
    """Test record addition with invalid amount."""
    request = AccessRequest(
        user_id="1",
        input_text="测试",
        channel="cli",
        context={},
        metadata={}
    )

    finance_plugin.ai.parse = Mock(return_value={
        "type": "expense",
        "amount": 0,
        "action": "add"
    })

    response = await finance_plugin.execute(request, {}, {})

    assert response.success == False
    assert "金额必须大于0" in response.error


@pytest.mark.asyncio
async def test_query_records(finance_plugin):
    """Test query records."""
    request = AccessRequest(
        user_id="1",
        input_text="查询本周支出",
        channel="cli",
        context={},
        metadata={}
    )

    finance_plugin.ai.parse = Mock(return_value={
        "action": "query"
    })

    finance_plugin.repository.get_all = Mock(return_value=[])

    response = await finance_plugin.execute(request, {}, {})

    assert response.success == True
    assert "暂无" in response.message


@pytest.mark.asyncio
async def test_parse_with_ai(finance_plugin):
    """Test AI parsing."""
    finance_plugin.ai.parse = Mock(return_value={
        "type": "expense",
        "amount": 100.0,
        "primary_category": "餐饮",
        "description": "测试"
    })

    result = await finance_plugin._parse_with_ai("花了100块")

    assert result["type"] == "expense"
    assert result["amount"] == 100.0
    finance_plugin.ai.parse.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown(finance_plugin):
    """Test plugin shutdown."""
    # Should not raise any exception
    await finance_plugin.shutdown()
