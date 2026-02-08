"""Record service for business logic."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.ai.parser import TextParser
from src.core.exceptions import InvalidInputError, AIServiceError
from src.core.models import User
from src.repositories.finance_repo import FinanceRepository
from src.repositories.health_repo import HealthRepository
from src.repositories.work_repo import WorkRepository
from src.repositories.leisure_repo import LeisureRepository


class RecordService:
    """Service for managing records."""

    def __init__(self, db: Session, user_id: int | None = None):
        """
        Initialize service.

        Args:
            db: Database session
            user_id: Current user ID (None for default user)
        """
        self.db = db
        self.user_id = user_id or self._get_or_create_default_user()
        self.parser = TextParser()

        # Initialize repositories
        self.finance_repo = FinanceRepository(db)
        self.health_repo = HealthRepository(db)
        self.work_repo = WorkRepository(db)
        self.leisure_repo = LeisureRepository(db)

    def _get_or_create_default_user(self) -> int:
        """Get or create default user."""
        # Try to get user with ID 1
        user = self.db.get(User, 1)
        if user:
            return 1

        # Create default user
        user = User(id=1, username="default")
        self.db.add(user)
        self.db.commit()
        return 1

    async def add_finance_from_text(self, text: str, record_date: date | None = None):
        """
        Add finance record from natural language text.

        Args:
            text: Natural language input
            record_date: Optional date (defaults to today)

        Returns:
            Created finance record
        """
        try:
            parsed = self.parser.parse_finance(text, record_date)
        except Exception as e:
            raise AIServiceError(f"Failed to parse text: {str(e)}")

        # Validate parsed data
        if parsed.get("type") not in ["income", "expense"]:
            raise InvalidInputError("Invalid record type. Must be 'income' or 'expense'.")

        amount = Decimal(str(parsed.get("amount", 0)))
        if amount <= 0:
            raise InvalidInputError("Amount must be positive.")

        record_date_str = parsed.get("record_date")
        if record_date_str:
            from datetime import datetime
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()

        return self.finance_repo.create(
            user_id=self.user_id,
            type=parsed["type"],
            amount=amount,
            category=parsed.get("category"),
            description=parsed.get("description"),
            raw_text=text,
            record_date=record_date or date.today(),
        )

    async def add_health_from_text(self, text: str, record_date: date | None = None):
        """
        Add health record from natural language text.

        Args:
            text: Natural language input
            record_date: Optional date (defaults to today)

        Returns:
            Created health record
        """
        try:
            parsed = self.parser.parse_health(text, record_date)
        except Exception as e:
            raise AIServiceError(f"Failed to parse text: {str(e)}")

        # Parse date
        record_date_str = parsed.get("record_date")
        if record_date_str:
            from datetime import datetime
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()

        # Parse times if provided
        wake_time = None
        bed_time = None
        if parsed.get("wake_time"):
            from datetime import datetime
            wake_time = datetime.strptime(parsed["wake_time"], "%H:%M").time()
        if parsed.get("bed_time"):
            from datetime import datetime
            bed_time = datetime.strptime(parsed["bed_time"], "%H:%M").time()

        # Check if record exists for this date and update it
        existing = self.health_repo.get_by_date(self.user_id, record_date or date.today())
        if existing:
            # Update existing record
            if parsed.get("sleep_hours"):
                existing.sleep_hours = Decimal(str(parsed["sleep_hours"]))
            if parsed.get("sleep_quality"):
                existing.sleep_quality = parsed["sleep_quality"]
            if wake_time:
                existing.wake_time = wake_time
            if bed_time:
                existing.bed_time = bed_time
            if parsed.get("mood"):
                existing.mood = parsed["mood"]
            if parsed.get("notes"):
                existing.notes = parsed["notes"]
            existing.raw_text = (existing.raw_text or "") + "\n" + text
            self.db.commit()
            self.db.refresh(existing)
            return existing

        return self.health_repo.create(
            user_id=self.user_id,
            record_date=record_date or date.today(),
            sleep_hours=Decimal(str(parsed["sleep_hours"])) if parsed.get("sleep_hours") else None,
            sleep_quality=parsed.get("sleep_quality"),
            wake_time=wake_time,
            bed_time=bed_time,
            mood=parsed.get("mood"),
            notes=parsed.get("notes"),
            raw_text=text,
        )

    async def add_work_from_text(self, text: str, record_date: date | None = None):
        """
        Add work record from natural language text.

        Args:
            text: Natural language input
            record_date: Optional date (defaults to today)

        Returns:
            Created work record
        """
        try:
            parsed = self.parser.parse_work(text, record_date)
        except Exception as e:
            raise AIServiceError(f"Failed to parse text: {str(e)}")

        # Validate
        if not parsed.get("task_name"):
            raise InvalidInputError("Could not extract task name from text.")

        duration_hours = Decimal(str(parsed.get("duration_hours", 0)))
        if duration_hours <= 0:
            raise InvalidInputError("Duration must be positive.")

        # Parse date
        record_date_str = parsed.get("record_date")
        if record_date_str:
            from datetime import datetime
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()

        return self.work_repo.create(
            user_id=self.user_id,
            record_date=record_date or date.today(),
            task_name=parsed["task_name"],
            duration_hours=duration_hours,
            value_description=parsed.get("value_description"),
            tags=parsed.get("tags"),
            status=parsed.get("status", "completed"),
            raw_text=text,
        )

    async def add_leisure_from_text(self, text: str, record_date: date | None = None):
        """
        Add leisure record from natural language text.

        Args:
            text: Natural language input
            record_date: Optional date (defaults to today)

        Returns:
            Created leisure record
        """
        try:
            parsed = self.parser.parse_leisure(text, record_date)
        except Exception as e:
            raise AIServiceError(f"Failed to parse text: {str(e)}")

        # Validate
        if not parsed.get("activity"):
            raise InvalidInputError("Could not extract activity from text.")

        duration_hours = Decimal(str(parsed.get("duration_hours", 0)))
        if duration_hours <= 0:
            raise InvalidInputError("Duration must be positive.")

        # Parse date
        record_date_str = parsed.get("record_date")
        if record_date_str:
            from datetime import datetime
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()

        return self.leisure_repo.create(
            user_id=self.user_id,
            record_date=record_date or date.today(),
            activity=parsed["activity"],
            duration_hours=duration_hours,
            enjoyment_score=parsed.get("enjoyment_score"),
            notes=parsed.get("notes"),
            raw_text=text,
        )

    def get_db_schema_for_ai(self) -> str:
        """
        Generate database schema documentation for AI use.

        Returns:
            Database schema as markdown string
        """
        return """
