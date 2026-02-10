"""Unit tests for Context Repository."""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from src.storage.context.repository import ContextRepository
from src.shared.models import ConversationContext, ConversationTurn


@pytest.fixture
def context_repository():
    """Create a context repository fixture."""
    db = Mock()
    return ContextRepository(db)


def test_get_context_found(context_repository):
    """Test getting existing context."""
    mock_context = Mock()
    mock_context.user_id = 1

    # Properly chain the mock calls
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_context
    context_repository.db.execute.return_value = mock_result

    result = context_repository.get_context(1)

    assert result == mock_context


def test_get_context_not_found(context_repository):
    """Test getting non-existent context."""
    # Create a proper mock chain
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    context_repository.db.execute.return_value = mock_result

    result = context_repository.get_context(999)

    assert result is None


def test_get_or_create_context_existing(context_repository):
    """Test get_or_create with existing context."""
    mock_context = Mock()
    context_repository.get_context = Mock(return_value=mock_context)

    result = context_repository.get_or_create_context(1)

    assert result == mock_context
    context_repository.db.add.assert_not_called()


def test_get_or_create_context_new(context_repository):
    """Test get_or_create with new context."""
    context_repository.get_context = Mock(return_value=None)
    context_repository.db.commit = Mock()
    context_repository.db.refresh = Mock()

    result = context_repository.get_or_create_context(1)

    assert result.user_id == 1
    context_repository.db.add.assert_called_once()


def test_update_context(context_repository):
    """Test updating context."""
    mock_context = Mock()
    mock_context.user_id = 1
    context_repository.get_or_create_context = Mock(return_value=mock_context)
    context_repository.db.commit = Mock()
    context_repository.db.refresh = Mock()

    result = context_repository.update_context(1, current_domain="finance")

    assert result == mock_context
    assert mock_context.current_domain == "finance"
    context_repository.db.commit.assert_called_once()


def test_add_turn(context_repository):
    """Test adding conversation turn."""
    context_repository.db.add = Mock()
    context_repository.db.commit = Mock()
    context_repository.db.refresh = Mock()

    # Mock query to return empty list (no old turns to delete)
    mock_query = Mock()
    mock_query.filter.return_value.order_by.return_value.offset.return_value.all.return_value = []
    context_repository.db.query.return_value = mock_query

    turn_data = {
        "user_input": "测试",
        "intent": "add",
        "domain": "finance",
        "response": "已记录"
    }

    result = context_repository.add_turn(1, turn_data)

    assert result.user_id == 1
    assert result.user_input == "测试"
    context_repository.db.add.assert_called_once()


def test_get_recent_turns(context_repository):
    """Test getting recent conversation turns."""
    mock_turns = [Mock(), Mock()]
    context_repository.db.execute.return_value.scalars.return_value.all.return_value = mock_turns

    result = context_repository.get_recent_turns(1, limit=10)

    assert result == mock_turns
