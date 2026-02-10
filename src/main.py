"""Main CLI entry point for Personal Memory."""
import asyncio
import sys
import os
import typer
from rich.console import Console

# Fix Windows console encoding issue
if sys.platform == "win32":
    import codecs
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # Set environment variable for UTF-8 mode
    os.environ["PYTHONIOENCODING"] = "utf-8"

from src.shared.config import settings
from src.shared.database import init_db, reset_db

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

        reset_db()
        console.print("[green]✓[/green] Database reset successfully!")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to reset database: {e}")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information"""
    console.print("Personal Memory v2.0.0 - AI-Powered Personal Data Tracking")
    console.print("\n主要命令:")
    console.print("  pm chat <文本>     智能对话，自动识别你的需求")
    console.print("  pm init           初始化数据库")
    console.print("  pm reset          重置数据库（清空所有数据）")
    console.print("  pm plugin list-plugins   查看所有可用插件")
    console.print("  pm help           显示帮助信息")


@app.command(name="help")
def help_cmd():
    """显示帮助信息和使用示例"""
    console.print("\n[bold]Personal Memory - AI驱动的个人数据追踪[/bold]\n")
    console.print("使用 [cyan]pm chat[/cyan] 命令，用自然语言与系统交互：\n")
    console.print("[yellow]财务记录示例：[/yellow]")
    console.print('  pm chat "今天花了50块钱买午饭"')
    console.print('  pm chat "收到工资5000元"')
    console.print('  pm chat "今天买了杯咖啡，18块"')
    console.print("")
    console.print("[yellow]工作记录示例：[/yellow]")
    console.print('  pm chat "今天工作了8小时，完成了用户认证模块"')
    console.print('  pm chat "下午开会2小时，讨论项目进度"')
    console.print("")
    console.print("[yellow]查询数据示例：[/yellow]")
    console.print('  pm chat "查询今天的财务记录"')
    console.print('  pm chat "这周工作了多少小时"')
    console.print('  pm chat "看看最近的消费情况"')
    console.print("")
    console.print("[yellow]管理命令：[/yellow]")
    console.print("  pm init              初始化数据库")
    console.print("  pm reset             重置数据库（清空数据）")
    console.print("  pm plugin list-plugins  查看可用插件")
    console.print("")
    console.print("[dim]提示: 系统会自动识别你的意图，调用合适的插件处理请求。[/dim]")


@app.command()
def serve():
    """
    Start the Feishu bot service.

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

    # Import and start the Feishu client
    try:
        from src.access.feishu.client import LarkBotClient

        client = LarkBotClient()
        console.print("\n[yellow]提示:[/yellow] 服务运行中，按 Ctrl+C 停止\n")
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


# Main command - AI-powered intelligent routing
@app.command()
def chat(text: str):
    """智能对话 - 自动识别并处理你的需求（添加记录、查询数据、统计分析等）"""
    from src.access.cli.adapter import CLIAdapter
    from src.access.base import AccessRequest
    from rich.markdown import Markdown

    async def _process():
        adapter = CLIAdapter()
        await adapter.initialize_plugins()
        request = AccessRequest(
            user_id="1",
            input_text=text,
            channel="cli",
            context={},
            metadata={}
        )
        return await adapter.router.route(request)

    response = asyncio.run(_process())

    if not response.success:
        console.print(f"[red]错误: {response.error}[/red]")
        raise typer.Exit(1)

    # Print summary
    if response.message:
        console.print(f"\n{response.message}")

    # Print Markdown if available
    if response.metadata and "markdown" in response.metadata:
        console.print(Markdown(response.metadata["markdown"]))


# Plugin management commands
plugin_app = typer.Typer(help="插件管理")
app.add_typer(plugin_app, name="plugin")


@plugin_app.command()
def list_plugins():
    """列出所有插件"""
    from src.access.cli.adapter import CLIAdapter

    async def _list():
        adapter = CLIAdapter()
        await adapter.initialize_plugins()
        plugins = adapter.plugin_manager.list_plugins()

        console.print("\n可用插件:")
        for p in plugins:
            console.print(f"  - {p['display_name']} ({p['name']}) v{p['version']}")
            console.print(f"    {p['description']}")
            console.print(f"    状态: {p['state']}")
            console.print("")

    asyncio.run(_list())


@plugin_app.command()
def reload(name: str):
    """热重载插件"""
    from src.access.cli.adapter import CLIAdapter

    async def _reload():
        adapter = CLIAdapter()
        await adapter.initialize_plugins()
        success = await adapter.plugin_manager.reload_plugin(name)
        if success:
            console.print(f"✓ 插件 '{name}' 重载成功")
        else:
            console.print(f"✗ 插件 '{name}' 重载失败", style="red")

    asyncio.run(_reload())


if __name__ == "__main__":
    app()
