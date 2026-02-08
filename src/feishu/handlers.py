"""Feishu event handlers with AI-driven intent recognition."""
import asyncio
import nest_asyncio  # Allow nested event loops
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict
from dataclasses import dataclass
from collections import deque
import hashlib

from sqlalchemy.orm import Session

from src.config import settings
from src.core.models import FinanceRecord, HealthRecord, WorkRecord, LeisureRecord
from src.core.database import get_db
from src.services.record_service import RecordService
from src.services.query_service import QueryService, SQLSafetyError
from src.repositories.user_repo import UserRepository
from src.ai.parser import TextParser

# Apply nest_asyncio patch globally
nest_asyncio.apply()


# ============================================================================
# MESSAGE DEDUPLICATION - Prevent duplicate processing
# ============================================================================

class MessageDeduplicator:
    """Prevent processing duplicate messages within a time window."""

    def __init__(self, window_seconds: int = 10, max_size: int = 1000):
        """
        Initialize deduplicator.

        Args:
            window_seconds: Time window to consider messages as duplicates (default: 10s)
            max_size: Maximum number of message hashes to store
        """
        self.window_seconds = window_seconds
        self.max_size = max_size
        self.message_hashes = deque()  # List of (hash, timestamp)

    def _hash_message(self, sender_id: str, text: str) -> str:
        """Generate hash for message deduplication."""
        content = f"{sender_id}:{text}:{datetime.now().strftime('%Y%m%d%H')}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_duplicate(self, sender_id: str, text: str) -> bool:
        """
        Check if message is a duplicate.

        Args:
            sender_id: Sender ID
            text: Message text

        Returns:
            True if duplicate, False otherwise
        """
        message_hash = self._hash_message(sender_id, text)
        now = datetime.now()

        # Clean old hashes
        cutoff_time = now - timedelta(seconds=self.window_seconds)
        while self.message_hashes and self.message_hashes[0][1] < cutoff_time:
            self.message_hashes.popleft()

        # Check if hash exists in window
        for existing_hash, _ in self.message_hashes:
            if existing_hash == message_hash:
                # Simply log and skip, no other logic
                print(f"⚠️  重复消息，已跳过 (2分钟内)", flush=True)
                return True

        # Add new hash
        self.message_hashes.append((message_hash, now))

        # Prevent unlimited growth
        if len(self.message_hashes) > self.max_size:
            self.message_hashes.popleft()

        return False


# Global deduplicator instance (2-minute window for duplicate detection)
message_deduplicator = MessageDeduplicator(window_seconds=120)


# Minimal MessageEvent for backward compatibility
@dataclass
class FeishuUser:
    """Feishu user information."""
    user_id: str


@dataclass
class MessageEvent:
    """Feishu message event (minimal version for backward compatibility)."""
    sender: FeishuUser
    content: str


# ============================================================================
# LEGACY KEYWORD-BASED INTENT RECOGNITION
# These are retained as fallback when AI fails
# ============================================================================

# Query intent keywords
QUERY_KEYWORDS = [
    "查询", "看看", "显示", "统计", "多少", "总计", "一共",
    "报告", "汇总", "明细", "记录", "花了", "花费", "支出",
    "收入", "睡眠", "工作", "休闲", "运动",
]

# Record type keywords
RECORD_TYPE_KEYWORDS = {
    "finance": ["花了", "花费", "支出", "收入", "赚", "买", "支付", "付款"],
    "health": ["睡眠", "睡了", "睡觉", "心情", "健康", "运动", "锻炼"],
    "work": ["工作", "完成", "开发", "写", "修复", "任务"],
    "leisure": ["玩", "看", "听", "游戏", "电影", "音乐", "阅读"],
}