**Database Schema**

**finance_records** - 财务记录
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- type (TEXT) - 'income' or 'expense'
- amount (NUMERIC(10,2)) - 金额
- category (TEXT) - 分类: 餐饮, 交通, 购物, 娱乐, 住房, 医疗, 教育, 工资, 投资, 其他
- description (TEXT) - 描述
- record_date (DATE) - 记录日期

**health_records** - 健康记录
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- record_date (DATE, UNIQUE)
- sleep_hours (NUMERIC(4,2)) - 睡眠时长
- sleep_quality (TEXT) - 睡眠质量: 优, 良, 中, 差
- wake_time (TIME) - 起床时间
- bed_time (TIME) - 睡觉时间
- mood (TEXT) - 心情

**work_records** - 工作记录
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- record_date (DATE)
- task_name (TEXT) - 任务名称
- duration_hours (NUMERIC(5,2)) - 工作时长
- value_description (TEXT) - 价值描述
- tags (TEXT) - 标签
- status (TEXT) - 状态

**leisure_records** - 休闲记录
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- record_date (DATE)
- activity (TEXT) - 活动名称
- duration_hours (NUMERIC(5,2)) - 时长
- enjoyment_score (INTEGER) - 愉悦度 1-5

Notes:
- Always filter by user_id = {user_id}
- Date format: 'YYYY-MM-DD'
- Use SQLite date functions: date(), date('now', '-7 days')
"""
