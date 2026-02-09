# Personal Memory System

A lightweight personal data recording and management platform powered by AI natural language processing.

## Features

- 📝 **Natural Language Input**: Just describe what happened in plain language
- 🤖 **AI-Powered Parsing**: Automatically structures your data using AI
- 💰 **Finance Tracking**: Track income and expenses with automatic categorization
- 😴 **Health Monitoring**: Record sleep, mood, and wellness metrics
- 💼 **Work Logging**: Track tasks, hours, and achievements
- 🎮 **Leisure Activities**: Log free time activities and enjoyment levels
- 📚 **Learning Records**: Track study activities, reading progress, and skill development
- 🎯 **Goal Management**: Set goals and track progress with milestones
- 👥 **Social Activities**: Record social interactions, gatherings, and relationships
- 📊 **Reports**: Generate daily, weekly, and monthly summaries
- 🤖 **Feishu Bot Integration**: Add and query data via Feishu with natural language

## Installation

```bash
# Install in editable mode
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"

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

# Database (default is fine for most users)
DATABASE_URL=sqlite:///data/database.db
```

## Quick Start

### 1. Initialize the database

```bash
pm init
```

### 2. Start the bot service (optional)

If you want to use Feishu bot for easy data tracking:

```bash
pm serve
```

### 3. Add your first records

```bash
# Finance
pm finance add "今天花了50块买午饭"

# Health
pm health add "昨晚睡了8小时，睡得很好"

# Work
pm work add "今天工作8小时，完成了用户认证模块"

# Leisure
pm leisure add "看了2小时电影"

# Learning
pm learning add "读了2小时《深度工作》，完成了第一章"

# Goal
pm goal add "今年要读12本书"
pm goal progress 1 1  # Update goal ID 1 with +1 progress

# Social
pm social add "和朋友聚餐，花了200块，很愉快"
```

### 3. View reports

```bash
pm report daily
pm report weekly
pm report monthly
```

## Commands

### Finance Commands

```bash
# Add a finance record
pm finance add "今天花了50块买午饭"

# List recent records
pm finance list --days 7

# Show statistics by category
pm finance stats
```

### Health Commands

```bash
# Add a health record
pm health add "昨晚睡了8小时，睡得很好"

# List recent records
pm health list --days 7
```

### Work Commands

```bash
# Add a work record
pm work add "今天工作8小时，完成了用户认证模块"

# List recent records
pm work list --days 7

# Show summary
pm work summary --days 30
```

### Leisure Commands

```bash
# Add a leisure record
pm leisure add "看了2小时电影"

# List recent records
pm leisure list --days 7
```

### Learning Commands

```bash
# Add a learning record
pm learning add "读了2小时《深度工作》，完成了第一章"

# List recent records
pm learning list --days 7

# Show statistics by type
pm learning stats --days 30
```

### Goal Commands

```bash
# Add a goal
pm goal add "今年要读12本书"

# List all goals
pm goal list

# List active goals only
pm goal list --status active

# Update goal progress
pm goal progress 1 1                    # Add +1 to goal ID 1

# Show goal statistics
pm goal stats
```

### Social Commands

```bash
# Add a social record
pm social add "和朋友聚餐，花了200块，很愉快"

# List recent records
pm social list --days 7

# Show statistics
pm social stats --days 30
```

### Report Commands

```bash
# Daily report
pm report daily

# Weekly report
pm report weekly

# Monthly report
pm report monthly

# Report for a specific date
pm report daily 2025-01-15
```

## Feishu Bot Integration

Personal Memory now supports Feishu bot integration for easy data tracking through chat!

**New**: Uses SDK long-connection mode - no public URL required!

### Quick Setup

1. **Configure Environment Variables**:

```bash
# Add to your .env file
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=your_app_secret_here
```

2. **Start the Bot Service**:

```bash
pm serve
```

3. **Configure Feishu Bot**:

