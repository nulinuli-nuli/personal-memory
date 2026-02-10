"""Conversation context repository."""
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from src.shared.models import ConversationContext, ConversationTurn
from src.storage.repositories.base import BaseRepository


class ContextRepository(BaseRepository[ConversationContext]):
    """Conversation context repository."""

    def __init__(self, db: Session):
        super().__init__(ConversationContext, db)

    def get_context(self, user_id: int) -> Optional[ConversationContext]:
        """
        Get user context.

        Args:
            user_id: User ID

        Returns:
            Conversation context or None
        """
        from sqlalchemy import select

        result = self.db.execute(
            select(ConversationContext).filter(ConversationContext.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def get_or_create_context(self, user_id: int) -> ConversationContext:
        """
        Get or create user context.

        Args:
            user_id: User ID

        Returns:
            Conversation context
        """
        context = self.get_context(user_id)
        if not context:
            context = ConversationContext(user_id=user_id)
            self.db.add(context)
            self.db.commit()
            self.db.refresh(context)
        return context

    def update_context(self, user_id: int, **updates):
        """
        Update context.

        Args:
            user_id: User ID
            **updates: Fields to update

        Returns:
            Updated context
        """
        context = self.get_or_create_context(user_id)
        for key, value in updates.items():
            setattr(context, key, value)
        context.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(context)
        return context

    def add_turn(self, user_id: int, turn_data: dict) -> ConversationTurn:
        """
        Add conversation turn.

        Args:
            user_id: User ID
            turn_data: Turn data

        Returns:
            Created turn
        """
        # Rename metadata to turn_metadata if present
        if "metadata" in turn_data:
            turn_data["turn_metadata"] = turn_data.pop("metadata")

        turn = ConversationTurn(user_id=user_id, **turn_data)
        self.db.add(turn)

        # Only keep last 10 turns per user
        recent_turns = self.db.query(ConversationTurn).filter(
            ConversationTurn.user_id == user_id
        ).order_by(ConversationTurn.timestamp.desc()).offset(10).all()

        for old_turn in recent_turns:
            self.db.delete(old_turn)

        self.db.commit()
        self.db.refresh(turn)
        return turn

    def get_recent_turns(self, user_id: int, limit: int = 10) -> List[ConversationTurn]:
        """
        Get recent conversation turns.

        Args:
            user_id: User ID
            limit: Maximum number of turns to return

        Returns:
            List of conversation turns
        """
        from sqlalchemy import select

        result = self.db.execute(
            select(ConversationTurn)
            .filter(ConversationTurn.user_id == user_id)
            .order_by(ConversationTurn.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
