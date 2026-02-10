"""Unit tests for Work plugin."""
import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal

from src.core.plugins.work.plugin import WorkPlugin
from src.access.base import AccessRequest, AccessResponse


@pytest.fixture
def work_plugin():
    """Create a work plugin fixture."""
    plugin = WorkPlugin()
    plugin.db = Mock()
    plugin.ai = Mock()
    plugin.repository = Mock()
    return plugin


@pytest.mark.asyncio
async def test_plugin_properties(work_plugin):
    """Test plugin properties."""
    assert work_plugin.name == "work"
    assert work_plugin.display_name == "工作管理"
    assert "工作" in work_plugin.description
    assert work_plugin.version == "1.0.0"


@pytest.mark.asyncio
async def test_add_record_success(work_plugin):
    """Test successful work record addition."""
    request = AccessRequest(
        user_id="1",
        input_text="今天工作8小时，完成了用户认证模块",
        channel="cli",
        context={},
        metadata={}
    )

    # Mock AI parsing result
    work_plugin.ai.parse = Mock(return_value={
        "task_name": "完成用户认证模块",
        "duration_hours": 8.0,
        "task_type": "开发",
        "action": "add"
    })

    # Mock repository create
    mock_record = Mock()
    mock_record.id = 1
    mock_record.duration_hours = Decimal("8.0")
    mock_record.task_name = "完成用户认证模块"
    work_plugin.repository.create = Mock(return_value=mock_record)

    response = await work_plugin.execute(request, {}, {})

    assert response.success == True
    assert "已添加" in response.message
    assert response.data["duration"] == 8.0


@pytest.mark.asyncio
async def test_add_record_missing_task_name(work_plugin):
    """Test work record addition without task name."""
    request = AccessRequest(
        user_id="1",
        input_text="测试",
        channel="cli",
        context={},
        metadata={}
    )

    work_plugin.ai.parse = Mock(return_value={
        "action": "add"
    })

    response = await work_plugin.execute(request, {}, {})

    assert response.success == False
    assert "缺少任务名称" in response.error


@pytest.mark.asyncio
async def test_add_record_invalid_duration(work_plugin):
    """Test work record addition with invalid duration."""
    request = AccessRequest(
        user_id="1",
        input_text="测试",
        channel="cli",
        context={},
        metadata={}
    )

    work_plugin.ai.parse = Mock(return_value={
        "task_name": "测试任务",
        "duration_hours": 0,
        "action": "add"
    })

    response = await work_plugin.execute(request, {}, {})

    assert response.success == False
    assert "工作时长必须大于0" in response.error


@pytest.mark.asyncio
async def test_query_records(work_plugin):
    """Test query work records."""
    request = AccessRequest(
        user_id="1",
        input_text="查询本周工作",
        channel="cli",
        context={},
        metadata={}
    )

    work_plugin.ai.parse = Mock(return_value={
        "action": "query"
    })

    work_plugin.repository.get_all = Mock(return_value=[])

    response = await work_plugin.execute(request, {}, {})

    assert response.success == True
    assert "暂无" in response.message
