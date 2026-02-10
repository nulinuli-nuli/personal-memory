"""SQL query builder."""
from typing import List, Optional


class QueryBuilder:
    """SQL query builder."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset builder state."""
        self._select = []
        self._from = ""
        self._where = []
        self._group_by = []
        self._order_by = []
        self._limit = None
        self._offset = 0

    def select(self, *columns: str) -> "QueryBuilder":
        """
        Add SELECT columns.

        Args:
            *columns: Column names

        Returns:
            Self for chaining
        """
        self._select.extend(columns)
        return self

    def from_table(self, table: str) -> "QueryBuilder":
        """
        Set FROM table.

        Args:
            table: Table name

        Returns:
            Self for chaining
        """
        self._from = table
        return self

    def where(self, condition: str) -> "QueryBuilder":
        """
        Add WHERE condition.

        Args:
            condition: WHERE condition

        Returns:
            Self for chaining
        """
        self._where.append(condition)
        return self

    def group_by(self, *columns: str) -> "QueryBuilder":
        """
        Add GROUP BY columns.

        Args:
            *columns: Column names

        Returns:
            Self for chaining
        """
        self._group_by.extend(columns)
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "QueryBuilder":
        """
        Add ORDER BY column.

        Args:
            column: Column name
            direction: ASC or DESC

        Returns:
            Self for chaining
        """
        self._order_by.append(f"{column} {direction}")
        return self

    def limit(self, limit: int) -> "QueryBuilder":
        """
        Set LIMIT.

        Args:
            limit: Maximum number of results

        Returns:
            Self for chaining
        """
        self._limit = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder":
        """
        Set OFFSET.

        Args:
            offset: Number of results to skip

        Returns:
            Self for chaining
        """
        self._offset = offset
        return self

    def build(self) -> str:
        """
        Build SQL query.

        Returns:
            SQL query string
        """
        parts = []

        # SELECT
        if self._select:
            parts.append(f"SELECT {', '.join(self._select)}")
        else:
            parts.append("SELECT *")

        # FROM
        if self._from:
            parts.append(f"FROM {self._from}")

        # WHERE
        if self._where:
            parts.append(f"WHERE {' AND '.join(self._where)}")

        # GROUP BY
        if self._group_by:
            parts.append(f"GROUP BY {', '.join(self._group_by)}")

        # ORDER BY
        if self._order_by:
            parts.append(f"ORDER BY {', '.join(self._order_by)}")

        # LIMIT and OFFSET
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")
        if self._offset > 0:
            parts.append(f"OFFSET {self._offset}")

        return "\n".join(parts)
