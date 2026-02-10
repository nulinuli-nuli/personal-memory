"""Work record repository."""
from datetime import date
from decimal import Decimal
from typing import List

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from src.shared.models import WorkRecord
from src.storage.repositories.base import BaseRepository


class WorkRepository(BaseRepository[WorkRecord]):
    """Repository for work records."""

    def __init__(self, db: Session):
        """Initialize repository."""
        super().__init__(WorkRecord, db)

    def create(
        self,
        user_id: int,
        record_date: date,
        task_type: str,
        task_name: str,
        duration_hours: Decimal,
        value_description: str | None = None,
        project_id: int | None = None,
        priority: str = "medium",
        status: str = "completed",
        start_time: object | None = None,
        end_time: object | None = None,
        tags: list | None = None,
        raw_text: str | None = None,
    ) -> WorkRecord:
        """
        Create a work record.

        Args:
            user_id: User ID
            record_date: Record date
            task_type: Task type (开发/会议/文档/学习/管理/协作)
            task_name: Task name
            duration_hours: Duration in hours
            value_description: Value description
            project_id: Project ID
            priority: Priority (high/medium/low)
            status: Task status
            start_time: Start time
            end_time: End time
            tags: Tags list
            raw_text: Original input text

        Returns:
            Created work record
        """
        db_obj = WorkRecord(
            user_id=user_id,
            record_date=record_date,
            task_type=task_type,
            task_name=task_name,
            duration_hours=duration_hours,
            value_description=value_description,
            project_id=project_id,
            priority=priority,
            status=status,
            start_time=start_time,
            end_time=end_time,
            tags=tags,
            raw_text=raw_text,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_date_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> List[WorkRecord]:
        """
        Get records within a date range.

        Args:
            user_id: User ID
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of work records
        """
        query = (
            select(WorkRecord)
            .where(
                and_(
                    WorkRecord.user_id == user_id,
                    WorkRecord.record_date >= start_date,
                    WorkRecord.record_date <= end_date,
                )
            )
            .order_by(WorkRecord.record_date.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_total_hours(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Decimal:
        """
        Get total work hours.

        Args:
            user_id: User ID
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Total hours worked
        """
        query = select(func.sum(WorkRecord.duration_hours)).where(
            WorkRecord.user_id == user_id
        )

        if start_date:
            query = query.where(WorkRecord.record_date >= start_date)
        if end_date:
            query = query.where(WorkRecord.record_date <= end_date)

        result = self.db.execute(query)
        return result.scalar() or Decimal("0")

    def get_by_tag(
        self,
        user_id: int,
        tag: str,
        limit: int = 100,
    ) -> List[WorkRecord]:
        """
        Get records by tag.

        Args:
            user_id: User ID
            tag: Tag to search for
            limit: Maximum records to return

        Returns:
            List of work records
        """
        query = (
            select(WorkRecord)
            .where(
                and_(
                    WorkRecord.user_id == user_id,
                    WorkRecord.tags.contains(tag),
                )
            )
            .order_by(WorkRecord.record_date.desc())
            .limit(limit)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())
