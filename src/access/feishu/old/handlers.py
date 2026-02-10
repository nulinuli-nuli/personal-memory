"""Feishu event handlers with AI-driven intent recognition."""
import asyncio
import nest_asyncio  # Allow nested event loops
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict
from dataclasses import dataclass
from collections import deque
import hashlib
import threading

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
    """Thread-safe message deduplicator to prevent duplicate processing."""

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
        self.lock = threading.Lock()  # Thread safety for concurrent access

    def _hash_message(self, sender_id: str, text: str) -> str:
        """Generate hash for message deduplication."""
        content = f"{sender_id}:{text}:{datetime.now().strftime('%Y%m%d%H')}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_duplicate(self, sender_id: str, text: str) -> bool:
        """
        Check if message is a duplicate (thread-safe).

        Args:
            sender_id: Sender ID
            text: Message text

        Returns:
            True if duplicate, False otherwise
        """
        message_hash = self._hash_message(sender_id, text)
        now = datetime.now()

        with self.lock:  # Ensure thread-safe access
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

        # Initialize repositories for report generation
        from src.repositories.finance_repo import FinanceRepository
        from src.repositories.health_repo import HealthRepository
        from src.repositories.work_repo import WorkRepository
        from src.repositories.leisure_repo import LeisureRepository

        self.finance_repo = FinanceRepository(db)
        self.health_repo = HealthRepository(db)
        self.work_repo = WorkRepository(db)
        self.leisure_repo = LeisureRepository(db)

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
                # Unknown intent - return error
                response = self._format_unknown_intent_error(intent_result)

        except Exception as e:
            print(f"  ✗ AI 处理失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
            response = self._format_ai_error(e)

        print(f"📤 [6/6] 准备发送回复", flush=True)
        print("=" * 60, flush=True)

        return response

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
            return self._format_query_error(e, query)

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
                # Use generic indicator system
                value_str = f"{record.value} {record.unit}" if record.value else "N/A"
                result = f"✅ 已添加：😴 {record.indicator_name} {value_str}"
                if record.notes:
                    result += f" - {record.notes}"
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

    def _format_unknown_intent_error(self, intent_result: Dict[str, Any]) -> str:
        """Format error message for unknown intent."""
        reasoning = intent_result.get('reasoning', '无法理解您的输入')
        return f"""❓ 无法理解您的意图

AI 推理: {reasoning}

请尝试:
• 记录数据: "今天花了50块买午饭"
• 查询数据: "查询本周花费"
• 使用命令: /help 查看所有可用命令"""

    def _format_ai_error(self, error: Exception) -> str:
        """Format error message for AI failures."""
        error_msg = str(error)
        if "API error" in error_msg or "timeout" in error_msg.lower():
            return f"""❌ AI 服务暂时不可用

请稍后重试，或检查:
• AI API 配置是否正确
• 网络连接是否正常
• API 配额是否已用完

技术详情: {error_msg[:200]}"""
        else:
            return f"""❌ 处理请求时出错

错误信息: {error_msg}

请尝试:
• 重新表述您的请求
• 使用 /help 查看帮助
• 联系管理员"""

    def _format_query_error(self, error: Exception, query: str) -> str:
        """Format error message for query failures."""
        from src.services.query_service import SQLSafetyError

        if isinstance(error, SQLSafetyError):
            return f"""❌ 查询被安全策略阻止

{str(error)}

请尝试简化查询条件，或使用标准查询格式:
• "查询本周财务记录"
• "今天都做了什么"
• "本月工作总时长"
"""

        query_preview = query[:50] + '...' if len(query) > 50 else query
        return f"""❌ 查询处理失败

您的查询: {query_preview}

错误: {str(error)}

建议:
• 检查查询表述是否清晰
• 使用 /help 查看查询示例
• 尝试更简单的查询方式
"""

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
        """Generate daily report using direct database queries."""
        today = date.today()
        result = f"📅 今日报告 ({today})\n\n"

        # Get finance summary
        finance_records = self.finance_repo.get_by_date_range(user_id, today, today)
        if finance_records:
            total_expense = sum(r.amount for r in finance_records if r.type == "expense")
            total_income = sum(r.amount for r in finance_records if r.type == "income")
            result += f"💰 支出: ¥{total_expense:.2f} | 收入: ¥{total_income:.2f}\n"

        # Get health record (using generic indicator system)
        health_records = self.health_repo.get_by_date_range(user_id, today, today)
        if health_records:
            # Display all health indicators for the day
            for hr in health_records:
                value_str = f"{hr.value} {hr.unit}" if hr.value else "N/A"
                result += f"😴 {hr.indicator_name}: {value_str}\n"

        # Get work summary
        work_records = self.work_repo.get_by_date_range(user_id, today, today)
        if work_records:
            total_hours = sum(r.duration_hours for r in work_records)
            result += f"💼 工作时长: {total_hours}h\n"

        # Get leisure summary
        leisure_records = self.leisure_repo.get_by_date_range(user_id, today, today)
        if leisure_records:
            total_hours = sum(r.duration_hours for r in leisure_records)
            result += f"🎮 休闲时长: {total_hours}h\n"

        if not any([finance_records, health_record, work_records, leisure_records]):
            result += "今天还没有记录任何数据\n"

        return result

    async def _generate_weekly_report(self, user_id: int) -> str:
        """Generate weekly report using direct database queries."""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        result = f"📊 本周报告 ({start_of_week} 至 {today})\n\n"

        # Get finance summary
        finance_records = self.finance_repo.get_by_date_range(user_id, start_of_week, today)
        if finance_records:
            total_expense = sum(r.amount for r in finance_records if r.type == "expense")
            total_income = sum(r.amount for r in finance_records if r.type == "income")
            result += f"💰 支出: ¥{total_expense:.2f} | 收入: ¥{total_income:.2f}\n"

        # Get work summary
        work_records = self.work_repo.get_by_date_range(user_id, start_of_week, today)
        if work_records:
            total_hours = sum(r.duration_hours for r in work_records)
            result += f"💼 工作时长: {total_hours}h\n"

        # Get leisure summary
        leisure_records = self.leisure_repo.get_by_date_range(user_id, start_of_week, today)
        if leisure_records:
            total_hours = sum(r.duration_hours for r in leisure_records)
            result += f"🎮 休闲时长: {total_hours}h\n"

        return result

    async def _generate_monthly_report(self, user_id: int) -> str:
        """Generate monthly report using direct database queries."""
        today = date.today()
        start_of_month = today.replace(day=1)
        result = f"📅 本月报告 ({start_of_month} 至 {today})\n\n"

        # Get finance summary
        finance_records = self.finance_repo.get_by_date_range(user_id, start_of_month, today)
        if finance_records:
            total_expense = sum(r.amount for r in finance_records if r.type == "expense")
            total_income = sum(r.amount for r in finance_records if r.type == "income")
            result += f"💰 支出: ¥{total_expense:.2f} | 收入: ¥{total_income:.2f}\n"

        # Get work summary
        work_records = self.work_repo.get_by_date_range(user_id, start_of_month, today)
        if work_records:
            total_hours = sum(r.duration_hours for r in work_records)
            result += f"💼 工作时长: {total_hours}h\n"

        # Get leisure summary
        leisure_records = self.leisure_repo.get_by_date_range(user_id, start_of_month, today)
        if leisure_records:
            total_hours = sum(r.duration_hours for r in leisure_records)
            result += f"🎮 休闲时长: {total_hours}h\n"

        return result

    async def _list_recent_records(self, user_id: int, args: list[str]) -> str:
        """List recent records using direct database queries."""
        record_type = args[0] if args else None

        if record_type == "finance":
            records = self.finance_repo.get_all(user_id, limit=10)
            if not records:
                return "📊 没有找到财务记录"
            result = "💸 财务记录 (最近10条)\n\n"
            for r in records:
                icon = "💰" if r.type == "income" else "💸"
                result += f"{icon} {r.record_date} {r.description or r.category or ''} ¥{r.amount}\n"
            return result

        elif record_type == "health":
            records = self.health_repo.get_all(user_id, limit=7)
            if not records:
                return "😴 没有找到健康记录"
            result = "😴 健康记录 (最近7条)\n\n"
            for r in records:
                value_str = f"{r.value} {r.unit}" if r.value else "N/A"
                notes_str = f" - {r.notes}" if r.notes else ""
                result += f"📅 {r.record_date} | 😴 {r.indicator_name}: {value_str}{notes_str}\n"
            return result

        elif record_type == "work":
            records = self.work_repo.get_all(user_id, limit=10)
            if not records:
                return "💼 没有找到工作记录"
            result = "💼 工作记录 (最近10条)\n\n"
            for r in records:
                result += f"📅 {r.record_date} | ⏱ {r.duration_hours}h | {r.task_name}\n"
            return result

        elif record_type == "leisure":
            records = self.leisure_repo.get_all(user_id, limit=10)
            if not records:
                return "🎮 没有找到休闲记录"
            result = "🎮 休闲记录 (最近10条)\n\n"
            for r in records:
                result += f"📅 {r.record_date} | ⏱ {r.duration_hours}h | {r.activity}\n"
            return result

        else:
            # Show all types
            result = "📊 最近记录\n\n"
            finance = self.finance_repo.get_all(user_id, limit=5)
            if finance:
                result += "💸 财务:\n"
                for r in finance[:3]:
                    result += f"  {r.record_date} ¥{r.amount}\n"
            health = self.health_repo.get_all(user_id, limit=3)
            if health:
                result += "😴 健康:\n"
                for r in health:
                    value_str = f"{r.value} {r.unit}" if r.value else "N/A"
                    result += f"  {r.record_date} {r.indicator_name}: {value_str}\n"
            return result or "暂无记录"
