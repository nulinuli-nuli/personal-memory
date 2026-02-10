"""Base repository with common CRUD operations."""
from typing import Generic, TypeVar, List, Optional, Type

from sqlalchemy.orm import Session
from sqlalchemy import select

from src.shared.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def create(self, **kwargs) -> ModelType:
        """
        Create a new record.

        Args:
            **kwargs: Model field values

        Returns:
            Created model instance
        """
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_id(self, record_id: int) -> Optional[ModelType]:
        """
        Get record by ID.

        Args:
            record_id: Record ID

        Returns:
            Model instance or None if not found
        """
        return self.db.get(self.model, record_id)

    def get_all(
        self,
        user_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ModelType]:
        """
        Get all records with optional filtering.

        Args:
            user_id: Filter by user ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of model instances
        """
        query = select(self.model)

        if hasattr(self.model, "user_id") and user_id is not None:
            query = query.where(self.model.user_id == user_id)

        query = query.order_by(self.model.created_at.desc()).limit(limit).offset(offset)

        result = self.db.execute(query)
        return list(result.scalars().all())

    def delete(self, record_id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            record_id: Record ID

        Returns:
            True if deleted, False if not found
        """
        db_obj = self.get_by_id(record_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
