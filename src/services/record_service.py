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
from src.repositories.learning_repo import LearningRepository
from src.repositories.social_repo import SocialRepository
from src.repositories.goal_repo import GoalRepository, GoalProgressRepository


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
        self.learning_repo = LearningRepository(db)
        self.social_repo = SocialRepository(db)
        self.goal_repo = GoalRepository(db)
        self.goal_progress_repo = GoalProgressRepository(db)

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

        # Handle multiple records (AI may return a list)
        records = parsed if isinstance(parsed, list) else [parsed]

        created_records = []
        for record_data in records:
            # Validate parsed data
            if record_data.get("type") not in ["income", "expense"]:
                raise InvalidInputError("Invalid record type. Must be 'income' or 'expense'.")

            amount = Decimal(str(record_data.get("amount", 0)))
            if amount <= 0:
                raise InvalidInputError("Amount must be positive.")

            record_date_str = record_data.get("record_date")
            if record_date_str:
                from datetime import datetime
                record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()

            created = self.finance_repo.create(
                user_id=self.user_id,
                type=record_data["type"],
                amount=amount,
                primary_category=record_data.get("primary_category", "其他"),
                secondary_category=record_data.get("secondary_category"),
                description=record_data.get("description"),
                payment_method=record_data.get("payment_method"),
                merchant=record_data.get("merchant"),
                is_recurring=record_data.get("is_recurring", False),
                tags=record_data.get("tags"),
                raw_text=text,
                record_date=record_date or date.today(),
            )
            created_records.append(created)

        # Return the first record for backward compatibility, or all records
        return created_records[0] if len(created_records) == 1 else created_records

    async def add_health_from_text(self, text: str, record_date: date | None = None):
        """
        Add health record from natural language text (multi-indicator system).

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

        # Validate required fields
        if not parsed.get("indicator_type"):
            raise InvalidInputError("Could not extract indicator_type from text.")
        if not parsed.get("indicator_name"):
            raise InvalidInputError("Could not extract indicator_name from text.")

        # Parse date
        record_date_str = parsed.get("record_date")
        if record_date_str:
            from datetime import datetime
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()

        return self.health_repo.create(
            user_id=self.user_id,
            record_date=record_date or date.today(),
            indicator_type=parsed["indicator_type"],
            indicator_name=parsed["indicator_name"],
            value=Decimal(str(parsed.get("value", 0))),
            unit=parsed.get("unit", ""),
            notes=parsed.get("notes"),
            tags=parsed.get("tags"),
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
            task_type=parsed.get("task_type", "开发"),
            task_name=parsed["task_name"],
            duration_hours=duration_hours,
            value_description=parsed.get("value_description"),
            project_id=parsed.get("project_id"),
            priority=parsed.get("priority", "medium"),
            status=parsed.get("status", "completed"),
            start_time=None,  # Can be added later if needed
            end_time=None,    # Can be added later if needed
            tags=parsed.get("tags"),
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
            activity_type=parsed.get("activity_type", "娱乐"),
            activity=parsed["activity"],
            duration_hours=duration_hours,
            location=parsed.get("location"),
            participants=parsed.get("participants"),
            enjoyment_score=parsed.get("enjoyment_score"),
            cost=Decimal(str(parsed["cost"])) if parsed.get("cost") else None,
            tags=parsed.get("tags"),
            notes=parsed.get("notes"),
            raw_text=text,
        )

    async def add_learning_from_text(self, text: str, record_date: date | None = None):
        """
        Add learning record from natural language text.

        Args:
            text: Natural language input
            record_date: Optional date (defaults to today)

        Returns:
            Created learning record
        """
        try:
            parsed = self.parser.parse_learning(text, record_date)
        except Exception as e:
            raise AIServiceError(f"Failed to parse text: {str(e)}")

        # Validate
        if not parsed.get("title"):
            raise InvalidInputError("Could not extract title from text.")

        duration_hours = Decimal(str(parsed.get("duration_hours", 0)))
        if duration_hours <= 0:
            raise InvalidInputError("Duration must be positive.")

        # Parse date
        record_date_str = parsed.get("record_date")
        if record_date_str:
            from datetime import datetime
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date()

        return self.learning_repo.create(
            user_id=self.user_id,
            record_date=record_date or date.today(),
            learning_type=parsed.get("learning_type", "阅读"),
            title=parsed["title"],
            duration_hours=duration_hours,
            progress=parsed.get("progress", 0),
            source=parsed.get("source"),
            rating=parsed.get("rating"),
            notes=parsed.get("notes"),
            tags=parsed.get("tags"),
            raw_text=text,
        )

    async def add_social_from_text(self, text: str, record_date: date | None = None):
        """
        Add social record from natural language text.

        Args:
            text: Natural language input
            record_date: Optional date (defaults to today)

        Returns:
            Created social record
        """
        try:
            parsed = self.parser.parse_social(text, record_date)
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

        return self.social_repo.create(
            user_id=self.user_id,
            record_date=record_date or date.today(),
            social_type=parsed.get("social_type", "朋友"),
            participants=parsed.get("participants"),
            relationship_type=parsed.get("relationship_type", "朋友"),
            duration_hours=duration_hours,
            activity=parsed["activity"],
            location=parsed.get("location"),
            enjoyment_score=parsed.get("enjoyment_score"),
            cost=Decimal(str(parsed["cost"])) if parsed.get("cost") else None,
            notes=parsed.get("notes"),
            tags=parsed.get("tags"),
            raw_text=text,
        )

    async def add_goal_from_text(self, text: str):
        """
        Add goal from natural language text.

        Args:
            text: Natural language input

        Returns:
            Created goal
        """
        try:
            parsed = self.parser.parse_goal(text)
        except Exception as e:
            raise AIServiceError(f"Failed to parse text: {str(e)}")

        # Validate
        if not parsed.get("title"):
            raise InvalidInputError("Could not extract title from text.")

        target_value = Decimal(str(parsed.get("target_value", 0)))
        if target_value <= 0:
            raise InvalidInputError("Target value must be positive.")

        # Parse dates
        from datetime import datetime
        start_date_str = parsed.get("start_date")
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()

        target_date_str = parsed.get("target_date")
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date() if target_date_str else date.today()

        return self.goal_repo.create(
            user_id=self.user_id,
            goal_type=parsed.get("goal_type", "life"),
            title=parsed["title"],
            description=parsed.get("description"),
            target_value=target_value,
            unit=parsed.get("unit", ""),
            start_date=start_date,
            target_date=target_date,
            status=parsed.get("status", "active"),
            frequency=parsed.get("frequency"),
            tags=parsed.get("tags"),
        )

    async def update_goal_progress(self, goal_id: int, value: float, notes: str | None = None):
        """
        Update goal progress.

        Args:
            goal_id: Goal ID
            value: Progress value to add
            notes: Optional notes

        Returns:
            Updated goal
        """
        # Get current goal
        goal = self.goal_repo.get_by_id(goal_id)
        if not goal:
            raise InvalidInputError(f"Goal with ID {goal_id} not found.")

        # Create progress record
        self.goal_progress_repo.create(
            goal_id=goal_id,
            user_id=self.user_id,
            record_date=date.today(),
            value=Decimal(str(value)),
            notes=notes,
        )

        # Update goal current value
        updated_goal = self.goal_repo.update_current_value(
            goal_id=goal_id,
            value=float(goal.current_value) + value,
        )

        return updated_goal

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
- primary_category (TEXT) - 一级分类
- secondary_category (TEXT) - 二级分类
- description (TEXT) - 描述
- record_date (DATE) - 记录日期

**health_records** - 健康记录
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- record_date (DATE)
- indicator_type (TEXT) - 指标类型: sleep, exercise, diet, body, mental, medical
- indicator_name (TEXT) - 指标名称
- value (NUMERIC(10,2)) - 数值
- unit (TEXT) - 单位

**work_records** - 工作记录
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- record_date (DATE)
- task_type (TEXT) - 任务类型
- task_name (TEXT) - 任务名称
- duration_hours (NUMERIC(5,2)) - 工作时长
- value_description (TEXT) - 价值描述
- priority (TEXT) - 优先级
- status (TEXT) - 状态
- tags (JSON) - 标签数组

**leisure_records** - 休闲记录
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- record_date (DATE)
- activity_type (TEXT) - 活动类型
- activity (TEXT) - 活动名称
- duration_hours (NUMERIC(5,2)) - 时长
- location (TEXT) - 地点
- participants (JSON) - 参与人员
- enjoyment_score (INTEGER) - 愉悦度 1-5
- cost (NUMERIC(10,2)) - 花费

**learning_records** - 学习记录
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- record_date (DATE)
- learning_type (TEXT) - 学习类型
- title (TEXT) - 学习内容标题
- duration_hours (NUMERIC(5,2)) - 学习时长
- progress (INTEGER) - 进度百分比
- source (TEXT) - 来源
- rating (INTEGER) - 评分 1-5

**social_records** - 社交记录
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- record_date (DATE)
- social_type (TEXT) - 社交类型
- participants (JSON) - 参与人员
- relationship (TEXT) - 关系类型
- duration_hours (NUMERIC(5,2)) - 社交时长
- activity (TEXT) - 活动内容
- enjoyment_score (INTEGER) - 享受度 1-5
- cost (NUMERIC(10,2)) - 花费

**goals** - 目标
- id (INTEGER, PK)
- user_id (INTEGER, FK)
- goal_type (TEXT) - 目标类型
- title (TEXT) - 目标标题
- target_value (NUMERIC(10,2)) - 目标值
- current_value (NUMERIC(10,2)) - 当前值
- unit (TEXT) - 单位
- start_date (DATE) - 开始日期
- target_date (DATE) - 目标日期
- status (TEXT) - 状态

Notes:
- Always filter by user_id = {user_id}
- Date format: 'YYYY-MM-DD'
- Use SQLite date functions: date(), date('now', '-7 days')
"""
