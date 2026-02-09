"""Chart generation CLI commands."""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import asyncio
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.database import get_db
from src.core.exceptions import PersonalMemoryError
from src.core.schemas_chart import (
    ChartRequest, ChartDataPoint, TimeRangeFilter,
    ChartFilters, AggregationConfig, GroupingConfig
)
from src.ai.parser import TextParser
from src.chart.generator import ChartGenerator
from src.services.record_service import RecordService

app = typer.Typer(help="Generate financial charts")
console = Console()


def _resolve_time_range(time_range_filter: TimeRangeFilter, user_id: int, db) -> tuple[date, date]:
    """Resolve relative time range to actual dates."""
    today = date.today()

    if time_range_filter.relative_range == "today":
        return today, today
    elif time_range_filter.relative_range == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif time_range_filter.relative_range == "this_week":
        # Start of week (Monday)
        days_since_monday = today.weekday()
        start_date = today - timedelta(days=days_since_monday)
        return start_date, today
    elif time_range_filter.relative_range == "last_week":
        days_since_monday = today.weekday()
        end_date = today - timedelta(days=days_since_monday + 1)
        start_date = end_date - timedelta(days=6)
        return start_date, end_date
    elif time_range_filter.relative_range == "this_month":
        start_date = today.replace(day=1)
        return start_date, today
    elif time_range_filter.relative_range == "last_month":
        if today.month == 1:
            last_month = today.replace(year=today.year - 1, month=12, day=1)
        else:
            last_month = today.replace(month=today.month - 1, day=1)
        # Last day of last month
        from calendar import monthrange
        last_day = monthrange(last_month.year, last_month.month)[1]
        end_date = last_month.replace(day=last_day)
        return last_month, end_date
    elif time_range_filter.relative_range and time_range_filter.relative_range.startswith("last_X_"):
        # Parse "last_X_days", "last_X_weeks", "last_X_months"
        parts = time_range_filter.relative_range.split("_")
        if len(parts) >= 3:
            unit = parts[2]  # days, weeks, months
            x = time_range_filter.x_value or 30

            if unit == "days":
                start_date = today - timedelta(days=x)
                return start_date, today
            elif unit == "weeks":
                start_date = today - timedelta(weeks=x)
                return start_date, today
            elif unit == "months":
                # Approximate month as 30 days
                start_date = today - timedelta(days=x * 30)
                return start_date, today

    # Default: last 30 days
    start_date = today - timedelta(days=30)
    return start_date, today


