# 从 v1.0 迁移到 v2.0

本文档帮助你从 Personal Memory v1.0 迁移到 v2.0（四层插件架构）。

## 主要变化

### 1. 架构重构
- **v1.0**: 三层架构（CLI → Service → Repository）
- **v2.0**: 四层架构（Access → Routing → Core(Plugin) → Storage）

### 2. 插件系统
- **v1.0**: 硬编码的领域处理
- **v2.0**: 可热插拔的插件系统

### 3. 智能路由
- **v1.0**: 手动指定命令 (`pm finance add`, `pm work add`)
- **v2.0**: AI 自动路由 (`pm add "今天花了50块"`)

### 4. 对话上下文
- **v1.0**: 无状态，每次调用独立
- **v2.0**: 有状态，支持多轮对话

### 5. 插件精简
- **v1.0**: 7个领域 (finance, health, work, leisure, learning, social, goal)
- **v2.0**: 2个插件 (finance, work) - 其他已移除

## 数据库变化

### 新增表

#### conversation_turns
```sql
CREATE TABLE conversation_turns (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    timestamp DATETIME,
    user_input TEXT,
    intent VARCHAR(50),
    domain VARCHAR(50),
    response TEXT,
    metadata JSON
);
```

#### conversation_contexts
```sql
CREATE TABLE conversation_contexts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE,
    current_intent VARCHAR(50),
    current_domain VARCHAR(50),
    state JSON,
    updated_at DATETIME
);
```

### 迁移步骤

```bash
# 1. 备份现有数据库
cp data/database.db data/database.db.backup

# 2. 初始化新架构（会自动创建新表）
pm init

# 3. 旧表仍然保留，数据不会丢失
# 如果需要清理旧表，可以手动执行：
# pm reset  # ⚠️ 警告：会删除所有数据
```

## CLI 命令变化

### 添加记录

#### v1.0
```bash
pm finance add "今天花了50块买午饭"
pm work add "今天工作8小时"
pm health add "昨晚睡了8小时"
```

#### v2.0
```bash
# AI 自动识别类型
pm add "今天花了50块买午饭"
pm add "今天工作8小时"

# 明确查询意图
pm query "本周花了多少钱"
pm query "最近一周的工作时长"

# 多轮对话
pm chat "我今天花了50块"
pm chat "那是买午饭的钱"
```

### 插件管理（新增）

```bash
# 列出所有插件
pm plugin list

# 热重载插件
pm plugin reload finance
pm plugin reload work
```

### 移除的命令

以下命令已被移除：
- `pm health ...`
- `pm leisure ...`
- `pm learning ...`
- `pm social ...`
- `pm goal ...`
- `pm report ...`

## API 变化

### Python API

#### v1.0
```python
from src.services.record_service import RecordService
from src.core.database import get_db

db = next(get_db())
service = RecordService(db)
await service.add_finance_from_text("今天花了50块")
```

#### v2.0
```python
from src.access.cli.adapter import CLIAdapter

adapter = CLIAdapter()
await adapter.initialize_plugins()
result = adapter.sync_process("1", "今天花了50块")
print(result)  # "已添加：午饭 ¥50.0 (支出)"
```

### 自定义集成

#### v1.0
```python
from src.cli.finance import finance_app
finance_app()
```

#### v2.0
```python
from src.access.cli.adapter import CLIAdapter
from src.access.base import AccessRequest

adapter = CLIAdapter()
await adapter.initialize_plugins()

request = AccessRequest(
    user_id="1",
    input_text="今天花了50块",
    channel="api",  # 自定义通道
    context={},
    metadata={}
)
response = await adapter.process_request(request)
```

## 配置变化

配置文件位置和格式保持不变，但有以下变化：

### 新增配置项

v2.0 支持（未来）：
- 插件相关配置
- 上下文保留策略
- 路由决策阈值

### 环境变量

保持不变：
```bash
# AI Provider
AI_PROVIDER=openai
AI_API_KEY=sk-xxx
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

# Feishu Bot
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx

# Database
DATABASE_URL=sqlite:///data/database.db
```

## 代码迁移

### 如果你有自定义代码

#### 1. 导入路径更新

```python
# v1.0
from src.core.models import FinanceRecord
from src.core.database import get_db
from src.config import settings

# v2.0
from src.shared.models import FinanceRecord
from src.shared.database import get_db
from src.shared.config import settings
```

#### 2. 服务层更新

```python
# v1.0
from src.services.record_service import RecordService

# v2.0 - 使用适配器
from src.access.cli.adapter import CLIAdapter
```

#### 3. AI 解析更新

