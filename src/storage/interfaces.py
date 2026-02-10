"""Repository interfaces."""
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

ModelType = TypeVar("ModelType")


class IRepository(ABC, Generic[ModelType]):
    """Repository interface."""

    @abstractmethod
    def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        pass

    @abstractmethod
    def get_by_id(self, record_id: int) -> Optional[ModelType]:
        """Get record by ID."""
        pass

    @abstractmethod
    def get_all(self, user_id: int, **filters) -> List[ModelType]:
        """Get all records with optional filtering."""
        pass

    @abstractmethod
    def update(self, record_id: int, **kwargs) -> Optional[ModelType]:
        """Update a record."""
        pass

    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """Delete a record."""
        pass
