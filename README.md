# Personal Memory System

A lightweight personal data recording and management platform powered by AI natural language processing with a four-layer plugin architecture.

## Features

### v2.0 - Four-Layer Plugin Architecture

- 🤖 **AI-Driven Routing**: Automatically understands user intent and routes to appropriate plugins
- 🔌 **Plugin System**: Hot-reloadable plugins for easy extensibility
- 💬 **Multi-turn Conversations**: Context-aware dialogue support
- 🎯 **Smart CLI**: Unified commands (`add`, `query`, `chat`) instead of domain-specific commands
- 📊 **Dual Access**: Both CLI and Feishu bot support

### Built-in Plugins

- 💰 **Finance Plugin**: Track income and expenses with automatic categorization
- 💼 **Work Plugin**: Log tasks, hours, and achievements

### v1.0 Features (Deprecated)

The following features from v1.0 are **not included** in v2.0 by default but can be added as custom plugins:
- 😴 Health Monitoring
- 🎮 Leisure Activities
- 📚 Learning Records
- 🎯 Goal Management
- 👥 Social Activities

See [PLUGIN_GUIDE.md](docs/PLUGIN_GUIDE.md) to learn how to create your own plugins.

## Architecture

Personal Memory v2.0 uses a **four-layer architecture**:

```
Layer 1 (Access) → Layer 2 (Routing) → Layer 3 (Core/Plugins) → Layer 4 (Storage)
    CLI/Feishu         AI Router          Finance/Work         Database
```

- **Access Layer**: Adapters for different channels (CLI, Feishu)
- **Routing Layer**: AI-driven plugin routing with context management
- **Core Layer**: Plugin system with hot-reload support
- **Storage Layer**: Repositories and database abstraction

For detailed architecture documentation, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/personal-memory.git
cd personal-memory

# Install in editable mode
pip install -e .

# Or with Poetry
poetry install

# Create .env file from example
cp .env.example .env

# Edit .env with your configuration
# Important: Set AI_PROVIDER and AI_API_KEY
```

## Configuration

Edit the `.env` file with your settings:

```bash
# AI Provider Configuration (choose one)
AI_PROVIDER=openai                    # Options: openai, anthropic
AI_API_KEY=your-api-key-here
AI_BASE_URL=https://api.openai.com/v1  # Optional: For proxy/relay services
AI_MODEL=gpt-4o-mini

# Or use Anthropic
# AI_PROVIDER=anthropic
# AI_API_KEY=sk-ant-your-key
# AI_MODEL=claude-haiku-4-20250205

# Feishu Bot (optional)
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx

# Database (default is fine for most users)
DATABASE_URL=sqlite:///data/database.db
```

## Quick Start

### 1. Initialize the database

```bash
pm init
```

### 2. Add your first records

With v2.0, you don't need to specify the domain - AI will figure it out:

```bash
# AI automatically recognizes this as a finance record
pm add "今天花了50块买午饭"

# AI automatically recognizes this as a work record
pm add "今天工作8小时，完成了用户认证模块"

# Query your data
pm query "本周花了多少钱"
pm query "最近一周的工作时长"

# Multi-turn conversation
pm chat "我今天花了50块"
pm chat "那是买午饭的钱"
pm chat "再给我加10块钱的饮料"
```

### 3. Manage plugins

```bash
# List all available plugins
pm plugin list

# Hot-reload a plugin (after making changes)
pm plugin reload finance
```

### 4. Feishu Bot Integration (Optional)

If you want to use Feishu bot for easy data tracking:

```bash
pm serve
```

Then in Feishu, just send messages like:
- "今天花了50块买午饭"
- "今天工作8小时"
- "查询本周支出"

## Migration from v1.0

If you're upgrading from v1.0, see [MIGRATION.md](docs/MIGRATION.md) for detailed migration instructions.

**Key changes**:
- CLI commands: `pm finance add` → `pm add`
- AI automatically detects intent
- Only finance and work plugins included by default
- Old data (health, leisure, etc.) is preserved but not accessible

## Plugin Development

Create your own plugins easily! The plugin system makes it simple to add new functionality:

```python
from src.core.plugin.base import BasePlugin
from src.access.base import AccessRequest, AccessResponse

class MyPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "myplugin"

    @property
    def display_name(self) -> str:
        return "My Plugin"

    @property
    def description(self) -> str:
        return "What this plugin does (used by AI for routing)"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def execute(self, request, context, params):
        # Your plugin logic here
        return AccessResponse(success=True, message="Done!")
```

See [PLUGIN_GUIDE.md](docs/PLUGIN_GUIDE.md) for complete plugin development guide.

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Detailed architecture documentation
- [PLUGIN_GUIDE.md](docs/PLUGIN_GUIDE.md) - How to create plugins
- [MIGRATION.md](docs/MIGRATION.md) - Migrating from v1.0 to v2.0

## Development

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Code formatting
poetry run black src/

# Linting
poetry run ruff check src/

# Type checking
poetry run mypy src/
```

## Contributing

Contributions are welcome! The plugin architecture makes it easy to add new features:

1. Fork the repository
2. Create a new plugin in `src/core/plugins/yourplugin/`
3. Follow the plugin interface
4. Submit a pull request

Or contribute to the core:
- Improve routing accuracy
- Enhance AI prompts
- Add new features to existing plugins
- Improve documentation

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for CLI
- Powered by [OpenAI](https://openai.com/) or [Anthropic](https://www.anthropic.com/) AI
- Feishu integration via [lark-oapi](https://github.com/larksuite/oapi-sdk-python)