class FeishuEventHandler:
    """Handler for Feishu events."""

    def __init__(self, db: Session):
        """
        Initialize handler.

        Args:
            db: Database session
        """
        self.db = db
        self.parser = TextParser()
        self.user_repo = UserRepository(db)

    def handle_message_by_text(self, sender_id: str, text: str) -> str:
        """
        Handle text message using AI-driven intent recognition (SDK-compatible entry point).

        This is the main entry point for SDK events.
        It uses AI to classify intent and routes to appropriate handler.

        Args:
            sender_id: Feishu user ID
            text: Message text

        Returns:
            Response message
        """
        # Check for duplicate messages
        if message_deduplicator.is_duplicate(sender_id, text):
            return None  # Return None to indicate duplicate (no response)

        print("=" * 60, flush=True)
        print(f"📨 [1/6] 收到消息", flush=True)
        print(f"  发送者: {sender_id}", flush=True)
        print(f"  内容: {text}", flush=True)

        # Get or create user
        print(f"🔍 [2/6] 查询/创建用户...", flush=True)
        user = self.user_repo.get_or_create_by_feishu(sender_id)
        service = RecordService(self.db, user.id)

        # Helper to run async code (works with nest_asyncio)
        def run_async(coro):
            try:
                loop = asyncio.get_running_loop()
                return loop.run_until_complete(coro)
            except RuntimeError:
                return asyncio.run(coro)

        # AI intent recognition
        print(f"🎯 [3/6] AI 意图识别...", flush=True)

        # Check for legacy commands first
        if text.startswith("/"):
            print(f"  → 识别为: 传统命令 (以 / 开头)", flush=True)
            response = run_async(self.handle_command_by_service(service, text))
            print(f"📤 [6/6] 准备发送回复", flush=True)
            print("=" * 60, flush=True)
            return response

        try:
            intent_result = self.parser.classify_intent(text)
            intent = intent_result["intent"]
            confidence = intent_result["confidence"]

            print(f"  → 意图: {intent} (置信度: {confidence:.2f})", flush=True)
            print(f"  → 记录类型: {intent_result.get('record_type') or '通用'}", flush=True)
            print(f"  → 推理: {intent_result['reasoning']}", flush=True)

            # Route based on intent
            if intent == "query":
                response = run_async(self.handle_query_by_service(service, text, intent_result))
            elif intent == "add_record":
                # Low confidence handling
                if confidence < 0.6:
                    return "❓ 不太确定您的意图，请换个说法试试\n\n您可以：\n• 记录数据：今天花了50块\n• 查询数据：查询本周花费"
                response = run_async(self.handle_record_by_service(service, text, intent_result))
            else:
                # Unknown intent, fallback to traditional method
                print(f"  → 未知意图，回退到关键词匹配...", flush=True)
                response = run_async(self._fallback_handler(service, text))

        except Exception as e:
            print(f"  ✗ AI 处理失败: {e}", flush=True)
            print(f"  → 回退到传统处理...", flush=True)
            import traceback
            traceback.print_exc()
            response = run_async(self._fallback_handler(service, text))

        print(f"📤 [6/6] 准备发送回复", flush=True)
        print("=" * 60, flush=True)

        return response

    async def handle_message(self, event: MessageEvent) -> str:
        """
        Handle message event with smart intent recognition.

        Args:
            event: Message event

        Returns:
            Response message
        """
        content = event.content
        if not content:
            return "❓ 没有收到消息内容"

        # 1. Check if it's a command (starts with /)
        if content.startswith("/"):
            return await self.handle_command(event, content)

        # 2. Check if it's a query intent (contains query keywords)
        if self._is_query_intent(content):
            return await self.handle_query(event, content)

        # 3. Otherwise, treat as adding a record
        return await self.handle_record(event, content)

    def _is_query_intent(self, text: str) -> bool:
        """
        Check if text indicates a query intent.

        Args:
            text: Input text

        Returns:
            True if query intent detected
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in QUERY_KEYWORDS)

    async def handle_command_by_service(self, service: RecordService, command: str) -> str:
        """
        Handle traditional commands (with service).

        Args:
            service: RecordService instance
            command: Command string

        Returns:
            Response message
        """
        user_id = service.user_id

        # Parse command
        parts = command.strip().split()
        cmd = parts[0].lower() if parts else ""

        print(f"  → 命令类型: {cmd}", flush=True)
        print(f"📋 [4/6] 执行命令...", flush=True)

        if cmd == "/help":
            result = self._get_help_message()
            print(f"  ✓ 帮助信息已生成", flush=True)
            return result
        elif cmd == "/daily":
            print(f"  → 生成今日报告...", flush=True)
            result = await self._generate_daily_report(user_id)
            print(f"  ✓ 报告生成完成", flush=True)
            return result
        elif cmd == "/weekly":
            print(f"  → 生成本周报告...", flush=True)
            result = await self._generate_weekly_report(user_id)
            print(f"  ✓ 报告生成完成", flush=True)
            return result
        elif cmd == "/monthly":
            print(f"  → 生成本月报告...", flush=True)
            result = await self._generate_monthly_report(user_id)
            print(f"  ✓ 报告生成完成", flush=True)
            return result
        elif cmd == "/list":
            print(f"  → 列出最近记录...", flush=True)
            result = await self._list_recent_records(user_id, parts[1:] if len(parts) > 1 else [])
            print(f"  ✓ 列表生成完成", flush=True)
            return result
        else:
            print(f"  ✗ 未知命令: {cmd}", flush=True)
            return f"❓ 未知命令: {cmd}\n\n发送 /help 查看可用命令"

    async def handle_command(self, event: MessageEvent, command: str) -> str:
        """
        Handle traditional commands (legacy, for backward compatibility).

        Args:
            event: Message event
            command: Command string

        Returns:
            Response message
        """
        user = self.user_repo.get_or_create_by_feishu(event.sender.user_id)
        service = RecordService(self.db, user.id)
        return await self.handle_command_by_service(service, command)

    async def handle_query_by_service(
        self,
        service: RecordService,
        query: str,
        intent_result: Dict[str, Any] | None = None
    ) -> str:
        """
        Use AI to generate SQL and execute query.

        Args:
            service: RecordService instance
            query: Query text
            intent_result: Pre-classified intent result (optional)

        Returns:
            Query result
        """
        user_id = service.user_id
        print(f"🔍 [4/6] AI 生成查询 SQL...", flush=True)

        try:
            # Get database schema
            schema = service.get_db_schema_for_ai()

            # AI generates SQL
            query_result = self.parser.generate_query_sql(query, user_id, schema)
            print(f"  → 生成 SQL: {query_result['sql'][:80]}...", flush=True)
            print(f"  → 说明: {query_result['explanation']}", flush=True)

            # Safe execution
            print(f"📊 [5/6] 执行查询...", flush=True)
            query_service = QueryService(self.db)
            rows = query_service.execute_query(query_result['sql'], user_id)

            # Format results
            result = query_service.format_results(rows, query_result)
            print(f"  ✓ 查询完成，{len(rows)} 条结果", flush=True)

            return result

        except SQLSafetyError as e:
            print(f"  ✗ SQL 安全检查失败: {e}", flush=True)
            return f"❌ 查询被安全策略阻止: {str(e)}\n\n请尝试简化查询条件"

        except Exception as e:
            print(f"  ✗ AI 查询失败: {e}", flush=True)
            import traceback
            traceback.print_exc()

            # Fallback to traditional query
            print(f"  → 回退到传统查询...", flush=True)
            return await self._fallback_query(user_id, query)

    async def handle_query(self, event: MessageEvent, query: str) -> str:
        """
        Handle AI-powered smart query (legacy, for backward compatibility).

        Args:
            event: Message event
            query: Query text

        Returns:
            Query result
        """
        user = self.user_repo.get_or_create_by_feishu(event.sender.user_id)
        service = RecordService(self.db, user.id)
        return await self.handle_query_by_service(service, query)

    def _parse_query_intent(self, query: str) -> dict[str, Any]:
        """
        Parse query intent using AI.

        Args:
            query: Query text

        Returns:
            Parsed query intent
        """
        # Simple rule-based parsing (can be enhanced with AI)
        today = date.today()
        parsed = {
            "record_type": None,
            "start_date": None,
            "end_date": None,
            "category": None,
            "query_type": "list",  # list, sum, avg, count
        }

        # Detect record type
        for record_type, keywords in RECORD_TYPE_KEYWORDS.items():
            if any(kw in query for kw in keywords):
                parsed["record_type"] = record_type
                break

        # Detect time range
        if "今天" in query:
            parsed["start_date"] = today
            parsed["end_date"] = today
        elif "昨天" in query:
            yesterday = today - timedelta(days=1)
            parsed["start_date"] = yesterday
            parsed["end_date"] = yesterday
        elif "本周" in query:
            start_of_week = today - timedelta(days=today.weekday())
            parsed["start_date"] = start_of_week
            parsed["end_date"] = today
        elif "上周" in query:
            start_of_week = today - timedelta(days=today.weekday() + 7)
            end_of_week = start_of_week + timedelta(days=6)
            parsed["start_date"] = start_of_week
            parsed["end_date"] = end_of_week
        elif "本月" in query:
            start_of_month = today.replace(day=1)
            parsed["start_date"] = start_of_month
            parsed["end_date"] = today
        elif "上月" in query:
            first_day = today.replace(day=1)
            last_month_end = first_day - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            parsed["start_date"] = last_month_start
            parsed["end_date"] = last_month_end

        # Detect query type
        if any(kw in query for kw in ["总计", "一共", "总共", "总和"]):
            parsed["query_type"] = "sum"
        elif any(kw in query for kw in ["平均", "均值"]):
            parsed["query_type"] = "avg"
        elif any(kw in query for kw in ["多少", "数量", "几条"]):
            parsed["query_type"] = "count"

        # Detect category for finance
        if parsed["record_type"] == "finance":
            categories = ["餐饮", "交通", "购物", "娱乐", "居住", "医疗", "教育", "其他"]
            for cat in categories:
                if cat in query:
                    parsed["category"] = cat
                    break

        return parsed

    async def _execute_query(self, user_id: int, parsed: dict[str, Any]) -> str:
        """
        Execute parsed query.

        Args:
            user_id: User ID
            parsed: Parsed query intent

        Returns:
            Query result
        """
        record_type = parsed.get("record_type")
        start_date = parsed.get("start_date")
        end_date = parsed.get("end_date")
        category = parsed.get("category")
        query_type = parsed.get("query_type", "list")

        # If no record type detected, show all types
        if not record_type:
            return await self._generate_multi_type_report(user_id, start_date, end_date)

        # Execute query by type
        if record_type == "finance":
            return await self._query_finance(user_id, start_date, end_date, category, query_type)
        elif record_type == "health":
            return await self._query_health(user_id, start_date, end_date, query_type)
        elif record_type == "work":
            return await self._query_work(user_id, start_date, end_date, query_type)
        elif record_type == "leisure":
            return await self._query_leisure(user_id, start_date, end_date, query_type)
        else:
            return "❓ 无法识别查询类型"

    async def _query_finance(
        self,
        user_id: int,
        start_date: date | None,
        end_date: date | None,
        category: str | None,
        query_type: str,
    ) -> str:
        """Query finance records."""
        from src.repositories.finance_repo import FinanceRepository

        repo = FinanceRepository(self.db)

        if query_type == "sum":
            if start_date and end_date:
                records = repo.get_by_date_range(user_id, start_date, end_date)
            else:
                records = repo.get_all(user_id, limit=1000)

            total_expense = sum(r.amount for r in records if r.type == "expense")
            total_income = sum(r.amount for r in records if r.type == "income")

            date_range = self._format_date_range(start_date, end_date)
            result = f"💸 财务统计 {date_range}\n\n"
            result += f"支出: ¥{total_expense:.2f}\n"
            result += f"收入: ¥{total_income:.2f}\n"
            result += f"结余: ¥{total_income - total_expense:.2f}"

            return result
        else:
            # List records
            if start_date and end_date:
                records = repo.get_by_date_range(user_id, start_date, end_date)
            else:
                records = repo.get_all(user_id, limit=20)

            if not records:
                return "📊 没有找到财务记录"

            result = "💸 财务记录\n\n"
            for r in records[:10]:
                icon = "💰" if r.type == "income" else "💸"
                result += f"{icon} {r.record_date} {r.description or r.category or ''} ¥{r.amount}\n"

            return result

    async def _query_health(
        self,
        user_id: int,
        start_date: date | None,
        end_date: date | None,
        query_type: str,
    ) -> str:
        """Query health records."""
        from src.repositories.health_repo import HealthRepository

        repo = HealthRepository(self.db)

        if start_date and end_date:
            records = [
                r for r in repo.get_all(user_id, limit=1000)
                if start_date <= r.record_date <= end_date
            ]
        else:
            records = repo.get_all(user_id, limit=7)

        if not records:
            return "😴 没有找到健康记录"

        result = "😴 健康记录\n\n"
        for r in records[:7]:
            sleep_info = f"{r.sleep_hours}h" if r.sleep_hours else "N/A"
            result += f"📅 {r.record_date} | 😴 {sleep_info} | {r.sleep_quality or 'N/A'}\n"

        return result

    async def _query_work(
        self,
        user_id: int,
        start_date: date | None,
        end_date: date | None,
        query_type: str,
    ) -> str:
        """Query work records."""
        from src.repositories.work_repo import WorkRepository

        repo = WorkRepository(self.db)

        if start_date and end_date:
            records = [
                r for r in repo.get_all(user_id, limit=1000)
                if start_date <= r.record_date <= end_date
            ]
        else:
            records = repo.get_all(user_id, limit=10)

        if not records:
            return "💼 没有找到工作记录"

        total_hours = sum(r.duration_hours for r in records)

        result = "💼 工作记录\n\n"
        for r in records[:10]:
            result += f"📅 {r.record_date} | ⏱ {r.duration_hours}h | {r.task_name}\n"

        result += f"\n总计: {total_hours}h"

        return result

    async def _query_leisure(
        self,
        user_id: int,
        start_date: date | None,
        end_date: date | None,
        query_type: str,
    ) -> str:
        """Query leisure records."""
        from src.repositories.leisure_repo import LeisureRepository

        repo = LeisureRepository(self.db)

        if start_date and end_date:
            records = [
                r for r in repo.get_all(user_id, limit=1000)
                if start_date <= r.record_date <= end_date
            ]
        else:
            records = repo.get_all(user_id, limit=10)

        if not records:
            return "🎮 没有找到休闲记录"

        total_hours = sum(r.duration_hours for r in records)

        result = "🎮 休闲记录\n\n"
        for r in records[:10]:
            result += f"📅 {r.record_date} | ⏱ {r.duration_hours}h | {r.activity}\n"

        result += f"\n总计: {total_hours}h"

        return result

    async def _generate_multi_type_report(
        self,
        user_id: int,
        start_date: date | None,
        end_date: date | None,
    ) -> str:
        """Generate report for all record types."""
        date_range = self._format_date_range(start_date, end_date)
        result = f"📊 数据统计 {date_range}\n\n"

        # Add summaries from each type
        finance_result = await self._query_finance(user_id, start_date, end_date, None, "sum")
        if not finance_result.startswith("❌"):
            result += finance_result + "\n\n"

        work_result = await self._query_work(user_id, start_date, end_date, "list")
        if not work_result.startswith("❌"):
            # Extract total hours
            lines = work_result.split("\n")
            for line in lines:
                if "总计" in line:
                    result += f"💼 {line}\n"
                    break

        return result

    def _format_date_range(self, start_date: date | None, end_date: date | None) -> str:
        """Format date range for display."""
        if start_date and end_date:
            if start_date == end_date:
                return f"({start_date})"
            return f"({start_date} 至 {end_date})"
        return ""

    async def handle_record_by_service(
        self,
        service: RecordService,
        text: str,
        intent_result: Dict[str, Any] | None = None
    ) -> str:
        """
        Use AI to detect record type and add record.

        Args:
            service: RecordService instance
            text: Record text
            intent_result: Pre-classified intent result (optional)

        Returns:
            Confirmation message
        """
        print(f"🤖 [4/6] AI 解析记录类型...", flush=True)

        try:
            # Use pre-classified type or let AI detect
            if intent_result and intent_result.get('record_type'):
                record_type = intent_result['record_type']
                print(f"  → 使用意图识别结果: {record_type}", flush=True)
            else:
                detection = self.parser.detect_record_type(text)
                record_type = detection['record_type']
                confidence = detection['confidence']
                print(f"  → AI 检测: {record_type} (置信度: {confidence:.2f})", flush=True)

                if confidence < 0.6:
                    return "❓ 不太确定这是什么类型的记录\n\n请明确说明是财务、健康、工作还是休闲记录"

            # Call corresponding parser (keep existing logic)
            if record_type == "finance":
                print(f"  → 调用 AI 解析财务记录...", flush=True)
                record = await service.add_finance_from_text(text)
                icon = "💰" if record.type == "income" else "💸"
                result = f"✅ 已添加：{icon} {record.description or record.category or ''} ¥{record.amount}"
                print(f"  ✓ AI 解析成功", flush=True)
                return result

            elif record_type == "health":
                print(f"  → 调用 AI 解析健康记录...", flush=True)
                record = await service.add_health_from_text(text)
                sleep_info = f"{record.sleep_hours}h" if record.sleep_hours else "N/A"
                result = f"✅ 已添加：😴 睡眠 {sleep_info} - {record.sleep_quality or 'N/A'}"
                print(f"  ✓ AI 解析成功", flush=True)
                return result

            elif record_type == "work":
                print(f"  → 调用 AI 解析工作记录...", flush=True)
                record = await service.add_work_from_text(text)
                result = f"✅ 已添加：💼 {record.task_name} ({record.duration_hours}h)"
                print(f"  ✓ AI 解析成功", flush=True)
                return result

            elif record_type == "leisure":
                print(f"  → 调用 AI 解析休闲记录...", flush=True)
                record = await service.add_leisure_from_text(text)
                result = f"✅ 已添加：🎮 {record.activity} ({record.duration_hours}h)"
                print(f"  ✓ AI 解析成功", flush=True)
                return result

            else:
                return "❓ 无法识别记录类型"

        except Exception as e:
            print(f"  ✗ AI 解析失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return f"❌ 添加失败: {str(e)}"

    async def handle_record(self, event: MessageEvent, text: str) -> str:
        """
        Handle adding a new record (with service).

        Args:
            service: RecordService instance
            text: Record text

        Returns:
            Confirmation message
        """
        # Detect record type by keywords
        record_type = self._detect_record_type(text)

        try:
            if record_type == "finance":
                record = await service.add_finance_from_text(text)
                icon = "💰" if record.type == "income" else "💸"
                return f"✅ 已添加：{icon} {record.description or record.category or ''} ¥{record.amount}"

            elif record_type == "health":
                record = await service.add_health_from_text(text)
                sleep_info = f"{record.sleep_hours}h" if record.sleep_hours else "N/A"
                return f"✅ 已添加：😴 睡眠 {sleep_info} - {record.sleep_quality or 'N/A'}"

            elif record_type == "work":
                record = await service.add_work_from_text(text)
                return f"✅ 已添加：💼 {record.task_name} ({record.duration_hours}h)"

            elif record_type == "leisure":
                record = await service.add_leisure_from_text(text)
                return f"✅ 已添加：🎮 {record.activity} ({record.duration_hours}h)"

            else:
                return "❓ 无法识别记录类型\n\n请尝试：\n• 今天花了50块买午饭\n• 昨晚睡了8小时\n• 今天工作了4小时完成开发\n• 看了2小时电影"

        except Exception as e:
            return f"❌ 添加失败: {str(e)}"

    async def handle_record(self, event: MessageEvent, text: str) -> str:
        """
        Handle adding a new record (legacy, for backward compatibility).

        Args:
            event: Message event
            text: Record text

        Returns:
            Confirmation message
        """
        user = self.user_repo.get_or_create_by_feishu(event.sender.user_id)
        service = RecordService(self.db, user.id)
        return await self.handle_record_by_service(service, text)

    def _detect_record_type(self, text: str) -> str | None:
        """
        Detect record type by keywords.

        Args:
            text: Input text

        Returns:
            Record type or None
        """
        for record_type, keywords in RECORD_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return record_type
        return None

    # ============================================================================
    # FALLBACK METHODS - Legacy keyword-based matching (used when AI fails)
    # ============================================================================

    async def _fallback_handler(self, service: RecordService, text: str) -> str:
        """
        Fallback to traditional keyword matching.

        Args:
            service: RecordService instance
            text: Input text

        Returns:
            Response message
        """
        # Use original keyword-based logic
        if self._is_query_intent(text):
            return await self._fallback_query(service.user_id, text)
        else:
            return await self.handle_record_by_service(service, text)

    async def _fallback_query(self, user_id: int, query: str) -> str:
        """
        Traditional query handling (fallback).

        Args:
            user_id: User ID
            query: Query text

        Returns:
            Query result
        """
        parsed = self._parse_query_intent(query)
        return await self._execute_query(user_id, parsed)

    def _get_help_message(self) -> str:
        """Get help message."""
        return """🤖 个人记忆助手 - AI 驱动的自然语言交互

