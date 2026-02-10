"""Date utilities."""
from datetime import datetime, date
from typing import Optional


def parse_date(date_str: Optional[str]) -> date:
    """
    Parse date string.

    Args:
        date_str: Date string in various formats

    Returns:
        Parsed date or today if None or invalid
    """
    if not date_str:
        return date.today()

    # Try various formats
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m-%d",
        "%m/%d",
        "%Y年%m月%d日",
        "%m月%d日",
    ]

    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            # If year is missing (1900 default), use current year
            if parsed_date.year == 1900:
                return parsed_date.replace(year=date.today().year)
            return parsed_date
        except ValueError:
            continue

    # Default to today
    return date.today()


def get_date_range(period: str, base_date: Optional[date] = None) -> tuple[date, date]:
    """
    Get date range for a period.

    Args:
        period: Period like 'today', 'week', 'month', 'year'
        base_date: Base date for calculation (default: today)

    Returns:
        Tuple of (start_date, end_date)
    """
    if base_date is None:
        base_date = date.today()

    if period == "today":
        return base_date, base_date

    elif period == "week":
        # Start of week (Monday)
        start = base_date
        while start.weekday() != 0:
            start = start.replace(day=start.day - 1)
        # End of week (Sunday)
        end = start.replace(day=start.day + 6)
        return start, end

    elif period == "month":
        # Start of month
        start = base_date.replace(day=1)
        # End of month
        if base_date.month == 12:
            end = base_date.replace(year=base_date.year + 1, month=1, day=1)
            end = end.replace(day=end.day - 1)
        else:
            end = base_date.replace(month=base_date.month + 1, day=1)
            end = end.replace(day=end.day - 1)
        return start, end

    elif period == "year":
        # Start of year
        start = base_date.replace(month=1, day=1)
        # End of year
        end = base_date.replace(month=12, day=31)
        return start, end

    else:
        # Default to today
        return base_date, base_date
