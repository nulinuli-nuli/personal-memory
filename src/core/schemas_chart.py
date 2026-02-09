"""Pydantic schemas for chart configuration and data."""
from datetime import date
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class TimeRangeFilter(BaseModel):
    """Time range filter for chart queries."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    relative_range: Optional[Literal[
        "today", "yesterday", "this_week", "last_week",
        "this_month", "last_month", "last_X_days",
        "last_X_weeks", "last_X_months"
    ]] = None
    x_value: Optional[int] = Field(default=None, alias="X")  # For last_X_* patterns


class ChartFilters(BaseModel):
    """Filters for chart data."""
    type: Optional[Literal["income", "expense", "both"]] = "expense"
    primary_categories: Optional[List[str]] = None
    secondary_categories: Optional[List[str]] = None
    payment_methods: Optional[List[str]] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


class AggregationConfig(BaseModel):
    """Aggregation configuration."""
    dimension: Literal["primary_category", "secondary_category", "date", "payment_method", "type"]
    metric: Literal["sum", "count", "avg"] = "sum"


class GroupingConfig(BaseModel):
    """Grouping configuration."""
    by: Literal["primary_category", "secondary_category", "date", "payment_method", "type", "none"]
    time_granularity: Optional[Literal["day", "week", "month", "year"]] = None


class ChartRequest(BaseModel):
    """Parsed chart request from natural language."""
    chart_type: Literal["bar", "line", "pie", "area", "stacked_bar", "scatter"]
    time_range: TimeRangeFilter
    filters: ChartFilters
    aggregation: AggregationConfig
    grouping: GroupingConfig
    chart_title: str
    x_axis_label: str
    y_axis_label: str
    color_scheme: Optional[Literal["category", "type", "sequential"]] = None
    sort_by: Optional[Literal["value", "label", "date"]] = None
    sort_order: Optional[Literal["asc", "desc"]] = None
    limit: Optional[int] = None


class ChartDataPoint(BaseModel):
    """Single data point for chart rendering."""
    label: str
    value: float
    category: Optional[str] = None  # For grouping/coloring
    date: Optional[date] = None


class ChartData(BaseModel):
    """Complete chart data ready for rendering."""
    title: str
    chart_type: str
    data: List[ChartDataPoint]
    x_axis_label: str
    y_axis_label: str
    color_scheme: Optional[str] = None
    total_value: Optional[float] = None  # For percentage calculations
