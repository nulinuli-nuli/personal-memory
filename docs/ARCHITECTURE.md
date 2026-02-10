# Personal Memory 架构文档

## 四层架构概述

Personal Memory 采用了四层架构设计，实现了高度模块化和可扩展的插件系统。

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1: 接入层                           │
│  ┌──────────────┐  ┌──────────────────┐                     │
│  │ CLI Adapter  │  │ Feishu Adapter   │                     │
│  │ (Typer)      │  │ (WebSocket)      │                     │
│  └──────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 2: 路由层                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ RouterService (AI驱动插件路由)                       │  │
│  │  - 理解用户输入                                       │  │
│  │  - 决定调用哪个插件                                   │  │
│  │  - 插件发现与加载                                     │  │
│  │  - 对话上下文管理 (数据库持久化)                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: 核心层 (插件架构)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Plugin Manager (插件管理器)                          │  │
│  │  - 插件发现与注册                                     │  │
│  │  - 插件生命周期管理 (加载/卸载/重载)                  │  │
│  │  - 插件间隔离                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                              ↓                               │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │ Finance Plugin   │  │ Work Plugin      │                  │
│  │ (财务)           │  │ (工作)           │                  │
│  └──────────────────┘  └──────────────────┘                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Common Services (共享服务)                           │    │
│  │  - AI Services (TextParser, IntentClassifier)       │    │
│  │  - Date Utils, Validators, Transformers             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 4: 存储层                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Repository│  │ Query    │  │ Context  │  │ Transaction│   │
│  │ Interface│  │ Builder  │  │ Store    │  │ Manager  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 各层详细说明

### Layer 1: 接入层 (Access Layer)

**职责**: 接收外部请求并转换为统一格式

**组件**:
- **BaseAdapter**: 适配器基类，定义统一接口
  - `process_request()`: 处理请求
  - `format_response()`: 格式化响应

- **CLI Adapter**: 命令行适配器
  - 使用 Typer 构建 CLI
  - 支持同步/异步转换
  - 提供 Rich 美化输出

- **Feishu Adapter**: 飞书机器人适配器
  - WebSocket 长连接
  - 消息格式转换
  - 事件处理

**数据模型**:
```python
@dataclass
class AccessRequest:
    user_id: str
    input_text: str
    channel: str  # "cli" | "feishu"
    context: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class AccessResponse:
    success: bool
    message: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    metadata: Dict[str, Any]
```

### Layer 2: 路由层 (Routing Layer)

**职责**: AI驱动的智能插件路由

**核心组件**:
- **RouterService**: 路由服务
  - 加载对话上下文
  - 使用 AI 理解用户意图
  - 决定调用哪个插件
  - 更新对话历史

- **PluginDiscovery**: 插件发现
  - 扫描插件目录
  - 动态加载插件

- **ContextRepository**: 上下文存储
  - 保存对话轮次
  - 维护上下文状态

**路由流程**:
1. 接收 `AccessRequest`
2. 加载用户对话上下文（最近3轮）
3. 调用 AI 分析用户输入
4. AI 返回路由决策（插件名、操作类型、参数）
5. 获取目标插件实例
6. 调用插件执行
7. 保存对话轮次到数据库
8. 返回 `AccessResponse`

### Layer 3: 核心层 (Core Layer)

**职责**: 插件化的业务逻辑处理

**插件系统**:
- **IPlugin**: 插件接口
  - `name`: 插件唯一标识
  - `display_name`: 显示名称
  - `description`: 功能描述（用于 AI 路由）
  - `version`: 版本号
  - `initialize()`: 初始化
  - `execute()`: 执行功能
  - `shutdown()`: 清理资源

- **BasePlugin**: 插件基类
  - 提供通用功能
  - 管理 repository 和 AI 实例

- **PluginManager**: 插件管理器
  - 插件发现与加载
  - 热重载支持
  - 生命周期管理

**内置插件**:
1. **Finance Plugin**: 财务管理
   - 添加收支记录
   - 查询财务数据
   - 生成统计报表

2. **Work Plugin**: 工作管理
   - 添加工作记录
   - 查询工作数据
   - 统计工作时长

**共享服务**:
- **AI Services**: 文本解析、意图识别
- **Date Utils**: 日期解析和格式化
- **Validators**: 数据验证

### Layer 4: 存储层 (Storage Layer)

**职责**: 数据持久化和查询

**组件**:
- **Repository Interface**: 仓储接口
  - CRUD 操作定义

- **BaseRepository**: 基础仓储实现
  - 通用 CRUD 逻辑
  - 类型安全

- **具体仓储**:
  - `FinanceRepository`: 财务数据
  - `WorkRepository`: 工作数据
  - `ContextRepository`: 对话上下文

- **Query Builder**: 查询构建器
  - 安全的 SQL 构建

- **SQL Safety**: SQL 安全验证
  - 防止注入攻击

**数据模型**:
- `User`: 用户
- `FinanceRecord`: 财务记录
- `WorkRecord`: 工作记录
- `ConversationContext`: 对话上下文
- `ConversationTurn`: 对话轮次

## 数据流

```
用户输入 "今天花了50块买午饭"
    ↓
CLI Adapter 创建 AccessRequest
    ↓
RouterService.route(request)
    ↓
ContextRepository.get_context(user_id)
    ↓
RouterService._decide_plugin(text, context)
    ↓
AI 分析 → {"plugin_name": "finance", "action": "add", ...}
    ↓
PluginManager.get_plugin("finance")
    ↓
FinancePlugin.execute(request, context, params)
    ↓
FinanceRepository.create(...)
    ↓
ContextRepository.add_turn(...)
    ↓
返回 AccessResponse
    ↓
CLI Adapter.format_response()
    ↓
用户看到: "已添加：午饭 ¥50.0 (支出)"
```

## 关键设计模式

1. **适配器模式**: 接入层统一不同通道
2. **策略模式**: 插件系统
3. **仓储模式**: 数据访问抽象
4. **工厂模式**: AI 提供者和插件创建
5. **依赖注入**: 插件通过构造函数注入依赖

## 扩展性

### 添加新插件

1. 创建插件目录: `src/core/plugins/myplugin/`
2. 实现 `IPlugin` 接口
3. 添加描述信息（用于 AI 路由）
4. 插件自动被发现和加载

### 添加新接入通道

1. 继承 `BaseAdapter`
2. 实现 `process_request()` 和 `format_response()`
3. 调用 `RouterService`

## 配置

配置文件: `src/shared/config.py`

```python
class Settings(BaseSettings):
    # AI Provider
    ai_provider: str = "openai"
    ai_api_key: str
    ai_base_url: Optional[str]
    ai_model: Optional[str]

    # Feishu Bot
    feishu_app_id: Optional[str]
    feishu_app_secret: Optional[str]

    # Database
    database_url: str = "sqlite:///data/database.db"

    # Application
    timezone: str = "Asia/Shanghai"
    debug: bool = False
```

## 性能考虑

- **插件热重载**: 无需重启应用
- **异步处理**: 提高并发能力
- **连接池**: 数据库连接复用
- **缓存**: AI 响应可缓存（未来）

## 安全

- **SQL 安全**: 参数化查询，SQL 注入防护
- **输入验证**: Pydantic schemas
- **错误处理**: 统一异常处理
