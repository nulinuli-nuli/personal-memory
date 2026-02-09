# 飞书机器人配置指南（SDK 长连接模式）

本文档详细说明如何配置飞书机器人与 Personal Memory 集成。

**重要更新**：现在使用飞书官方 SDK 的长连接模式，**无需配置公网地址**，本地开发环境即可直接使用！

## 功能概述

通过飞书机器人，你可以：

- 📝 **添加记录**：直接发送自然语言消息添加数据
  - "今天花了50块买午饭"
  - "昨晚睡了8小时"
  - "今天工作了4小时"

- 🔍 **智能查询**：自然语言查询数据
  - "查询本周花费"
  - "看看今天的工作记录"
  - "上个月在餐饮上花了多少钱"

- 📋 **快捷命令**：使用斜杠命令快速操作
  - `/daily` - 今日报告
  - `/weekly` - 本周报告
  - `/help` - 帮助信息

## 前置条件

1. 已安装 Personal Memory：`pip install personal-memory`
2. 已配置 AI Provider（OpenAI 或 Anthropic）
3. 拥有飞书账号（需要企业或组织账号）

## 第一步：创建飞书应用

### 1.1 访问飞书开放平台

打开浏览器，访问：https://open.feishu.cn/app

### 1.2 创建企业自建应用

1. 点击"创建企业自建应用"
2. 填写应用信息：
   - **应用名称**：Personal Memory（或自定义名称）
   - **应用描述**：个人数据追踪助手
   - **应用图标**：可上传自定义图标

3. 点击"创建"

### 1.3 获取凭证

创建成功后，进入应用详情页，找到并复制以下信息：

- **App ID**：格式如 `cli_xxxxxxxxxxxxx`
- **App Secret**：点击"查看"并复制

这些信息将在后续配置中使用。

## 第二步：配置应用权限

### 2.1 添加机器人能力

在应用详情页：

1. 左侧菜单选择"能力添加"
2. 找到并添加"机器人"能力
3. 确认添加

### 2.2 申请消息权限

1. 左侧菜单选择"权限管理"
2. 搜索并开通以下权限：
   - `im:message` - 发送消息
   - `im:message:send_as_bot` - 以机器人身份发送消息
3. 点击"申请权限"

### 2.3 配置事件订阅（使用长连接）

1. 左侧菜单选择"事件订阅"
2. **订阅方式选择**：**"使用长连接接收事件"**（重要！）
3. 订阅事件
   - 勾选 `im.message.receive_v1`（接收消息）
   - 点击"保存"

**注意**：选择长连接模式后，**不需要配置**：
- ❌ Request URL（请求地址）
- ❌ Verification Token（验证令牌）
- ❌ Encrypt Key（加密密钥）

## 第三步：配置环境变量

在你的项目目录创建 `.env` 文件：

```bash
# AI Provider 配置（必填）
AI_PROVIDER=openai  # 或 anthropic
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://api.openai.com/v1  # 可选
AI_MODEL=gpt-3.5-turbo  # 可选

# 数据库配置（可选，默认 sqlite:///data/database.db）
DATABASE_URL=sqlite:///data/database.db

# 飞书机器人配置（必填）
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=your_app_secret_here
```

**注意**：长连接模式**不需要**配置 `FEISHU_VERIFICATION_TOKEN` 和 `FEISHU_ENCRYPT_KEY`。

## 第四步：启动服务

### 4.1 安装依赖

确保已安装包含飞书 SDK 的依赖：

```bash
# 使用 Poetry
poetry install

# 或使用 pip
pip install -e .
```

### 4.2 初始化数据库

如果是首次使用，需要初始化数据库：

```bash
pm init
```

### 4.3 启动服务

直接运行 `pm serve` 命令：

```bash
pm serve
```

你将看到以下输出：

```
🚀 启动飞书机器人服务...
  App ID: cli_xxxxxxxxxxxxx
  Database: sqlite:///data/database.db

提示: 服务运行中，按 Ctrl+C 停止

✅ 飞书长连接已建立
📩 等待消息... (按 Ctrl+C 停止)
```

