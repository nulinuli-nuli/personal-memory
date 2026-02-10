# 插件开发指南

本文档介绍如何为 Personal Memory 开发插件。

## 快速开始

### 1. 创建插件目录

```bash
mkdir src/core/plugins/myplugin
touch src/core/plugins/myplugin/__init__.py
touch src/core/plugins/myplugin/plugin.py
```

### 2. 实现插件接口

```python
from src.core.plugin.base import BasePlugin
from src.access.base import AccessRequest, AccessResponse
from typing import Dict, Any

class MyPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "myplugin"

    @property
    def display_name(self) -> str:
        return "我的插件"

    @property
    def description(self) -> str:
        return "插件功能描述，用于AI路由决策"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _create_repository(self):
        # 如果需要数据库，返回仓储实例
        # 否则返回 None
        return None

    async def execute(
        self,
        request: AccessRequest,
        context: Dict[str, Any],
        params: Dict[str, Any]
    ) -> AccessResponse:
        # 插件主要逻辑
        return AccessResponse(
            success=True,
            message="执行成功",
            data={},
            error=None,
            metadata={}
        )

    async def shutdown(self):
        # 清理资源
        pass
```

### 3. 注册插件

插件会自动被发现和加载，只需确保：
- 插件目录在 `src/core/plugins/` 下
- 包含 `plugin.py` 文件
- 实现了 `IPlugin` 接口

### 4. 更新 `__init__.py`

```python
from .plugin import MyPlugin

__all__ = ["MyPlugin"]
```

## 插件接口详解

### 必须实现的属性

#### name
插件的唯一标识符，用于路由和查找。

```python
@property
def name(self) -> str:
    return "weather"  # 小写，无空格
```

#### display_name
插件的显示名称，用于用户界面。

```python
@property
def display_name(self) -> str:
    return "天气查询"
```

#### description
插件功能描述，**非常重要**，AI 会根据这个描述决定是否调用你的插件。

```python
@property
def description(self) -> str:
    return "查询天气信息。支持查询当前天气、未来天气预报、历史天气数据等。"
```

**好的描述应该**:
- 清楚说明插件功能
- 列出主要操作类型
- 提供使用示例

#### version
插件版本号，建议使用语义化版本。

```python
@property
def version(self) -> str:
    return "1.0.0"
```

### 必须实现的方法

#### initialize()
插件初始化时调用，可以在这里设置资源。

```python
async def initialize(self, db_session, ai_provider):
    self.db = db_session
    self.ai = ai_provider
    self.repository = self._create_repository()

    # 自定义初始化逻辑
    self.api_client = MyAPIClient()
```

#### execute()
插件主要逻辑，处理用户请求。

```python
async def execute(
    self,
    request: AccessRequest,
    context: Dict[str, Any],
    params: Dict[str, Any]
) -> AccessResponse:
    """
    Args:
        request: 用户请求
            - request.user_id: 用户ID
            - request.input_text: 用户输入
            - request.channel: 通道 (cli/feishu)
            - request.context: 额外上下文
            - request.metadata: 元数据

        context: 对话上下文
            - 当前对话的状态和历史

        params: 路由层传递的参数
            - AI 预解析的参数（如果路由层已解析）
            - 可以减少插件的二次解析开销

    Returns:
        AccessResponse
    """
    try:
        # 1. 如果路由层没有预解析，使用 AI 解析
        if "parsed_data" not in params:
            parsed = await self._parse_with_ai(request.input_text)
        else:
            parsed = params["parsed_data"]

        # 2. 根据操作类型分发
        action = parsed.get("action", "default")

        if action == "add":
            return await self._add_record(request, parsed)
        elif action == "query":
            return await self._query_records(request, parsed)
        else:
            return AccessResponse(
                success=False,
                error=f"不支持的操作: {action}",
                message="",
                data=None,
                metadata={}
            )

    except Exception as e:
        return AccessResponse(
            success=False,
            error=f"操作失败: {str(e)}",
            message="",
            data=None,
            metadata={}
        )
```

#### shutdown()
插件卸载时调用，清理资源。

```python
async def shutdown(self):
    # 关闭网络连接
    if hasattr(self, 'api_client'):
        self.api_client.close()

    # 保存状态
    if hasattr(self, 'state'):
        self._save_state(self.state)
```

### 可选方法

#### _create_repository()
如果插件需要数据库访问，创建并返回 repository。

```python
def _create_repository(self):
    from src.storage.repositories.base import BaseRepository
    from src.shared.models import Base

    class MyRepository(BaseRepository):
        pass

    return MyRepository(self.db)
```

## 使用 AI 解析

如果插件需要从用户输入中提取结构化数据：

```python
async def _parse_with_ai(self, text: str) -> Dict:
    """使用 AI 解析用户输入"""
    from pathlib import Path

    # 加载提示词模板
    prompt_template = Path("prompts/parse_myplugin.txt").read_text(encoding="utf-8")
    prompt = prompt_template.format(text=text)

    # 调用 AI
    return await self.ai.parse(prompt, context={})
```

