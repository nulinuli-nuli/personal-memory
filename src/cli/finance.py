"""Finance CLI commands."""
from datetime import date, datetime, timedelta
from decimal import Decimal

import typer
from rich.console import Console
from rich.table import Table

from src.core.database import get_db
from src.core.exceptions import PersonalMemoryError
from src.services.record_service import RecordService

app = typer.Typer(help="Finance tracking commands")
console = Console()


@app.command()
def add(text: str = typer.Argument(..., help="Natural language description of the transaction")):
    """Add a finance record (e.g., '今天花了50块买午饭')"""
    try:
        with get_db() as db:
            import asyncio
            service = RecordService(db)

            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(service.add_finance_from_text(text))
            loop.close()

            # Handle multiple records
            records = result if isinstance(result, list) else [result]

            # Display results
            for record in records:
                type_icon = "💰" if record.type == "income" else "💸"
                category_display = f"{record.primary_category}"
                if record.secondary_category:
                    category_display += f" > {record.secondary_category}"
                console.print(
                    f"{type_icon} [green]Successfully added[/green]: "
                    f"{record.type} {record.amount}元 - {record.description or category_display}"
                )
    except PersonalMemoryError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("list")
def list_records(
    days: int = typer.Option(7, help="Number of days to look back"),
    type: str = typer.Option(None, help="Filter by type (income/expense)"),
):
    """List recent finance records"""
    try:
        with get_db() as db:
            service = RecordService(db)
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            if type:
                records = service.finance_repo.get_by_date_range(
                    user_id=service.user_id,
                    start_date=start_date,
                    end_date=end_date,
                )
                records = [r for r in records if r.type == type]
            else:
                records = service.finance_repo.get_by_date_range(
                    user_id=service.user_id,
                    start_date=start_date,
                    end_date=end_date,
                )

            if not records:
                console.print("[yellow]No records found.[/yellow]")
                return

            # Create table
            table = Table(title=f"Finance Records (Last {days} days)")
            table.add_column("Date", style="cyan")
            table.add_column("Type", style="bold")
            table.add_column("Amount", justify="right", style="yellow")
            table.add_column("Category", style="green")
            table.add_column("Description")

            total_income = Decimal("0")
            total_expense = Decimal("0")

            for record in records:
                type_display = "💰 收入" if record.type == "income" else "💸 支出"
                category_display = record.primary_category or "-"
                if record.secondary_category:
                    category_display += f" > {record.secondary_category}"
                table.add_row(
                    str(record.record_date),
                    type_display,
                    f"¥{record.amount:.2f}",
                    category_display,
                    record.description or "-",
                )
                if record.type == "income":
                    total_income += record.amount
                else:
                    total_expense += record.amount

            console.print(table)
            console.print()
            console.print(f"[cyan]Total Income: [green]¥{total_income:.2f}[/green]")
            console.print(f"[cyan]Total Expense: [red]¥{total_expense:.2f}[/red]")
            console.print(f"[cyan]Net: [yellow]¥{total_income - total_expense:.2f}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def stats(
    days: int = typer.Option(30, help="Number of days to analyze"),
):
    """Show finance statistics"""
    try:
        with get_db() as db:
            service = RecordService(db)
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Get category summary
            summary = service.finance_repo.get_category_summary(
                user_id=service.user_id,
                start_date=start_date,
                end_date=end_date,
            )

            if not summary:
                console.print("[yellow]No data for the selected period.[/yellow]")
                return

            # Create table
            table = Table(title=f"Category Summary (Last {days} days)")
            table.add_column("Category", style="cyan")
            table.add_column("Type", style="bold")
            table.add_column("Total", justify="right", style="yellow")

            for item in sorted(summary, key=lambda x: x["total"], reverse=True):
                type_display = "💰 收入" if item["type"] == "income" else "💸 支出"
                table.add_row(
                    item["category"] or "未分类",
                    type_display,
                    f"¥{item['total']:.2f}",
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
