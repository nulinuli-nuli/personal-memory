# 测试说明

## 安装测试依赖

```bash
pip install pytest pytest-asyncio
```

或使用 Poetry:
```bash
poetry install --with dev
```

## 运行测试

### 运行所有测试
```bash
pytest tests/ -s
```

**注意**: 由于 pytest-asyncio 与 pytest 输出捕获系统的已知兼容性问题，运行测试时需要使用 `-s` 标志禁用输出捕获。所有测试都通过了验证。

### 运行特定层测试
```bash
# 核心层测试
pytest tests/core/ -s

# 插件测试
pytest tests/core/plugins/ -s

# 路由层测试
pytest tests/routing/ -s

# 存储层测试
pytest tests/storage/ -s

# 集成测试
pytest tests/integration/ -s
```

### 运行特定测试文件
```bash
pytest tests/core/plugins/test_finance_plugin.py -v
pytest tests/core/plugins/test_work_plugin.py -v
pytest tests/routing/test_router.py -v
```

### 生成覆盖率报告
```bash
pytest --cov=src --cov-report=html
```

### 查看测试输出详情
```bash
pytest -v --tb=short
```

## 测试覆盖范围

### 插件测试 (tests/core/plugins/)
- ✅ `test_finance_plugin.py` - 财务插件测试
  - 插件属性验证
  - 添加记录成功/失败场景
  - 查询记录
  - AI 解析
  - 参数验证

- ✅ `test_work_plugin.py` - 工作插件测试
  - 插件属性验证
  - 添加工作记录
  - 缺少任务名称
  - 无效时长验证
  - 查询工作记录

### 路由层测试 (tests/routing/)
- ✅ `test_router.py` - 路由服务测试
  - AI 路由决策
  - 插件调用
  - 路由失败处理
  - 插件未找到处理
  - 上下文格式化

### 核心层测试 (tests/core/)
- ✅ `test_plugin_manager.py` - 插件管理器测试
  - 插件发现
  - 插件加载
  - 插件列表
  - 获取插件

### 存储层测试 (tests/storage/)
- ✅ `test_context_repository.py` - 上下文仓储测试
  - 获取上下文
  - 创建/更新上下文
  - 添加对话轮次
  - 获取最近对话

### 集成测试 (tests/integration/)
- ✅ `test_cli_e2e.py` - CLI 端到端测试
  - 添加命令测试
  - 查询命令测试
  - 聊天命令测试
  - 插件列表测试
  - 初始化命令测试

## 测试最佳实践

1. **运行测试前确保数据库已初始化**:
   ```bash
   python -m src.main init
   ```

2. **使用 mock 避免真实 AI 调用**:
   - 所有测试都使用 mock，不会消耗 API 配额
   - 测试快速且可靠

3. **隔离测试环境**:
   - 每个测试使用独立的 fixture
   - 测试之间互不干扰

4. **覆盖率目标**:
   - 单元测试覆盖率 > 80%
   - 关键路径 100% 覆盖

## 快速验证

验证测试环境是否正确配置：
```bash
# 检查 pytest 版本
pytest --version

# 运行单个测试文件验证
pytest tests/core/plugins/test_finance_plugin.py::test_plugin_properties -v

# 查看可用测试
pytest --collect-only
```
