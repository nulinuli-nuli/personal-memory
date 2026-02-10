"""SQL safety validator."""


class SQLSafetyValidator:
    """SQL safety validator."""

    DANGEROUS_KEYWORDS = [
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE",
        "INSERT", "UPDATE", "EXEC", "EXECUTE", "SCRIPT",
        "--", ";--", "/*", "*/", "xp_", "sp_"
    ]

    @classmethod
    def validate(cls, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate if SQL is safe.

        Args:
            sql: SQL query

        Returns:
            Tuple of (is_safe, error_message)
        """
        sql_upper = sql.upper()

        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                return False, f"Contains dangerous keyword: {keyword}"

        # Check for multiple statements (semicolon)
        if ";" in sql.strip() and not sql.strip().endswith(";"):
            return False, "Multiple statements detected"

        return True, None

    @classmethod
    def sanitize_identifier(cls, identifier: str) -> str:
        """
        Sanitize SQL identifier.

        Args:
            identifier: Identifier to sanitize

        Returns:
            Sanitized identifier
        """
        # Remove any non-alphanumeric characters (except underscore)
        return "".join(c for c in identifier if c.isalnum() or c == "_")