提示词模板示例 (`prompts/parse_myplugin.txt`):

```
解析用户的天气查询输入，返回 JSON 格式：

用户输入：{text}

返回格式：
{{
    "action": "query" | "forecast",
    "location": "城市名称",
    "date": "YYYY-MM-DD" | null,
    "query_type": "current" | "forecast" | "historical"
}}
```

## 数据库访问

如果插件需要持久化数据：

### 1. 定义数据模型

在 `src/shared/models.py` 添加：

```python
class MyRecord(Base):
    """我的记录模型"""
    __tablename__ = "my_records"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    data = Column(JSON)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
```

### 2. 创建 Repository

在 `src/storage/repositories/myrepo_repo.py`:

```python
from src.storage.repositories.base import BaseRepository
from src.shared.models import MyRecord

class MyRepository(BaseRepository[MyRecord]):
    def __init__(self, db: Session):
        super().__init__(MyRecord, db)

    def custom_query(self, user_id: int):
        return self.db.query(MyRecord).filter(
            MyRecord.user_id == user_id
        ).all()
```

### 3. 在插件中使用

```python
def _create_repository(self):
    from src.storage.repositories.myrepo_repo import MyRepository
    return MyRepository(self.db)

async def _add_record(self, request, parsed):
    record = self.repository.create(
        user_id=int(request.user_id),
        data=parsed
    )
    return AccessResponse(
        success=True,
        data={"id": record.id},
        message="添加成功"
    )
```

## 错误处理

始终返回 `AccessResponse`，即使出错：

```python
try:
    # 业务逻辑
    result = self._do_something()
    return AccessResponse(
        success=True,
        message="操作成功",
        data=result,
        error=None
    )
except ValueError as e:
    return AccessResponse(
        success=False,
        error=f"参数错误: {e}",
        message="",
        data=None
    )
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return AccessResponse(
        success=False,
        error=f"操作失败: {str(e)}",
        message="",
        data=None
    )
```

## 测试插件

### 单元测试

```python
import pytest
from unittest.mock import Mock
from src.core.plugins.myplugin.plugin import MyPlugin
from src.access.base import AccessRequest

@pytest.fixture
def my_plugin():
    plugin = MyPlugin()
    plugin.db = Mock()
    plugin.ai = Mock()
    return plugin

@pytest.mark.asyncio
async def test_plugin_properties(my_plugin):
    assert my_plugin.name == "myplugin"
    assert my_plugin.display_name == "我的插件"

@pytest.mark.asyncio
async def test_execute(my_plugin):
    request = AccessRequest(
        user_id="1",
        input_text="测试",
        channel="cli",
        context={},
        metadata={}
    )

    response = await my_plugin.execute(request, {}, {})
    assert response.success == True
```

### 手动测试

```bash
# 初始化数据库
pm init

# 列出插件（应该包含你的插件）
pm plugin list

# 测试插件
pm add "测试我的插件功能"

# 重载插件（修改代码后）
pm plugin reload myplugin
```

## 最佳实践

### 1. 插件独立性
- 插件间不直接依赖
- 通过接口通信
- 共享代码放在 `src/core/common/`

### 2. 描述清晰
- `description` 属性用于 AI 路由决策
- 清楚说明插件功能和适用场景
- 提供使用示例

### 3. 参数验证
- 在 `execute` 开始处验证参数
- 使用 Pydantic schemas 验证
- 提供友好的错误信息

### 4. 使用 AI
- 复杂参数使用 AI 解析
- 减少用户记忆负担
- 提供灵活的输入方式

### 5. 日志记录
- 使用 Python logging
- 记录关键操作
- 便于调试

### 6. 资源管理
- 在 `shutdown` 中清理资源
- 使用上下文管理器
- 避免内存泄漏

## 示例插件

参考现有实现：
- `src/core/plugins/finance/`: 财务管理插件
- `src/core/plugins/work/`: 工作管理插件

## 常见问题

### Q: 插件没有被加载？
A: 检查：
1. 插件目录是否在 `src/core/plugins/` 下
2. 是否包含 `plugin.py` 文件
3. 是否实现了 `IPlugin` 接口
4. 查看 `pm plugin list` 输出

### Q: AI 总是路由到错误的插件？
A: 优化 `description` 属性：
1. 更具体地描述功能
2. 明确适用场景
3. 添加关键词

### Q: 如何调试插件？
A:
1. 使用日志: `logger.debug()`
2. 手动测试: `pm add "测试"`
3. 单元测试: `pytest tests/`

### Q: 插件可以调用其他插件吗？
A: 不建议。插件应该独立。如果有共享需求：
1. 将共享代码放到 `src/core/common/`
2. 创建共享服务
3. 通过依赖注入传递
