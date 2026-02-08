"""AI generated SQL safe execution service."""
import re
from typing import Any, List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import text


class SQLSafetyError(Exception):
    """SQL safety validation failed."""
    pass


class QueryService:
    """Safe SQL query execution service."""

    FORBIDDEN_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
        "CREATE", "TRUNCATE", "EXEC", "EXECUTE",
        "GRANT", "REVOKE", "ATTACH", "DETACH"
    ]

    def __init__(self, db: Session):
        """
        Initialize query service.

        Args:
            db: Database session
        """
        self.db = db

    def validate_sql(self, sql: str) -> None:
        """
        Validate SQL safety.

        Args:
            sql: SQL query to validate

        Raises:
            SQLSafetyError: If SQL is unsafe
        """
        sql_upper = sql.upper().strip()
        print(f"  → 验证 SQL: {sql_upper}", flush=True)
        # Must be SELECT
        if not sql_upper.startswith("SELECT"):
            raise SQLSafetyError("Only SELECT queries are allowed")

        # Check forbidden keywords
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in sql_upper:
                raise SQLSafetyError(f"Forbidden keyword detected: {keyword}")

        # Check suspicious patterns (SQL injection)
        suspicious = [r";.*SELECT", r"--", r"/\*", r"xp_", r"sp_"]
        for pattern in suspicious:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                raise SQLSafetyError("Suspicious SQL pattern detected")

        # Must contain user_id filter
        if "user_id" not in sql.lower():
            raise SQLSafetyError("Query must include user_id filter")

        # Check for comment attempts
        if "--" in sql or "/*" in sql:
            raise SQLSafetyError("SQL comments are not allowed")

    def execute_query(self, sql: str, user_id: int, max_rows: int = 100) -> List[Dict[str, Any]]:
        """
        Execute validated SQL query.

        Args:
            sql: SQL query to execute
            user_id: User ID for filtering
            max_rows: Maximum number of rows to return

        Returns:
            List of result rows as dictionaries
        """
        self.validate_sql(sql)

        # Inject user_id and row limit
        sql_final = sql.replace("{user_id}", str(user_id))
        if "LIMIT" not in sql_final.upper():
            sql_final += f" LIMIT {max_rows}"

        result = self.db.execute(text(sql_final))
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]

        return rows

    def format_results(self, rows: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
        """
        Format query results for display.

        Args:
            rows: Query result rows
            metadata: Query metadata (explanation, summary, chart_type)

        Returns:
            Formatted result string
        """
        if not rows:
            return f"📊 没有找到匹配的记录\n\n{metadata.get('summary', 'Query completed')}"

        # Single aggregate result
        if len(rows) == 1 and len(rows[0]) == 1:
            value = list(rows[0].values())[0]
            if isinstance(value, (int, float)):
                # Format numeric values
                if isinstance(value, float):
                    formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                return f"📊 {metadata.get('summary', '查询结果')}\n\n** {formatted_value} **"

        # Table format
        result = f"📊 {metadata.get('summary', '查询结果')}\n\n"
        if metadata.get('explanation'):
            result += f"{metadata['explanation']}\n\n"

        if rows:
            headers = list(rows[0].keys())
            result += " | ".join(str(h) for h in headers) + "\n"
            result += "-" * min(80, len(" | ".join(str(h) for h in headers))) + "\n"

            for row in rows[:20]:
                values = [str(v) if v is not None else "N/A" for v in row.values()]
                # Truncate long values
                values = [v[:50] + "..." if len(v) > 50 else v for v in values]
                result += " | ".join(values) + "\n"

            if len(rows) > 20:
                result += f"\n... 还有 {len(rows) - 20} 条记录\n"

        return result
