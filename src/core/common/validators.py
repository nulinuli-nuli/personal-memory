"""Validation utilities."""
from datetime import date
from decimal import Decimal
from typing import Tuple, Optional


def validate_amount(amount: float) -> Tuple[bool, Optional[str]]:
    """
    Validate amount value.

    Args:
        amount: Amount to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return False, "金额必须大于0"
        if amount_decimal > 999999999.99:
            return False, "金额超出范围"
        return True, None
    except (ValueError, TypeError):
        return False, "无效的金额格式"


def validate_duration(duration: float) -> Tuple[bool, Optional[str]]:
    """
    Validate duration value.

    Args:
        duration: Duration in hours

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        duration_decimal = Decimal(str(duration))
        if duration_decimal <= 0:
            return False, "时长必须大于0"
        if duration_decimal > 24:
            return False, "时长不能超过24小时"
        return True, None
    except (ValueError, TypeError):
        return False, "无效的时长格式"


def validate_date_range(start_date: date, end_date: date) -> Tuple[bool, Optional[str]]:
    """
    Validate date range.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Tuple of (is_valid, error_message)
    """
    if start_date > end_date:
        return False, "开始日期不能晚于结束日期"
    return True, None