```python
# v1.0
from src.ai.parser import TextParser

parser = TextParser()
result = parser.parse_finance("今天花了50块")

# v2.0 - 使用插件
from src.core.plugins.finance.plugin import FinancePlugin

plugin = FinancePlugin()
await plugin.initialize(db, ai)
response = await plugin.execute(request, context, {})
```

## 数据兼容性

### 保留的表
- ✅ `users`
- ✅ `finance_records`
- ✅ `work_records`

### 移除的表（数据保留但不再使用）
- ❌ `health_records`
- ❌ `leisure_records`
- ❌ `learning_records`
- ❌ `social_records`
- ❌ `goals`
- ❌ `goal_progress`
- ❌ `time_logs`

**注意**: 这些表的数据仍然在数据库中，但新版本不会访问它们。

## 功能对比

| 功能 | v1.0 | v2.0 |
|------|------|------|
| 财务管理 | ✅ | ✅ (插件) |
| 工作管理 | ✅ | ✅ (插件) |
| 健康管理 | ✅ | ❌ |
| 休闲记录 | ✅ | ❌ |
| 学习记录 | ✅ | ❌ |
| 社交记录 | ✅ | ❌ |
| 目标管理 | ✅ | ❌ |
| 智能路由 | ❌ | ✅ |
| 多轮对话 | ❌ | ✅ |
| 插件热重载 | ❌ | ✅ |
| CLI 命令 | `pm <domain> <action>` | `pm <add/query/chat>` |

## 迁移检查清单

### 准备阶段
- [ ] 阅读本文档
- [ ] 备份数据库
- [ ] 备份配置文件 `.env`

### 执行阶段
- [ ] 更新代码: `git pull` 或安装新版本
- [ ] 安装依赖: `poetry install` 或 `pip install -e .`
- [ ] 初始化数据库: `pm init`
- [ ] 测试基本功能: `pm add "测试"`

### 验证阶段
- [ ] 测试财务记录: `pm add "今天花了50块"`
- [ ] 测试工作记录: `pm add "今天工作8小时"`
- [ ] 测试查询: `pm query "本周支出"`
- [ ] 测试多轮对话: `pm chat "我今天花了50块"`
- [ ] 测试插件列表: `pm plugin list`

### 清理阶段（可选）
- [ ] 如果不需要旧数据，运行 `pm reset`
- [ ] 从 .env 移除旧配置（如果有的话）

## 回滚计划

如果需要回滚到 v1.0：

### 1. 恢复数据库
```bash
cp data/database.db.backup data/database.db
```

### 2. 恢复代码
```bash
git checkout <v1.0-tag>
```

### 3. 恢复依赖
```bash
poetry install
```

### 4. 验证
```bash
pm finance add "测试"
pm work add "测试"
```

## 常见问题

### Q: 我的数据会丢失吗？
A: 不会。finance_records 和 work_records 表仍然保留，只是访问方式变了。

### Q: 健康等其他领域的记录怎么办？
A: v2.0 暂时只保留 finance 和 work 插件。你可以：
1. 继续使用 v1.0
2. 自己开发相应的插件（参考 PLUGIN_GUIDE.md）

### Q: 如何迁移健康记录数据？
A: 数据仍在 `health_records` 表中。如果需要：
1. 导出数据: `sqlite3 data/database.db ".dump health_records"`
2. 开发健康插件
3. 导入数据

### Q: AI 路由不准确怎么办？
A:
1. 优化插件描述（修改 `description` 属性）
2. 提供更明确的输入
3. 使用 `pm query` 明确查询意图

### Q: 多轮对话怎么用？
A:
```bash
pm chat "我今天花了50块"
# AI: 已记录支出 50 元
pm chat "那是买午饭的钱"
# AI: 理解上下文，更新记录描述
```

### Q: 可以同时使用 v1.0 和 v2.0 吗？
A: 不建议。它们使用相同的数据库，但架构不同。建议选择一个版本。

## 获取帮助

- 📖 架构文档: [ARCHITECTURE.md](ARCHITECTURE.md)
- 🔌 插件开发: [PLUGIN_GUIDE.md](PLUGIN_GUIDE.md)
- 🐛 问题反馈: GitHub Issues
- 💬 讨论: GitHub Discussions

## 总结

v2.0 是一个重大的架构升级：
- ✅ 更灵活的插件系统
- ✅ 更智能的 AI 路由
- ✅ 更好的对话体验
- ✅ 更容易扩展

迁移过程简单，主要变化在 CLI 命令和 API 使用方式。数据不会丢失，可以放心升级。
