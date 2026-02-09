"""Main CLI entry point for Personal Memory."""
import subprocess
import sys

import typer
from rich.console import Console

from src.cli import finance, health, work, leisure, learning, social, goal, report
from src.config import settings
from src.core.database import init_db

app = typer.Typer(help="Personal Memory - Track your life with AI")
console = Console()


@app.command()
def init():
    """Initialize the database"""
    try:
        init_db()
        console.print("[green]✓[/green] Database initialized successfully!")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to initialize database: {e}")
        raise typer.Exit(1)


@app.command()
def reset():
    """Reset the database (drop all tables and recreate)"""
    try:
        console.print("[yellow]⚠[/yellow] This will delete all data!")
        confirm = typer.confirm("Are you sure you want to reset the database?")
        if not confirm:
            console.print("Cancelled.")
            raise typer.Exit(0)

        from src.core.database import reset_db
        reset_db()
        console.print("[green]✓[/green] Database reset successfully!")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to reset database: {e}")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information"""
    console.print("Personal Memory v0.1.0")


@app.command()
def serve():
    """
    Start the Feishu bot service (using SDK long-connection).

    No public URL required - works locally!

    Make sure to configure FEISHU_APP_ID and FEISHU_APP_SECRET
    environment variables before starting.
    """
    # Check Feishu configuration
    if not settings.feishu_app_id or not settings.feishu_app_secret:
        console.print("[red]✗[/red] 飞书配置缺失！")
        console.print("\n请在 .env 中设置：")
        console.print("  FEISHU_APP_ID=cli_xxx")
        console.print("  FEISHU_APP_SECRET=xxx")
        console.print("\n详细说明请参考 FEISHU_SETUP.md")
        raise typer.Exit(1)

    console.print("[blue]🚀[/blue] 启动飞书机器人服务...")
    console.print(f"  App ID: {settings.feishu_app_id}")
    console.print(f"  Database: {settings.database_url}")

    # Create WebSocket client
    try:
        from src.feishu.client import LarkWSClient
        client = LarkWSClient()

        console.print("\n[yellow]提示:[/yellow] 服务运行中，按 Ctrl+C 停止\n")

        # Start connection (blocking)
        client.start()

    except ImportError:
        console.print("[red]✗[/red] lark-oapi 未安装！")
        console.print("请运行: [cyan]pip install lark-oapi[/cyan]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]服务已停止[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]✗[/red] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


# Register sub-commands
app.add_typer(finance.app, name="finance", help="Finance tracking")
app.add_typer(health.app, name="health", help="Health tracking")
app.add_typer(work.app, name="work", help="Work tracking")
app.add_typer(leisure.app, name="leisure", help="Leisure tracking")
app.add_typer(learning.app, name="learning", help="Learning tracking")
app.add_typer(social.app, name="social", help="Social tracking")
app.add_typer(goal.app, name="goal", help="Goal tracking")
app.add_typer(report.app, name="report", help="Generate reports")


if __name__ == "__main__":
    app()