@app.command()
def generate(
    text: str = typer.Argument(..., help="Natural language description of the chart you want"),
    output: str = typer.Option(None, "--output", "-o", help="Output filename (without extension)"),
    format: str = typer.Option("window", "--format", "-f", help="Output format: window, html, or png"),
):
    """Generate a financial chart from natural language description.

    Examples:
        pm chart generate "画一个饼图显示最近30天的支出分类占比"
        pm chart generate "用柱状图比较最近3个月的收入和支出" -o income_vs_expense
        pm chart generate "显示本周每天的消费趋势折线图"
    """
    try:
        with get_db() as db:
            service = RecordService(db)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Step 1: Parse chart request
                task = progress.add_task("正在解析图表请求...", total=None)
                parser = TextParser()
                try:
                    parsed = parser.parse_chart_request(text)
                except Exception as e:
                    console.print(f"[red]AI解析失败:[/red] {e}")
                    console.print("[yellow]提示:[/yellow] 请尝试更详细地描述您想要的图表，例如：")
                    console.print("  - '显示最近30天的支出分类饼图'")
                    console.print("  - '本月每周的收入趋势折线图'")
                    raise typer.Exit(1)

                # Validate and create ChartRequest
                try:
                    config = ChartRequest(**parsed)
                except Exception as e:
                    console.print(f"[red]配置验证失败:[/red] {e}")
                    raise typer.Exit(1)

                progress.update(task, description="正在获取财务数据...")

                # Step 2: Resolve time range
                start_date, end_date = _resolve_time_range(config.time_range, service.user_id, db)

                # Step 3: Get aggregated data
                data_points = service.finance_repo.get_aggregated_data(
                    user_id=service.user_id,
                    start_date=start_date,
                    end_date=end_date,
                    group_by=config.grouping.by,
                    metric=config.aggregation.metric,
                    record_type=config.filters.type,
                    primary_categories=config.filters.primary_categories,
                    secondary_categories=config.filters.secondary_categories,
                    time_granularity=config.grouping.time_granularity,
                )

                if not data_points:
                    console.print("[yellow]没有找到符合条件的数据[/yellow]")
                    console.print(f"时间范围: {start_date} 到 {end_date}")
                    raise typer.Exit(0)

                # Convert to ChartDataPoint
                chart_data = [
                    ChartDataPoint(
                        label=d["label"],
                        value=d["value"],
                    )
                    for d in data_points
                ]

                # Apply sorting
                if config.sort_by == "value":
                    reverse = config.sort_order == "desc"
                    chart_data.sort(key=lambda x: x.value, reverse=reverse)
                elif config.sort_by == "label":
                    reverse = config.sort_order == "desc"
                    chart_data.sort(key=lambda x: x.label, reverse=reverse)

                # Apply limit
                if config.limit and len(chart_data) > config.limit:
                    chart_data = chart_data[:config.limit]

                progress.update(task, description="正在生成图表...")

                # Step 4: Generate chart
                try:
                    generator = ChartGenerator()
                except ImportError as e:
                    console.print(f"[red]图表库未安装:[/red] {e}")
                    console.print("[yellow]请运行:[/yellow] poetry install")
                    raise typer.Exit(1)

                fig = generator.generate(chart_data, config)

                # Step 5: Save and display
                progress.update(task, description="正在保存图表...")

                # Generate filename
                if not output:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    chart_type_map = {
                        "pie": "pie",
                        "bar": "bar",
                        "line": "line",
                        "area": "area",
                        "stacked_bar": "stacked",
                        "scatter": "scatter",
                    }
                    output = f"finance_{chart_type_map.get(config.chart_type, 'chart')}_{timestamp}"

                if format == "window":
                    console.print(f"[cyan]正在弹出窗口显示图表...[/cyan]")
                    generator.show_window(chart_data, config)
                elif format == "html":
                    output_path = generator.save_html(fig, output)
                    console.print(f"[green]图表已保存:[/green] {output_path}")
                    console.print("[cyan]正在打开浏览器...[/cyan]")
                    generator.open_in_browser(fig, output)
                elif format == "png":
                    try:
                        output_path = generator.save_png(fig, output)
                        console.print(f"[green]图表已保存:[/green] {output_path}")
                    except Exception as e:
                        console.print(f"[red]PNG导出失败:[/red] {e}")
                        console.print("[yellow]回退到HTML格式...[/yellow]")
                        output_path = generator.save_html(fig, output)
                        console.print(f"[green]图表已保存:[/green] {output_path}")
                        generator.open_in_browser(fig, output)
                else:
                    console.print(f"[red]不支持的格式:[/red] {format}")
                    raise typer.Exit(1)

                console.print()
                console.print(f"[cyan]图表标题:[/cyan] {config.chart_title}")
                console.print(f"[cyan]数据点数量:[/cyan] {len(chart_data)}")
                console.print(f"[cyan]时间范围:[/cyan] {start_date} 到 {end_date}")

    except PersonalMemoryError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def examples():
    """Show examples of chart generation commands."""
    console.print()
    console.print("[bold cyan]财务图表生成示例[/bold cyan]")
    console.print()

    examples = [
        ("饼图 - 支出分类占比", "pm chart generate '画一个饼图显示最近30天的支出分类占比'"),
        ("柱状图 - 收支对比", "pm chart generate '用柱状图比较最近3个月的收入和支出'"),
        ("折线图 - 每日消费趋势", "pm chart generate '显示本周每天的消费趋势折线图'"),
        ("饼图 - 特定分类", "pm chart generate '餐饮和交通这两类的支出占比饼图'"),
        ("折线图 - 月度趋势", "pm chart generate '最近6个月的支出趋势折线图'"),
        ("柱状图 - 支付方式", "pm chart generate '按支付方式统计支出，显示柱状图'"),
    ]

    for desc, cmd in examples:
        console.print(f"  [yellow]{desc}[/yellow]")
        console.print(f"    {cmd}")
        console.print()
