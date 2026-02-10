"""CLI output formatters."""
from typing import Any, List


def format_success(message: str) -> str:
    """Format success message."""
    return f"✓ {message}"


def format_error(message: str) -> str:
    """Format error message."""
    return f"✗ {message}"


def format_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    Format data as table.

    Args:
        headers: Table headers
        rows: Table rows

    Returns:
        Formatted table string
    """
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Build table
    lines = []

    # Header
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    lines.append(header_line)

    # Separator
    separator = "-+-".join("-" * w for w in col_widths)
    lines.append(separator)

    # Rows
    for row in rows:
        row_line = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        lines.append(row_line)

    return "\n".join(lines)


def format_list(items: List[str]) -> str:
    """
    Format items as list.

    Args:
        items: List items

    Returns:
        Formatted list string
    """
    return "\n".join(f"  - {item}" for item in items)
