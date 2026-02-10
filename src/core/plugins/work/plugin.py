"""Work plugin - handles work-related records and queries."""
from typing import Dict, Any
from decimal import Decimal
from datetime import date, timedelta
import logging

from src.access.base import AccessRequest, AccessResponse
from src.core.plugin.base import BasePlugin
from src.storage.repositories.work_repo import WorkRepository
from src.core.common.date_utils import parse_date

logger = logging.getLogger(__name__)


class WorkPlugin(BasePlugin):
    """Work plugin - handles work tasks and time tracking."""

    @property
    def name(self) -> str:
        return "work"

    @property
    def display_name(self) -> str:
        return "工作管理"

    @property
    def description(self) -> str:
        return "处理工作任务记录、时长统计、项目管理等功能。支持添加工作记录，查询工作数据，生成工作报表。"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _create_repository(self):
        """Create work repository."""
        return WorkRepository(self.db)

    async def execute(
        self,
        request: AccessRequest,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> AccessResponse:
        """
        Execute work plugin functionality.

        Args:
            request: User request
            context: Conversation context
            params: Parameters (empty - router doesn't pass anything)

        Returns:
            Response result
        """
        try:
            # 1. Use AI to analyze user intent and extract data
            analysis = await self._analyze_user_intent(request.input_text)

            # 2. Execute based on intent
            action = analysis.get("action", "add")

            if action == "add":
                return await self._add_record(request, analysis)
            elif action == "query":
                return await self._query_records(request, analysis)
            elif action == "stats":
                return await self._get_statistics(request, analysis)
            else:
                return AccessResponse(
                    success=False,
                    error=f"不支持的操作: {action}",
                    message="",
                    data=None,
                    metadata={}
                )

        except Exception as e:
            logger.error(f"Work plugin error: {e}", exc_info=True)
            return AccessResponse(
                success=False,
                error=f"操作失败: {str(e)}",
                message="",
                data=None,
                metadata={}
            )

    async def _analyze_user_intent(self, text: str) -> Dict:
        """
        Use AI to analyze user intent and extract data.

        Args:
            text: User input text

        Returns:
            Analysis result with action and extracted data
        """
        prompt = f"""分析用户输入，判断操作类型并提取相关数据。

用户输入: {text}

请返回JSON格式:
{{
    "action": "操作类型（add/query/stats）",
    "data": {{
        // 根据action类型提取相应数据
    }}
}}

## 操作类型判断规则:

1. **add** - 添加记录
   - 用户想要记录新的工作内容
   - 关键词：工作了、完成、做了、开发、会议等
   - data: {{task_type, task_name, duration_hours, value_description, record_date}}

2. **query** - 查询记录列表
   - 用户想要查看具体的工作明细
   - 关键词：查询、列出、显示、看看、记录等
   - data: {{date_range}}

3. **stats** - 统计分析
   - 用户想要统计数字、总计、汇总
   - 关键词：多少、多久、总计、统计、汇总、一共等
   - data: {{date_range, stat_type}}

## 数据提取规则:
- record_date: "今天"/"明天"/"昨天"/"本周"/"本月"/"YYYY-MM-DD"
- task_type: 工作类型（如：开发、会议、协作、学习等）
- task_name: 任务名称
- duration_hours: 工作时长（小时数）
- value_description: 价值描述
"""

        return self.ai.parse(prompt, context={})

    async def _add_record(self, request: AccessRequest, analysis: Dict) -> AccessResponse:
        """
        Add work record.

        Args:
            request: User request
            analysis: AI analysis result

        Returns:
            Response
        """
        data = analysis.get("data", {})

        if not data.get("task_name"):
            return AccessResponse(
                success=False,
                error="缺少任务名称",
                message="",
                data=None,
                metadata={}
            )

        duration_hours = Decimal(str(data.get("duration_hours", 0)))
        if duration_hours <= 0:
            return AccessResponse(
                success=False,
                error="工作时长必须大于0",
                message="",
                data=None,
                metadata={}
            )

        # Parse date
        record_date = parse_date(data.get("record_date"))

        # Create record
        record = self.repository.create(
            user_id=int(request.user_id),
            record_date=record_date,
            task_type=data.get("task_type", "开发"),
            task_name=data["task_name"],
            duration_hours=duration_hours,
            value_description=data.get("value_description"),
            project_id=data.get("project_id"),
            priority=data.get("priority", "medium"),
            status=data.get("status", "completed"),
            tags=data.get("tags"),
            raw_text=request.input_text
        )

        return AccessResponse(
            success=True,
            data={"id": record.id, "duration": float(record.duration_hours)},
            message=f"已添加：{record.task_name} ({record.duration_hours}小时)",
            error=None,
            metadata={}
        )

    async def _query_records(self, request: AccessRequest, analysis: Dict) -> AccessResponse:
        """
        Query work records.

        Args:
            request: User request
            analysis: AI analysis result

        Returns:
            Response
        """
        # Get recent records
        records = self.repository.get_all(
            user_id=int(request.user_id),
            limit=10
        )

        if not records:
            return AccessResponse(
                success=True,
                data=[],
                message="暂无工作记录",
                error=None,
                metadata={}
            )

        # Format records
        formatted_records = []
        for record in records:
            formatted_records.append({
                "date": record.record_date.strftime("%Y-%m-%d"),
                "task_type": record.task_type,
                "task_name": record.task_name,
                "duration": float(record.duration_hours),
                "description": record.value_description or ""
            })

        return AccessResponse(
            success=True,
            data=formatted_records,
            message=f"找到 {len(records)} 条记录",
            error=None,
            metadata={}
        )

    async def _get_statistics(self, request: AccessRequest, analysis: Dict) -> AccessResponse:
        """
        Get work statistics.

        Args:
            request: User request
            analysis: AI analysis result

        Returns:
            Response
        """
        # Get today's date
        today = date.today()
        start_date = today
        end_date = today

        # Check if user asked for specific time range
        user_input = request.input_text.lower()
        if "本周" in user_input or "这周" in user_input:
            # Get Monday of this week
            start_date = today - timedelta(days=today.weekday())
        elif "本月" in user_input or "这个月" in user_input:
            # Get first day of this month
            start_date = today.replace(day=1)
        elif "昨天" in user_input:
            start_date = today - timedelta(days=1)
            end_date = today - timedelta(days=1)

        # Get all records in the date range
        records = self.repository.get_all(
            user_id=int(request.user_id),
            limit=1000
        )

        # Filter by date range and calculate total
        total_hours = Decimal("0")
        period_records = []
        task_summary = {}

        for record in records:
            if start_date <= record.record_date <= end_date:
                total_hours += record.duration_hours
                period_records.append(record)

                # Group by task type
                task_type = record.task_type or "其他"
                if task_type not in task_summary:
                    task_summary[task_type] = Decimal("0")
                task_summary[task_type] += record.duration_hours

        if not period_records:
            return AccessResponse(
                success=True,
                data={"total_hours": 0, "record_count": 0},
                message=f"统计期间（{start_date} 至 {end_date}）暂无工作记录",
                error=None,
                metadata={}
            )

        # Format message
        time_desc = "今天"
        if start_date != end_date:
            time_desc = f"{start_date} 至 {end_date}"

        # Build detailed summary
        summary_parts = [f"{time_desc}工作 {total_hours:.1f} 小时"]
        if len(task_summary) > 1:
            task_details = "，".join([f"{t}: {h:.1f}h" for t, h in sorted(task_summary.items(), key=lambda x: x[1], reverse=True)])
            summary_parts.append(f"（{task_details}）")

        message = "".join(summary_parts)

        return AccessResponse(
            success=True,
            data={
                "total_hours": float(total_hours),
                "record_count": len(period_records),
                "task_breakdown": {k: float(v) for k, v in task_summary.items()}
            },
            message=message,
            error=None,
            metadata={}
        )
