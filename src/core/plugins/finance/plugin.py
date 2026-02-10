"""Finance plugin - handles finance-related records and queries."""
from typing import Dict, Any, List
from decimal import Decimal
from datetime import date, timedelta
import logging

from src.access.base import AccessRequest, AccessResponse
from src.core.plugin.base import BasePlugin
from src.storage.repositories.finance_repo import FinanceRepository
from src.core.common.date_utils import parse_date

logger = logging.getLogger(__name__)


class FinancePlugin(BasePlugin):
    """Finance plugin - handles income/expense records and queries."""

    @property
    def name(self) -> str:
        return "finance"

    @property
    def display_name(self) -> str:
        return "财务管理"

    @property
    def description(self) -> str:
        return "处理收支记录、账单管理、财务统计等功能。支持添加收入/支出记录，AI智能查询财务数据。"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _create_repository(self):
        """Create finance repository."""
        return FinanceRepository(self.db)

    async def execute(
        self,
        request: AccessRequest,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> AccessResponse:
        """
        Execute finance plugin functionality.

        Args:
            request: User request
            context: Conversation context
            params: Parameters (empty - router doesn't pass anything)

        Returns:
            Response result
        """
        try:
            # 1. Intent recognition - add or query
            intent = await self._recognize_intent(request.input_text)

            if intent["action"] == "add":
                return await self._add_records(request, intent)
            elif intent["action"] == "query":
                return await self._query_with_ai(request, intent)
            else:
                return AccessResponse(
                    success=False,
                    error=f"未知操作类型: {intent['action']}",
                    message="",
                    data=None,
                    metadata={}
                )

        except Exception as e:
            logger.error(f"Finance plugin error: {e}", exc_info=True)
            return AccessResponse(
                success=False,
                error=f"操作失败: {str(e)}",
                message="",
                data=None,
                metadata={}
            )

    async def _recognize_intent(self, text: str) -> Dict:
        """
        Recognize user intent - add or query.

        Args:
            text: User input text

        Returns:
            Intent recognition result
        """
        prompt = f"""分析用户输入，判断是添加记录还是查询数据。

用户输入: {text}

请返回JSON格式:
{{
    "action": "add" 或 "query"
}}

## 判断规则:

1. **add** - 添加记录
   - 用户想要记录新的收支
   - 关键词：花了、收入、工资、买了、支付、消费等
   - 例如：今天花了50块买午饭、收到工资5000元

2. **query** - 查询数据
   - 用户想要查看财务数据、统计、明细
   - 关键词：查询、多少、统计、看看、记录、汇总、明细等
   - 例如：今天花了多少、查询本月的支出、看看最近的消费
"""

        return self.ai.parse(prompt, context={})

    async def _add_records(self, request: AccessRequest, intent: Dict) -> AccessResponse:
        """
        Add finance records (supports batch insert).

        Args:
            request: User request
            intent: Intent with action="add"

        Returns:
            Response
        """
        # Extract records using AI
        extraction_prompt = f"""从用户输入中提取财务记录信息，返回JSON格式。

用户输入: {request.input_text}

今天日期: {date.today().strftime("%Y-%m-%d")}

请返回JSON格式:
{{
    "records": [
        {{
            "type": "income" 或 "expense",
            "amount": 金额数字,
            "primary_category": "主要分类（餐饮/交通/购物/工资/奖金等）",
            "secondary_category": "次要分类（如：午餐/打车/衣服等）",
            "description": "描述",
            "record_date": "YYYY-MM-DD",
            "payment_method": "支付方式（可选）",
            "merchant": "商家（可选）",
            "tags": ["标签1", "标签2"]
        }}
    ]
}}

## 注意事项:
1. 如果用户输入包含多条记录，返回多条
2. amount必须是数字，不要带单位
3. record_date默认为今天
4. 如果提到"花了"、"支付"等，type为"expense"
5. 如果提到"收入"、"工资"、"奖金"等，type为"income"

## 示例:
输入: "今天花了50块买午饭，又花了18块买咖啡"
输出:
{{
    "records": [
        {{"type": "expense", "amount": 50, "primary_category": "餐饮", "secondary_category": "午餐", "description": "买午饭", "record_date": "2025-02-10"}},
        {{"type": "expense", "amount": 18, "primary_category": "餐饮", "secondary_category": "咖啡", "description": "买咖啡", "record_date": "2025-02-10"}}
    ]
}}
"""

        result = self.ai.parse(extraction_prompt, context={})
        records_data = result.get("records", [])

        if not records_data:
            return AccessResponse(
                success=False,
                error="未能识别到有效的财务记录",
                message="",
                data=None,
                metadata={}
            )

        # Batch insert
        inserted_records = []
        for record_data in records_data:
            try:
                amount = Decimal(str(record_data.get("amount", 0)))
                if amount <= 0:
                    continue

                record_date = parse_date(record_data.get("record_date"))

                record = self.repository.create(
                    user_id=int(request.user_id),
                    type=record_data.get("type", "expense"),
                    amount=amount,
                    primary_category=record_data.get("primary_category", "其他"),
                    secondary_category=record_data.get("secondary_category"),
                    description=record_data.get("description"),
                    payment_method=record_data.get("payment_method"),
                    merchant=record_data.get("merchant"),
                    is_recurring=False,
                    tags=record_data.get("tags"),
                    raw_text=request.input_text,
                    record_date=record_date
                )
                inserted_records.append(record)
            except Exception as e:
                logger.warning(f"Failed to insert record: {e}")
                continue

        if not inserted_records:
            return AccessResponse(
                success=False,
                error="没有成功添加任何记录",
                message="",
                data=None,
                metadata={}
            )

        # Format response message
        count = len(inserted_records)
        total_amount = sum(r.amount for r in inserted_records)
        type_cn = "支出" if inserted_records[0].type == "expense" else "收入"

        if count == 1:
            message = f"已添加：{inserted_records[0].description or inserted_records[0].primary_category} ¥{inserted_records[0].amount} ({type_cn})"
        else:
            message = f"已添加 {count} 条记录，共 ¥{total_amount} ({type_cn})"

        return AccessResponse(
            success=True,
            data={"count": count, "total": float(total_amount)},
            message=message,
            error=None,
            metadata={}
        )

    async def _query_with_ai(self, request: AccessRequest, intent: Dict) -> AccessResponse:
        """
        Query using AI-generated SQL and format results as Markdown.

        Args:
            request: User request
            intent: Intent with action="query"

        Returns:
            Response with formatted Markdown
        """
        # Step 1: Get table schema
        schema_prompt = """## 财务记录表结构 (finance_records)

字段说明:
- id: 主键
- user_id: 用户ID
- type: 类型 (income=收入, expense=支出)
- amount: 金额 (DECIMAL)
- primary_category: 主要分类 (如: 餐饮、交通、购物)
- secondary_category: 次要分类 (如: 午餐、打车)
- description: 描述
- payment_method: 支付方式
- merchant: 商家
- is_recurring: 是否周期性
- tags: 标签 (JSON数组)
- raw_text: 原始文本
- record_date: 记录日期 (DATE)
- created_at: 创建时间
"""

        # Step 2: Generate SQL using AI
        sql_prompt = f"""{schema_prompt}

用户查询: {request.input_text}

当前日期: {date.today().strftime("%Y-%m-%d")}

请根据用户需求生成SQL查询语句，只返回SQL，不要有其他内容。

## 注意事项:
1. 使用SQLite语法
2. 金额使用SUM计算，按类型分类
3. 日期筛选使用 record_date
4. 用户ID为 {request.user_id}
5. 只返回SQL语句，不要markdown标记
6. LIMIT限制在100条以内

## 示例:
用户: "今天花了多少"
SQL: SELECT SUM(amount) as total FROM finance_records WHERE user_id = 1 AND type = 'expense' AND record_date = '2025-02-10'

用户: "本周的支出统计"
SQL: SELECT primary_category, SUM(amount) as total FROM finance_records WHERE user_id = 1 AND type = 'expense' AND record_date >= '2025-02-03' GROUP BY primary_category

用户: "最近的消费记录"
SQL: SELECT record_date, type, amount, primary_category, description FROM finance_records WHERE user_id = 1 AND type = 'expense' ORDER BY record_date DESC LIMIT 10
"""

        sql_result = self.ai.parse(sql_prompt, context={})
        sql = sql_result.get("sql", "")

        if not sql:
            # Fallback: extract SQL from text
            import re
            sql_match = re.search(r'SELECT.*?(?=;|$)', str(sql_result), re.IGNORECASE | re.DOTALL)
            if sql_match:
                sql = sql_match.group(0)
            else:
                return AccessResponse(
                    success=False,
                    error="无法生成查询语句",
                    message="",
                    data=None,
                    metadata={}
                )

        # Step 3: Execute SQL (safely)
        try:
            from sqlalchemy import text
            from src.shared.database import SessionLocal

            db = SessionLocal()
            try:
                result = db.execute(text(sql))
                rows = result.fetchall()
                columns = result.keys()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return AccessResponse(
                success=False,
                error=f"查询执行失败: {str(e)}",
                message="",
                data=None,
                metadata={}
            )

        if not rows:
            return AccessResponse(
                success=True,
                data=[],
                message="没有找到相关记录",
                error=None,
                metadata={}
            )

        # Step 4: Format results as Markdown using AI
        data_str = self._format_query_results(columns, rows)

        format_prompt = f"""将查询结果格式化为Markdown表格。

用户查询: {request.input_text}

查询结果:
{data_str}

请返回JSON格式:
{{
    "markdown": "格式化的Markdown内容",
    "summary": "简短摘要（1-2句话）"
}}

## 格式要求:
1. 使用Markdown表格
2. 金额保留2位小数，加上¥符号
3. 日期格式: YYYY-MM-DD
4. 如果是统计数据，突出显示总计
5. summary用一句话概括查询结果

## 示例:
用户: "今天的支出"
输出:
{{
    "markdown": "# 💰 今天的支出统计\\n\\n| 日期 | 分类 | 描述 | 金额 |\\n|------|------|------|------|\\n| 2025-02-10 | 餐饮 | 买午饭 | ¥50.00 |\\n| 2025-02-10 | 餐饮 | 买咖啡 | ¥18.00 |\\n\\n**总计: ¥68.00**",
    "summary": "今天共支出¥68.00，2笔记录"
}}
"""

        formatted = self.ai.parse(format_prompt, context={})

        return AccessResponse(
            success=True,
            data={"rows_count": len(rows)},
            message=formatted.get("summary", ""),
            error=None,
            metadata={"markdown": formatted.get("markdown", "")}
        )

    def _format_query_results(self, columns: List[str], rows: List) -> str:
        """Format query results as text for AI processing."""
        lines = ["列名: " + ", ".join(columns)]
        lines.append("数据:")
        for row in rows:
            row_str = " | ".join(str(v) if v is not None else "" for v in row)
            lines.append(f"  {row_str}")
        return "\n".join(lines)
