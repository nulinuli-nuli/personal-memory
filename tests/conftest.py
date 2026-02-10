"""Pytest configuration and shared fixtures."""
import pytest
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    from unittest.mock import Mock
    from sqlalchemy.orm import Session

    return Mock(spec=Session)


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider."""
    from unittest.mock import Mock

    ai = Mock()
    ai.parse = Mock(return_value={})
    ai.chat = Mock(return_value={})
    return ai


@pytest.fixture
def sample_finance_data():
    """Sample finance record data."""
    return {
        "type": "expense",
        "amount": 50.0,
        "primary_category": "餐饮",
        "secondary_category": "午餐",
        "description": "午饭",
        "record_date": "2026-02-10"
    }


@pytest.fixture
def sample_work_data():
    """Sample work record data."""
    return {
        "task_name": "完成用户认证模块",
        "duration_hours": 8.0,
        "task_type": "开发",
        "record_date": "2026-02-10"
    }
