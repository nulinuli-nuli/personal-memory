# Personal Memory System

A lightweight personal data recording and management platform powered by AI natural language processing.

## Features

- 📝 **Natural Language Input**: Just describe what happened in plain language
- 🤖 **AI-Powered Parsing**: Automatically structures your data using AI
- 💰 **Finance Tracking**: Track income and expenses with automatic categorization
- 😴 **Health Monitoring**: Record sleep, mood, and wellness metrics
- 💼 **Work Logging**: Track tasks, hours, and achievements
- 🎮 **Leisure Activities**: Log free time activities and enjoyment levels
- 📊 **Reports**: Generate daily, weekly, and monthly summaries
- 📈 **Chart Visualization**: Generate interactive charts with natural language
- 🤖 **Feishu Bot Integration**: Add and query data via Feishu with natural language

## Installation

### Using Poetry (Recommended)

```bash
# Install dependencies
poetry install

# Create .env file from example
cp .env.example .env

# Edit .env with your configuration
# Important: Set AI_PROVIDER and AI_API_KEY
```

### Using pip

```bash
pip install -e .
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

### 2. Add your first records

```bash
# Finance
pm finance add "今天花了50块买午饭"

# Health
pm health add "昨晚睡了8小时，睡得很好"

# Work
pm work add "今天工作8小时，完成了用户认证模块"

# Leisure
pm leisure add "看了2小时电影"
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

### Chart Commands 📈

Generate beautiful charts with natural language descriptions:

```bash
# View chart examples
pm chart examples

# Generate a pie chart for expense categories
pm chart generate "画一个饼图显示最近30天的支出分类占比"

# Generate a bar chart comparing income and expenses
pm chart generate "用柱状图比较最近3个月的收入和支出"

# Generate a line chart for daily spending trend
pm chart generate "显示本周每天的消费趋势折线图"

# Group expenses by category
pm chart generate "最近7天支出按分类统计"

# Output options
pm chart generate "支出饼图" --format window   # Popup window (default)
pm chart generate "支出饼图" --format html     # Open in browser
pm chart generate "支出饼图" --format png      # Export as image
pm chart generate "支出统计" -o custom_name    # Custom filename
```

**Supported Chart Types:**
- 🥧 **Pie Chart** - Category distribution/percentages
- 📊 **Bar Chart** - Comparisons, rankings
- 📈 **Line Chart** - Trends over time
- 📉 **Area Chart** - Cumulative trends
- 📊 **Stacked Bar** - Grouped comparisons

**Features:**
- Natural language chart description
- Auto-detection of time ranges (today, this week, this month, last X days, etc.)
- Flexible filtering by category, type, payment method
- Display in popup window or browser
- Export to PNG image

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
│   │   └── exceptions.py    # Custom exceptions
│   ├── services/
│   │   └── record_service.py # Business logic
│   ├── repositories/        # Data access layer
│   ├── cli/                 # CLI commands
│   ├── ai/
│   │   ├── parser.py        # Text parser
│   │   └── providers.py     # AI provider abstraction
│   ├── chart/               # Chart generation module
│   │   └── generator.py     # Plotly/Matplotlib chart generator
│   └── utils/               # Utilities
├── prompts/                 # AI prompt templates
├── data/                    # Database storage
└── tests/                   # Tests
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black src/
poetry run ruff check src/
```

## License

MIT License - feel free to use this project for personal use.
