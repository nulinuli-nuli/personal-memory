"""User repository for Feishu integration."""
from typing import Optional

from sqlalchemy.orm import Session

from src.core.models import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user records."""

    def __init__(self, db: Session):
        """Initialize repository."""
        super().__init__(User, db)

    def get_by_feishu_id(self, feishu_user_id: str) -> Optional[User]:
        """
        Get user by Feishu user ID.

        Args:
            feishu_user_id: Feishu user ID

        Returns:
            User instance or None if not found
        """
        query = select(User).where(User.feishu_user_id == feishu_user_id)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_or_create_by_feishu(self, feishu_user_id: str, username: str | None = None) -> User:
        """
        Get existing user or create new one by Feishu ID.

        NOTE: All Feishu users are mapped to the same default user (ID=1)
        to ensure data consistency across CLI and Feishu bot.

        Args:
            feishu_user_id: Feishu user ID (not used, always returns ID=1)
            username: Optional username (not used)

        Returns:
            User instance (always returns user ID 1)
        """
        # Always return the default user (ID=1) for consistency
        # This ensures that records added via Feishu are visible in CLI
        return self.get_or_create_default()

    def get_or_create_default(self) -> User:
        """
        Get or create default user (ID=1).

        Returns:
            Default user instance
        """
        user = self.db.get(User, 1)
        if user:
            return user

        # Create default user
        user = User(id=1, username="default")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


# Import at the end for type checking
from sqlalchemy import select