📝 记录数据（纯自然语言）：
• 今天花了50块买午饭
• 昨晚睡了8小时，睡得很好
• 今天工作了4小时，完成用户认证模块
• 看了2小时电影

🔍 查询数据（支持复杂查询）：
• 查询本周财务记录
• 工作超过4小时的任务
• 本月餐饮和交通总支出
• 睡眠质量为优的天数
• 今天都做了什么

📋 快捷命令：
• /daily - 今日报告
• /weekly - 本周报告
• /monthly - 本月报告
• /list - 最近记录
• /help - 帮助信息

💡 提示：完全支持自然语言，无需记忆命令格式！"""

    async def _generate_daily_report(self, user_id: int) -> str:
        """Generate daily report."""
        today = date.today()
        return await self._execute_query(user_id, {
            "record_type": None,
            "start_date": today,
            "end_date": today,
            "query_type": "list",
        })

    async def _generate_weekly_report(self, user_id: int) -> str:
        """Generate weekly report."""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        return await self._execute_query(user_id, {
            "record_type": None,
            "start_date": start_of_week,
            "end_date": today,
            "query_type": "list",
        })

    async def _generate_monthly_report(self, user_id: int) -> str:
        """Generate monthly report."""
        today = date.today()
        start_of_month = today.replace(day=1)
        return await self._execute_query(user_id, {
            "record_type": None,
            "start_date": start_of_month,
            "end_date": today,
            "query_type": "list",
        })

    async def _list_recent_records(self, user_id: int, args: list[str]) -> str:
        """List recent records."""
        record_type = args[0] if args else None

        if record_type == "finance":
            return await self._query_finance(user_id, None, None, None, "list")
        elif record_type == "health":
            return await self._query_health(user_id, None, None, "list")
        elif record_type == "work":
            return await self._query_work(user_id, None, None, "list")
        elif record_type == "leisure":
            return await self._query_leisure(user_id, None, None, "list")
        else:
            return await self._generate_multi_type_report(user_id, None, None)