- Go to [Feishu Open Platform](https://open.feishu.cn/app)
- Create a new app or use existing one
- Enable "使用长连接接收事件" (Use long-connection mode)
- Subscribe to `im.message.receive_v1` event

**That's it!** No need for webhooks, ngrok, or public URLs.

For detailed setup instructions, see [FEISHU_SETUP.md](FEISHU_SETUP.md) or [FEISHU_QUICKSTART.md](FEISHU_QUICKSTART.md).

### Usage Examples

Once configured, you can interact with the bot directly in Feishu:

#### Adding Records

```
📝 Add finance record:
"今天花了50块买午饭"
✓ Response: ✅ 已添加：💸 午饭 ¥50.00

📝 Add health record:
"昨晚睡了8小时，睡得很好"
✓ Response: ✅ 已添加：😴 睡眠 8h - 很好

📝 Add work record:
"今天工作了4小时，完成开发任务"
✓ Response: ✅ 已添加：💼 完成开发任务 (4h)

📝 Add leisure record:
"看了2小时电影"
✓ Response: ✅ 已添加：🎮 电影 (2h)

📝 Add learning record:
"读了2小时《深度工作》"
✓ Response: ✅ 已添加：📚 《深度工作》 (2h)

📝 Add social record:
"和朋友聚餐，花了200块，很愉快"
✓ Response: ✅ 已添加：👥 朋友-聚餐 (¥200, ⭐5)

📝 Add goal:
"今年要读12本书"
✓ Response: ✅ 已添加：🎯 读书目标 (12本)

📝 Update goal progress:
"目标进度 +1"
✓ Response: ✅ 已更新：📈 目标进度 1/12 (8.3%)
```

#### Smart Query (Natural Language)

```
🔍 Query expenses:
"查询本周花费"
📊 Response:
💸 财务统计 (2025-01-13 至 2025-01-19)
支出: ¥500.00
收入: ¥2000.00
结余: ¥1500.00

🔍 Query work records:
"看看今天的工作记录"
📊 Response:
💼 工作记录
📅 2025-01-19 | ⏱ 4h | 完成开发任务
总计: 4h

🔍 Complex query:
"上个月在餐饮上花了多少钱"
📊 Response: 📊 上个月餐饮支出：¥1,234.56

🔍 Query learning records:
"最近学了什么"
📊 Response: 📚 学习记录 (最近7天)
- 《深度工作》 - 2h

🔍 Query social activities:
"最近有哪些社交活动"
📊 Response: 👥 社交记录 (最近7天)
总计时长: 5h | 总花费: ¥300

🔍 Query goals:
"我的目标进度怎么样"
📊 Response: 🎯 目标概览
活跃目标: 3个 | 已完成: 1个
```

#### Quick Commands

```
/help    - Show help message
/daily   - Daily report
/weekly  - Weekly report
/monthly - Monthly report
/list    - Recent records
```

### Key Features

- 🤖 **Smart Intent Recognition**: Automatically detects if you're adding a record or querying data
- 💬 **Pure Natural Language**: No need for specific commands - just talk naturally
- 🎯 **Keyword Detection**: Recognizes query intents from context ("查询", "看看", "多少", etc.)
- 🔍 **Flexible Queries**: Ask questions in your own words
- 📱 **Multi-user Support**: Each user gets their own data space
- 📚 **All Record Types**: Support for finance, health, work, leisure, learning, social, and goals

## Natural Language Examples

### Finance

- "今天花了50块买午饭"
- "地铁8块钱"
- "发了10000块工资"
- "超市买菜花了200元"

### Health

- "昨晚睡了8小时，睡得很好"
- "11点睡，7点起，睡眠质量一般"
- "今天心情不错"
- "睡了6个小时，很差"

### Work

- "今天工作8小时，完成了用户认证模块"
- "开了2个小时会，讨论了产品方案"
- "修复了3个bug"
- "写了文档，大概3小时"

### Leisure

- "看了2小时电影"
- "和朋友打了3小时桌球，很开心"
- "逛了1小时公园"
- "玩了一下午游戏"

### Learning

- "读了2小时《深度工作》，完成了第一章"
- "学Python编程，3小时，完成了基础语法"
- "看在线课程，学会了递归算法"
- "背单词1小时，记住了50个"

### Goal

- "今年要读12本书"
- "目标：每月跑步50公里"
- "计划今年存5万块钱"
- "要在三个月内学会弹吉他"

### Social

- "和朋友聚餐，花了200块，很愉快"
- "和同事打了2小时桌球"
- "和家人视频聊天1小时"
- "参加了同学聚会，见到了10个老同学"

## AI Provider Support

The system supports multiple AI providers:

### OpenAI (Default)

```bash
AI_PROVIDER=openai
AI_API_KEY=sk-your-key
AI_MODEL=gpt-4o-mini
```

### Anthropic Claude

```bash
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-your-key
AI_MODEL=claude-haiku-4-20250205
```

### Custom/Proxy Services

You can use custom base URLs for proxy or relay services:

```bash
AI_PROVIDER=openai
AI_API_KEY=your-custom-key
AI_BASE_URL=https://your-proxy.com/v1
AI_MODEL=gpt-4o-mini
```

## Project Structure

```
personal-memory/
├── src/
│   ├── main.py              # CLI entry point
│   ├── config.py            # Configuration management
│   ├── core/
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── database.py      # Database connection
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── categories.py    # Category definitions
│   ├── services/
│   │   ├── record_service.py # Business logic
│   │   └── query_service.py  # Query service
│   ├── repositories/        # Data access layer
│   │   ├── base.py          # Base repository
│   │   ├── finance_repo.py  # Finance repository
│   │   ├── health_repo.py   # Health repository
│   │   ├── work_repo.py     # Work repository
│   │   ├── leisure_repo.py  # Leisure repository
│   │   ├── learning_repo.py # Learning repository
│   │   ├── social_repo.py   # Social repository
│   │   ├── goal_repo.py     # Goal repository
│   │   └── user_repo.py     # User repository
│   ├── cli/                 # CLI commands
│   ├── ai/
│   │   ├── parser.py        # Text parser
│   │   └── providers.py     # AI provider abstraction
│   └── feishu/              # Feishu bot integration
│       ├── client.py        # WebSocket client
│       ├── event_handler.py # Event handler
│       └── handlers.py      # Message handlers
├── prompts/                 # AI prompt templates
├── data/                    # Database storage
└── tests/                   # Tests
```

## System Commands

```bash
# Initialize database
pm init

# Reset database (WARNING: deletes all data)
pm reset

# Show version
pm version

# Start Feishu bot service
pm serve
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
ruff check src/
```

### Type Checking

```bash
mypy src/
```

## License

MIT License - feel free to use this project for personal use.
