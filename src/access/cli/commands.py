"""CLI commands."""
import asyncio
import typer
from pathlib import Path

from src.access.cli.adapter import CLIAdapter
from src.access.base import AccessRequest
from src.shared.database import init_db

app = typer.Typer(help="Personal Memory - 个人数据追踪CLI")


async def _process_command(text: str, prefix: str = "") -> str:
    """Helper function to process commands asynchronously."""
    adapter = CLIAdapter()
    await adapter.initialize_plugins()

    input_text = f"{prefix}{text}" if prefix else text
    request = AccessRequest(
        user_id="1",
        input_text=input_text,
        channel="cli",
        context={},
        metadata={}
    )

    response = await adapter.router.route(request)

    return adapter.format_response(response)


@app.command()
def add(text: str):
    """
    添加记录（自动路由到合适的插件）

    Example: pm add "今天花了50块买午饭"
    """
    result = asyncio.run(_process_command(text))
    typer.echo(result)


@app.command()
def query(text: str):
    """
    查询数据

    Example: pm query "本周花了多少钱"
    """
    result = asyncio.run(_process_command(text, prefix="查询"))
    typer.echo(result)


@app.command()
def chat(text: str):
    """
    多轮对话

    Example: pm chat "我今天花了50块"
    """
    result = asyncio.run(_process_command(text))
    typer.echo(result)


# Plugin management sub-commands
plugin_app = typer.Typer(help="插件管理")
app.add_typer(plugin_app, name="plugin")


@plugin_app.command()
def list():
    """列出所有插件"""
    async def _list():
        adapter = CLIAdapter()
        await adapter.initialize_plugins()
        plugins = adapter.plugin_manager.list_plugins()

        typer.echo("\n可用插件:")
        for p in plugins:
            typer.echo(f"  - {p['display_name']} ({p['name']}) v{p['version']}")
            typer.echo(f"    {p['description']}")
            typer.echo(f"    状态: {p['state']}")
            typer.echo("")

    asyncio.run(_list())


@plugin_app.command()
def reload(name: str):
    """热重载插件"""
    async def _reload():
        adapter = CLIAdapter()
        await adapter.initialize_plugins()
        success = await adapter.plugin_manager.reload_plugin(name)
        if success:
            typer.echo(f"✓ 插件 '{name}' 重载成功")
        else:
            typer.echo(f"✗ 插件 '{name}' 重载失败", err=True)

    asyncio.run(_reload())