**就这么简单！** 无需配置 ngrok、无需公网地址、无需域名。

### 4.4 生产部署

对于生产环境，建议使用：

#### 使用进程管理器（推荐）

使用 `systemd`、`supervisor` 或 `pm2` 管理进程：

**systemd 示例** (`/etc/systemd/system/personal-memory.service`)：

```ini
[Unit]
Description=Personal Memory Feishu Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/personal-memory
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/pm serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable personal-memory
sudo systemctl start personal-memory
sudo systemctl status personal-memory
```

#### Docker 部署（推荐）

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

EXPOSE 8000

CMD ["pm", "serve"]
```

构建并运行：

```bash
docker build -t personal-memory .
docker run -d --name personal-memory --restart unless-stopped \
    --env-file .env \
    personal-memory
```

## 第五步：验证配置

### 5.1 检查服务状态

确保服务正在运行且显示：

```
✅ 飞书长连接已建立
```

### 5.2 在飞书中测试

1. 在飞书中找到你的机器人应用
2. 发送测试消息：
   - `hello` - 应该收到帮助信息
   - `今天花了50块买午饭` - 应该成功添加记录
   - `/daily` - 应该显示今日报告

## 长连接模式 vs Webhook 模式

| 特性 | Webhook 模式 | 长连接模式 |
|------|-------------|-----------|
| 公网地址 | ❌ 必须 | ✅ 不需要 |
| 本地开发 | ❌ 需要 ngrok | ✅ 直接运行 |
| 鉴权复杂度 | ⚠️ 需要解密/验签 | ✅ 仅建连时 |
| 稳定性 | ⚠️ 依赖网络 | ✅ 自动重连 |
| 配置难度 | ⚠️ 中等 | ✅ 简单 |
| 实时性 | ⚠️ 轮询延迟 | ✅ 实时推送 |

## 常见问题

### Q1: 长连接建立失败

**可能原因**：
- 飞书应用凭证错误
- 网络连接问题
- SDK 未安装

**解决方案**：
- 确认 `.env` 中的 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 正确
- 检查网络连接
- 运行 `poetry install` 确保安装了 `lark-oapi`

### Q2: 机器人无响应

**可能原因**：
- AI API 配置错误
- 数据库未初始化
- 权限未开通
- 事件订阅未开启

**解决方案**：
- 检查 `.env` 中的 AI 配置
- 运行 `pm init` 初始化数据库
- 确认飞书应用权限已开通（`im:message` 和 `im:message:send_as_bot`）
- 确认事件订阅已开启并选择了"使用长连接接收事件"

### Q3: AI 解析失败

**可能原因**：
- API Key 无效
- 网络问题
- API 限流

**解决方案**：
- 验证 AI API Key
- 检查网络连接
- 如使用代理，配置 `AI_BASE_URL`

### Q4: 如何在多个环境使用？

**方案**：创建多个飞书应用，每个环境一个：

```bash
# 开发环境
FEISHU_APP_ID=cli_dev_xxx
FEISHU_APP_SECRET=dev_secret

# 生产环境
FEISHU_APP_ID=cli_prod_xxx
FEISHU_APP_SECRET=prod_secret
```

### Q5: 服务断开怎么办？

长连接模式支持**自动重连**，无需手动干预。如果网络中断，SDK 会自动尝试重新建立连接。

## 安全建议

1. **保护凭证**：不要将 `.env` 文件提交到版本控制
2. **定期轮换**：定期更新 API Key 和 Secret
3. **最小权限**：只申请必要的权限
4. **日志审计**：定期检查服务日志

## 下一步

配置完成后，你可以：

- 查看 [README.md](README.md) 了解更多使用示例
- 发送 `/help` 查看完整命令列表
- 尝试自然语言查询："帮我查询上周工作记录"

## 技术支持

遇到问题？

- 检查日志：服务启动时会显示详细日志
- GitHub Issues：https://github.com/your-repo/issues
- 飞书开放平台文档：https://open.feishu.cn/document
- 飞书 SDK 文档：https://github.com/larksuite/oapi-sdk-python
