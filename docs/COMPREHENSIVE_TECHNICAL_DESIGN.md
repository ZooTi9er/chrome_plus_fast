# Chrome Plus V2.0 完整技术设计开发文档

## 📋 文档信息

| 项目名称 | Chrome Plus V2.0 |
|---------|------------------|
| 版本 | 2.0.0 |
| 文档类型 | 完整技术设计开发文档 |
| 目标受众 | 开发人员、架构师、技术负责人 |
| 最后更新 | 2024-12 |

## 📖 目录

1. [项目概述和架构设计](#1-项目概述和架构设计)
2. [核心功能模块分析](#2-核心功能模块分析)
3. [代码结构和组件说明](#3-代码结构和组件说明)
4. [API接口文档](#4-api接口文档)
5. [开发指南和最佳实践](#5-开发指南和最佳实践)
6. [部署和配置说明](#6-部署和配置说明)

---

## 1. 项目概述和架构设计

### 1.1 项目概述

Chrome Plus V2.0是一款现代化的智能AI助手Chrome扩展，采用微服务架构设计，支持WebSocket实时通信、异步任务处理和容器化部署。项目从传统的HTTP同步模式升级为实时通信和分布式处理模式。

#### 核心特性
- **🚀 WebSocket实时通信**: 双向实时消息传输，告别HTTP轮询
- **🔄 异步任务处理**: Celery分布式任务队列，支持长时间AI处理
- **🏗️ 微服务架构**: Redis消息队列 + FastAPI网关 + Celery Worker
- **🐳 容器化部署**: Docker Compose一键启动所有服务
- **🤖 多模型支持**: DeepSeek、OpenAI等多种AI模型
- **🌍 代理功能**: 支持HTTP/SOCKS5代理，解决地理限制

### 1.2 技术栈

#### 前端技术栈
- **Chrome Extension API**: Manifest V3标准
- **JavaScript ES6+**: 现代语法，支持异步处理
- **WebSocket Client**: 实时通信客户端
- **CSS3**: 响应式设计
- **marked.js**: Markdown渲染
- **highlight.js**: 代码语法高亮

#### 后端技术栈
- **FastAPI**: 现代Python Web框架，支持WebSocket
- **Celery**: 分布式任务队列
- **Redis**: 消息代理和结果存储
- **uvicorn**: ASGI服务器
- **pydantic**: 数据验证和序列化

#### 基础设施
- **Docker**: 容器化部署
- **Docker Compose**: 服务编排
- **Python 3.10+**: 运行环境

### 1.3 系统架构

#### 整体架构图
```
┌─────────────────┐    WebSocket/HTTP    ┌─────────────────┐
│  Chrome扩展     │ ←──────────────────→ │  FastAPI网关    │
│  - sidepanel    │                      │  - WebSocket    │
│  - background   │                      │  - HTTP API     │
│  - websocket    │                      │  - 连接管理     │
└─────────────────┘                      └─────────────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │  Redis消息队列   │
                                         │  - 任务队列     │
                                         │  - 发布/订阅    │
                                         │  - 结果存储     │
                                         └─────────────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │  Celery Worker  │
                                         │  - AI任务处理   │
                                         │  - 代理支持     │
                                         │  - 文件操作     │
                                         └─────────────────┘
```

#### 数据流设计
1. **用户输入** → Chrome扩展接收
2. **WebSocket连接** → 实时双向通信
3. **任务分发** → Redis队列异步处理
4. **AI处理** → Celery Worker调用AI API
5. **结果推送** → Redis发布/订阅实时返回
6. **界面更新** → 实时显示处理结果

### 1.4 架构优势

#### V2.0 vs V1.0 对比
| 特性 | V1.0 | V2.0 |
|------|------|------|
| 通信方式 | HTTP同步 | WebSocket实时 |
| 任务处理 | 同步阻塞 | 异步非阻塞 |
| 扩展性 | 单体应用 | 微服务架构 |
| 部署方式 | 手动部署 | 容器化部署 |
| 监控能力 | 基础日志 | 完整监控体系 |

#### 技术优势
- **高性能**: WebSocket减少连接开销，异步处理提升并发能力
- **高可用**: 微服务架构，单点故障不影响整体服务
- **易扩展**: 容器化部署，支持水平扩展
- **易维护**: 模块化设计，职责分离清晰

---

## 2. 核心功能模块分析

### 2.1 Chrome扩展前端模块

#### 2.1.1 Manifest配置 (manifest.json)
```json
{
  "manifest_version": 3,
  "name": "Chrome Plus V2.0",
  "version": "2.0.0",
  "permissions": ["sidePanel", "storage", "activeTab"],
  "host_permissions": [
    "http://localhost:5001/*",
    "ws://localhost:5001/*",
    "https://api.openai.com/*",
    "https://api.deepseek.com/*"
  ],
  "side_panel": {
    "default_path": "sidepanel.html"
  },
  "background": {
    "service_worker": "background.js"
  }
}
```

#### 2.1.2 后台服务 (background.js)
- **功能**: 扩展生命周期管理、侧边栏控制
- **职责**:
  - 扩展安装和启动处理
  - 侧边栏开启/关闭控制
  - 全局状态管理

#### 2.1.3 WebSocket客户端 (websocket-api.js)
```javascript
class WebSocketAPIClient {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.channelId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    async connect() {
        const wsUrl = 'ws://localhost:5001/ws';
        this.ws = new WebSocket(wsUrl);
        // 连接处理逻辑
    }

    async sendChatMessage(message, options = {}) {
        const chatData = {
            message: message,
            user_id: options.userId || 'chrome_extension_user',
            proxy_config: options.proxyConfig || null,
            api_config: options.apiConfig || null
        };
        await this.sendMessage('chat', chatData);
    }
}
```

#### 2.1.4 聊天界面 (chat.js)
- **功能**: 用户界面交互、消息显示、状态管理
- **特性**:
  - 实时消息显示
  - Markdown渲染
  - 代码高亮
  - 连接状态指示
  - 自动重连机制

### 2.2 FastAPI后端网关

#### 2.2.1 应用配置 (main.py)
```python
app = FastAPI(
    title="Chrome Plus V2.0 API",
    description="AI助手API，支持WebSocket实时通信、异步任务处理和文件操作",
    version="2.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2.2.2 WebSocket连接管理
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        channel_id = str(uuid.uuid4())
        self.active_connections[channel_id] = websocket
        return channel_id

    async def send_personal_message(self, message: dict, channel_id: str):
        if channel_id in self.active_connections:
            await self.active_connections[channel_id].send_json(message)
```

#### 2.2.3 API端点设计
- **WebSocket端点**: `/ws` - 实时通信
- **HTTP API**: `/api/chat` - 兼容模式
- **健康检查**: `/health` - 服务状态
- **文件操作**: `/api/files/*` - 文件管理

### 2.3 Celery异步任务处理

#### 2.3.1 任务配置 (tasks.py)
```python
celery_app = Celery(
    'chrome_plus_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_time_limit=300,  # 5分钟超时
    worker_prefetch_multiplier=1,
)
```

#### 2.3.2 AI消息处理任务
```python
@celery_app.task(bind=True, name='process_ai_message')
def process_ai_message(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        request = TaskRequest(**task_data)
        task_id = self.request.id

        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'status': '正在处理AI请求...', 'progress': 10}
        )

        # 调用AI API
        response = _call_ai_api(request.message, request.api_config, request.proxy_config)

        # 发布结果到Redis频道
        _publish_result(request.channel_id, result.dict())

        return result.dict()
    except Exception as e:
        logger.error(f"任务处理失败: {e}")
        return {"success": False, "error": str(e)}
```

### 2.4 Redis消息队列

#### 2.4.1 功能职责
- **任务队列**: Celery任务的消息代理
- **发布/订阅**: 实时结果推送
- **会话存储**: 用户会话和状态管理
- **缓存**: 临时数据和配置缓存

#### 2.4.2 消息流设计
```
WebSocket请求 → FastAPI → Redis队列 → Celery Worker
                    ↑                        ↓
              Redis发布/订阅 ← 处理结果 ← AI API调用
```

---

## 3. 代码结构和组件说明

### 3.1 项目目录结构

```
chrome_plus/
├── 📄 manifest.json              # Chrome扩展配置
├── 🎨 sidepanel.html             # 主界面
├── 💅 sidepanel.css              # 样式文件
├── ⚙️ background.js              # 后台服务
├── 💬 chat.js                    # 聊天逻辑
├── 🔌 api.js                     # API通信层
├── 🌐 websocket-api.js           # WebSocket客户端
├── 🖼️ images/                    # 图标资源
│   ├── icon-16.png
│   ├── icon-48.png
│   └── icon-128.png
├── 📚 lib/                       # 第三方库
│   ├── marked/                   # Markdown解析
│   └── highlight/                # 代码高亮
├── 🚀 scripts/                   # 构建脚本
│   ├── docker-dev.sh             # Docker开发脚本
│   └── build-extension.sh        # 扩展打包脚本
├── 🐳 docker-compose.yml         # 服务编排配置
├── 🚀 start-v2.sh                # V2.0启动脚本
├── 🧪 quick_test.py              # 快速验证脚本
├── 🧪 test_chrome_plus_v2.py     # 综合测试脚本
├── 📚 docs/                      # 文档目录
│   ├── USER_MANUAL.md            # 用户手册
│   ├── DEVELOPMENT_GUIDE.md      # 开发指南
│   ├── TECHNICAL_DESIGN_REPORT.md # 技术设计报告
│   └── DEPLOYMENT_GUIDE.md       # 部署指南
└── 🖥️ server/                    # 后端服务
    ├── main.py                   # FastAPI应用
    ├── tasks.py                  # Celery任务处理
    ├── config.py                 # 配置管理
    ├── Dockerfile                # 容器配置
    ├── pyproject.toml            # 依赖配置
    ├── requirements.txt          # Python依赖
    ├── .env.example              # 环境配置示例
    ├── test_v2_architecture.py   # 架构测试
    └── test/                     # 沙箱目录
```

### 3.2 前端组件详解

#### 3.2.1 侧边栏界面 (sidepanel.html)
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Chrome Plus V2.0</title>
    <link rel="stylesheet" href="sidepanel.css">
    <link rel="stylesheet" href="lib/highlight/styles/default.css">
</head>
<body>
    <div id="app">
        <div id="header">
            <h1>Chrome Plus V2.0</h1>
            <div id="connection-status">
                <span id="status-indicator">●</span>
                <span id="status-text">连接中...</span>
            </div>
        </div>
        <div id="chat-container">
            <div id="messages"></div>
        </div>
        <div id="input-container">
            <textarea id="message-input" placeholder="输入消息..."></textarea>
            <button id="send-button">发送</button>
        </div>
    </div>

    <script src="lib/marked/marked.min.js"></script>
    <script src="lib/highlight/highlight.min.js"></script>
    <script src="websocket-api.js"></script>
    <script src="api.js"></script>
    <script src="chat.js"></script>
</body>
</html>
```

#### 3.2.2 样式设计 (sidepanel.css)
- **响应式布局**: 适配不同屏幕尺寸
- **连接状态指示**: 实时显示连接状态
- **消息样式**: 用户消息和AI回复的差异化显示
- **代码高亮**: 支持多种编程语言语法高亮

#### 3.2.3 API通信层 (api.js)
```javascript
class APIClient {
    constructor() {
        this.baseURL = 'http://localhost:5001';
        this.wsClient = null;
    }

    async sendMessage(message, options = {}) {
        // 优先使用WebSocket
        if (this.wsClient && this.wsClient.isConnected) {
            return await this.wsClient.sendChatMessage(message, options);
        }

        // 降级到HTTP
        return await this.sendHTTPMessage(message, options);
    }

    async sendHTTPMessage(message, options = {}) {
        const response = await fetch(`${this.baseURL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                proxy_config: options.proxyConfig,
                api_config: options.apiConfig
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }
}
```

### 3.3 后端组件详解

#### 3.3.1 配置管理 (config.py)
```python
import os
from typing import Optional

class Config:
    # Redis配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # API配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # 服务配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5001))

    # 安全配置
    ALLOWED_ORIGINS = [
        "chrome-extension://*",
        "http://localhost:*"
    ]

    # 文件操作配置
    SANDBOX_DIR = os.path.join(os.path.dirname(__file__), 'test')
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
```

#### 3.3.2 数据模型 (main.py)
```python
from pydantic import BaseModel
from typing import Dict, Any, Optional

class ProxyConfig(BaseModel):
    enabled: bool = False
    type: str = "http"  # http, https, socks5
    host: str = ""
    port: int = 0
    username: Optional[str] = None
    password: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    proxy_config: Optional[ProxyConfig] = None
    api_config: Optional[Dict[str, Any]] = None

class WebSocketMessage(BaseModel):
    type: str  # 'chat', 'status', 'error', 'result'
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    channel_id: Optional[str] = None
```

#### 3.3.3 文件操作模块
```python
import os
import json
from pathlib import Path

class FileManager:
    def __init__(self, sandbox_dir: str):
        self.sandbox_dir = Path(sandbox_dir)
        self.sandbox_dir.mkdir(exist_ok=True)

    def create_file(self, filename: str, content: str) -> dict:
        file_path = self.sandbox_dir / filename
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "message": f"文件 {filename} 创建成功"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_file(self, filename: str) -> dict:
        file_path = self.sandbox_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_files(self) -> dict:
        try:
            files = [f.name for f in self.sandbox_dir.iterdir() if f.is_file()]
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

## 4. API接口文档

### 4.1 WebSocket API

#### 4.1.1 连接端点
- **URL**: `ws://localhost:5001/ws`
- **协议**: WebSocket
- **认证**: 无需认证

#### 4.1.2 消息格式
```json
{
    "type": "chat|status|error|result|ping|pong",
    "data": {
        // 消息数据
    },
    "timestamp": "2024-12-XX T XX:XX:XX.XXXZ",
    "channel_id": "uuid-string"
}
```

#### 4.1.3 聊天消息
**发送格式**:
```json
{
    "type": "chat",
    "data": {
        "message": "用户输入的消息",
        "user_id": "chrome_extension_user",
        "proxy_config": {
            "enabled": true,
            "type": "http",
            "host": "proxy.example.com",
            "port": 8080,
            "username": "user",
            "password": "pass"
        },
        "api_config": {
            "model": "deepseek-chat",
            "api_key": "sk-xxx"
        }
    }
}
```

**接收格式**:
```json
{
    "type": "result",
    "data": {
        "response": "AI助手的回复内容",
        "task_id": "celery-task-id",
        "success": true
    },
    "timestamp": "2024-12-XX T XX:XX:XX.XXXZ",
    "channel_id": "uuid-string"
}
```

#### 4.1.4 状态消息
```json
{
    "type": "status",
    "data": {
        "status": "processing|completed|error",
        "progress": 50,
        "message": "正在处理中..."
    }
}
```

#### 4.1.5 心跳检测
```json
// 发送
{
    "type": "ping",
    "data": {}
}

// 接收
{
    "type": "pong",
    "data": {
        "timestamp": "2024-12-XX T XX:XX:XX.XXXZ"
    }
}
```

### 4.2 HTTP REST API

#### 4.2.1 聊天接口
- **URL**: `POST /api/chat`
- **Content-Type**: `application/json`

**请求体**:
```json
{
    "message": "用户消息",
    "proxy_config": {
        "enabled": true,
        "type": "http",
        "host": "proxy.example.com",
        "port": 8080
    },
    "api_config": {
        "model": "deepseek-chat",
        "api_key": "sk-xxx"
    }
}
```

**响应体**:
```json
{
    "response": "AI助手回复",
    "timestamp": "2024-12-XX T XX:XX:XX.XXXZ",
    "success": true
}
```

#### 4.2.2 健康检查
- **URL**: `GET /health`
- **响应**:
```json
{
    "status": "healthy",
    "version": "2.0.0",
    "services": {
        "redis": "connected",
        "celery": "running"
    },
    "timestamp": "2024-12-XX T XX:XX:XX.XXXZ"
}
```

#### 4.2.3 文件操作API

**创建文件**:
- **URL**: `POST /api/files`
```json
{
    "filename": "test.txt",
    "content": "文件内容"
}
```

**读取文件**:
- **URL**: `GET /api/files/{filename}`

**列出文件**:
- **URL**: `GET /api/files`

**删除文件**:
- **URL**: `DELETE /api/files/{filename}`

### 4.3 错误处理

#### 4.3.1 HTTP错误码
- **400**: 请求参数错误
- **401**: 认证失败
- **403**: 权限不足
- **404**: 资源不存在
- **429**: 请求频率限制
- **500**: 服务器内部错误
- **503**: 服务不可用

#### 4.3.2 错误响应格式
```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": "详细错误信息"
    },
    "timestamp": "2024-12-XX T XX:XX:XX.XXXZ"
}
```

#### 4.3.3 WebSocket错误消息
```json
{
    "type": "error",
    "data": {
        "code": "WEBSOCKET_ERROR",
        "message": "WebSocket连接错误",
        "details": "详细错误信息"
    },
    "timestamp": "2024-12-XX T XX:XX:XX.XXXZ"
}
```

---

## 5. 开发指南和最佳实践

### 5.1 开发环境搭建

#### 5.1.1 前置要求
- **Chrome 88+**: 支持Manifest V3
- **Python 3.10+**: 后端运行环境
- **Docker & Docker Compose**: 容器化部署
- **Node.js**: 前端工具链 (可选)
- **Redis**: 消息队列服务

#### 5.1.2 快速启动
```bash
# 1. 克隆项目
git clone <repository-url>
cd chrome_plus

# 2. 快速验证环境
python3 quick_test.py

# 3. 一键启动V2.0服务
./start-v2.sh

# 4. 安装Chrome扩展
# 访问 chrome://extensions/
# 开启开发者模式
# 加载已解压的扩展程序
```

#### 5.1.3 Docker开发环境
```bash
# 使用Docker Compose
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 5.1.4 手动环境搭建
```bash
# 1. 安装Python依赖
cd server
pip install -r requirements.txt
# 或使用uv: uv sync

# 2. 启动Redis
redis-server

# 3. 启动FastAPI服务
python main.py

# 4. 启动Celery Worker
celery -A tasks worker --loglevel=info

# 5. 启动Flower监控 (可选)
celery -A tasks flower
```

### 5.2 开发工作流

#### 5.2.1 代码结构规范
```
功能模块/
├── __init__.py           # 模块初始化
├── models.py             # 数据模型
├── handlers.py           # 业务逻辑
├── utils.py              # 工具函数
├── tests/                # 测试文件
│   ├── test_models.py
│   ├── test_handlers.py
│   └── test_utils.py
└── README.md             # 模块文档
```

#### 5.2.2 代码风格规范
- **Python**: 遵循PEP 8规范
- **JavaScript**: 使用ES6+语法
- **命名规范**:
  - 变量和函数: snake_case (Python) / camelCase (JavaScript)
  - 类名: PascalCase
  - 常量: UPPER_CASE
- **注释规范**:
  - 函数必须有docstring
  - 复杂逻辑必须有行内注释

#### 5.2.3 Git工作流
```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发和提交
git add .
git commit -m "feat: 添加新功能"

# 3. 推送分支
git push origin feature/new-feature

# 4. 创建Pull Request
# 5. 代码审查和合并
```

#### 5.2.4 提交消息规范
```
type(scope): description

type: feat|fix|docs|style|refactor|test|chore
scope: 影响范围 (可选)
description: 简短描述

示例:
feat(websocket): 添加心跳检测机制
fix(api): 修复代理配置解析错误
docs(readme): 更新安装指南
```

### 5.3 测试策略

#### 5.3.1 测试分类
- **单元测试**: 测试单个函数或类
- **集成测试**: 测试模块间交互
- **端到端测试**: 测试完整用户流程
- **性能测试**: 测试系统性能指标

#### 5.3.2 测试工具
- **Python**: pytest, unittest
- **JavaScript**: Jest (如需要)
- **API测试**: requests, httpx
- **WebSocket测试**: websockets库

#### 5.3.3 测试示例
```python
# test_websocket.py
import pytest
import asyncio
import websockets
import json

@pytest.mark.asyncio
async def test_websocket_connection():
    """测试WebSocket连接"""
    uri = "ws://localhost:5001/ws"

    async with websockets.connect(uri) as websocket:
        # 发送ping消息
        ping_message = {
            "type": "ping",
            "data": {}
        }
        await websocket.send(json.dumps(ping_message))

        # 接收pong响应
        response = await websocket.recv()
        data = json.loads(response)

        assert data["type"] == "pong"
        assert "timestamp" in data["data"]

@pytest.mark.asyncio
async def test_chat_message():
    """测试聊天消息处理"""
    uri = "ws://localhost:5001/ws"

    async with websockets.connect(uri) as websocket:
        # 发送聊天消息
        chat_message = {
            "type": "chat",
            "data": {
                "message": "Hello, AI!",
                "user_id": "test_user"
            }
        }
        await websocket.send(json.dumps(chat_message))

        # 接收响应
        response = await websocket.recv()
        data = json.loads(response)

        assert data["type"] in ["result", "status"]
        if data["type"] == "result":
            assert "response" in data["data"]
```

#### 5.3.4 性能测试
```python
# test_performance.py
import asyncio
import time
import statistics

async def test_websocket_latency():
    """测试WebSocket延迟"""
    latencies = []

    for i in range(100):
        start_time = time.time()

        # 发送ping并等待pong
        # ... WebSocket通信代码 ...

        end_time = time.time()
        latency = (end_time - start_time) * 1000  # 转换为毫秒
        latencies.append(latency)

    avg_latency = statistics.mean(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)

    print(f"平均延迟: {avg_latency:.2f}ms")
    print(f"最大延迟: {max_latency:.2f}ms")
    print(f"最小延迟: {min_latency:.2f}ms")

    assert avg_latency < 100  # 平均延迟应小于100ms
```

### 5.4 调试和监控

#### 5.4.1 日志配置
```python
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 使用示例
logger.info("WebSocket连接建立")
logger.error(f"任务处理失败: {error}")
logger.debug(f"接收到消息: {message}")
```

#### 5.4.2 性能监控
```python
import time
import functools

def monitor_performance(func):
    """性能监控装饰器"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"{func.__name__} 执行时间: {duration:.3f}秒")
    return wrapper

@monitor_performance
async def process_message(message):
    # 处理消息的逻辑
    pass
```

#### 5.4.3 错误追踪
```python
import traceback

try:
    # 可能出错的代码
    result = await process_ai_request(message)
except Exception as e:
    # 记录完整的错误堆栈
    logger.error(f"处理失败: {e}")
    logger.error(f"错误堆栈: {traceback.format_exc()}")

    # 返回用户友好的错误信息
    return {"success": False, "error": "处理请求时发生错误"}
```

### 5.5 安全最佳实践

#### 5.5.1 输入验证
```python
from pydantic import BaseModel, validator
import re

class ChatRequest(BaseModel):
    message: str

    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('消息不能为空')
        if len(v) > 10000:
            raise ValueError('消息长度不能超过10000字符')
        # 过滤恶意内容
        if re.search(r'<script|javascript:|data:', v, re.IGNORECASE):
            raise ValueError('消息包含不安全内容')
        return v.strip()
```

#### 5.5.2 API密钥管理
```python
import os
from cryptography.fernet import Fernet

class SecureConfig:
    def __init__(self):
        self.cipher_suite = Fernet(os.getenv('ENCRYPTION_KEY'))

    def encrypt_api_key(self, api_key: str) -> str:
        """加密API密钥"""
        return self.cipher_suite.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """解密API密钥"""
        return self.cipher_suite.decrypt(encrypted_key.encode()).decode()
```

#### 5.5.3 文件操作安全
```python
import os
from pathlib import Path

class SecureFileManager:
    def __init__(self, sandbox_dir: str):
        self.sandbox_dir = Path(sandbox_dir).resolve()

    def validate_path(self, filename: str) -> Path:
        """验证文件路径安全性"""
        # 禁止路径遍历
        if '..' in filename or filename.startswith('/'):
            raise ValueError('不安全的文件路径')

        file_path = (self.sandbox_dir / filename).resolve()

        # 确保文件在沙箱目录内
        if not str(file_path).startswith(str(self.sandbox_dir)):
            raise ValueError('文件路径超出沙箱范围')

        return file_path
```

---

## 6. 部署和配置说明

### 6.1 生产环境部署

#### 6.1.1 Docker生产部署
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - chrome_plus_network

  chrome_plus_api:
    build:
      context: ./server
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "5001:5001"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
    depends_on:
      - redis
    networks:
      - chrome_plus_network
    volumes:
      - ./server/test:/app/test

  chrome_plus_worker:
    build:
      context: ./server
      dockerfile: Dockerfile
    restart: unless-stopped
    command: celery -A tasks worker --loglevel=info --concurrency=4
    environment:
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
    depends_on:
      - redis
    networks:
      - chrome_plus_network

  flower:
    build:
      context: ./server
      dockerfile: Dockerfile
    restart: unless-stopped
    command: celery -A tasks flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    networks:
      - chrome_plus_network

volumes:
  redis_data:

networks:
  chrome_plus_network:
    driver: bridge
```

#### 6.1.2 Nginx反向代理
```nginx
# /etc/nginx/sites-available/chrome-plus
server {
    listen 80;
    server_name your-domain.com;

    # WebSocket支持
    location /ws {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API请求
    location /api {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查
    location /health {
        proxy_pass http://localhost:5001;
    }

    # 任务监控
    location /flower {
        proxy_pass http://localhost:5555;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 6.1.3 SSL配置
```bash
# 使用Let's Encrypt获取SSL证书
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 6.2 环境配置

#### 6.2.1 环境变量配置
```bash
# server/.env.prod
# Redis配置
REDIS_URL=redis://redis:6379/0

# API密钥
DEEPSEEK_API_KEY=sk-your-deepseek-key
OPENAI_API_KEY=sk-your-openai-key

# 服务配置
HOST=0.0.0.0
PORT=5001
ENVIRONMENT=production

# 安全配置
ENCRYPTION_KEY=your-encryption-key
SECRET_KEY=your-secret-key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# 代理配置 (可选)
DEFAULT_PROXY_HOST=proxy.example.com
DEFAULT_PROXY_PORT=8080
```

#### 6.2.2 Chrome扩展配置
```json
// manifest.json (生产版本)
{
  "manifest_version": 3,
  "name": "Chrome Plus V2.0",
  "version": "2.0.0",
  "host_permissions": [
    "https://your-domain.com/*",
    "wss://your-domain.com/*",
    "https://api.openai.com/*",
    "https://api.deepseek.com/*"
  ],
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'; connect-src 'self' wss://your-domain.com https://your-domain.com https://api.openai.com https://api.deepseek.com;"
  }
}
```

### 6.3 监控和维护

#### 6.3.1 健康检查脚本
```bash
#!/bin/bash
# health_check.sh

# 检查API服务
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/health)
if [ $API_STATUS -ne 200 ]; then
    echo "API服务异常: $API_STATUS"
    # 发送告警
fi

# 检查Redis连接
REDIS_STATUS=$(redis-cli ping)
if [ "$REDIS_STATUS" != "PONG" ]; then
    echo "Redis连接异常"
    # 发送告警
fi

# 检查Celery Worker
WORKER_COUNT=$(celery -A tasks inspect active | grep -c "worker")
if [ $WORKER_COUNT -eq 0 ]; then
    echo "Celery Worker异常"
    # 发送告警
fi

echo "所有服务正常运行"
```

#### 6.3.2 日志轮转配置
```bash
# /etc/logrotate.d/chrome-plus
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        docker-compose restart chrome_plus_api
    endscript
}
```

#### 6.3.3 备份策略
```bash
#!/bin/bash
# backup.sh

# 备份Redis数据
docker exec chrome_plus_redis redis-cli BGSAVE
docker cp chrome_plus_redis:/data/dump.rdb ./backups/redis-$(date +%Y%m%d).rdb

# 备份配置文件
tar -czf ./backups/config-$(date +%Y%m%d).tar.gz server/.env* docker-compose*.yml

# 清理旧备份 (保留30天)
find ./backups -name "*.rdb" -mtime +30 -delete
find ./backups -name "*.tar.gz" -mtime +30 -delete
```

### 6.4 扩展打包和发布

#### 6.4.1 扩展打包脚本
```bash
#!/bin/bash
# scripts/build-extension.sh

echo "开始打包Chrome Plus V2.0扩展..."

# 创建构建目录
BUILD_DIR="build/chrome-plus-v2"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# 复制扩展文件
cp manifest.json $BUILD_DIR/
cp *.html $BUILD_DIR/
cp *.css $BUILD_DIR/
cp *.js $BUILD_DIR/
cp -r images/ $BUILD_DIR/
cp -r lib/ $BUILD_DIR/

# 更新版本号
VERSION=$(grep '"version"' manifest.json | sed 's/.*"version": "\(.*\)".*/\1/')
echo "扩展版本: $VERSION"

# 创建zip包
cd build
zip -r "chrome-plus-v${VERSION}.zip" chrome-plus-v2/
cd ..

echo "扩展打包完成: build/chrome-plus-v${VERSION}.zip"
```

#### 6.4.2 发布检查清单
- [ ] 版本号更新
- [ ] 功能测试通过
- [ ] 安全审查完成
- [ ] 文档更新
- [ ] 变更日志记录
- [ ] 生产环境测试
- [ ] 备份当前版本
- [ ] 发布计划确认

---

## 总结

Chrome Plus V2.0项目采用现代化的微服务架构，通过WebSocket实现实时通信，使用Celery处理异步任务，Redis作为消息队列，Docker进行容器化部署。项目具有良好的可扩展性、高可用性和易维护性。

### 技术亮点
- **实时通信**: WebSocket双向通信，提升用户体验
- **异步处理**: Celery分布式任务队列，支持高并发
- **微服务架构**: 服务解耦，易于扩展和维护
- **容器化部署**: Docker一键部署，环境一致性
- **完善监控**: 健康检查、日志记录、性能监控

### 开发优势
- **标准化**: 遵循现代开发规范和最佳实践
- **可测试**: 完整的测试策略和工具链
- **可维护**: 清晰的代码结构和文档
- **可扩展**: 模块化设计，支持功能扩展

这份技术文档为Chrome Plus V2.0项目的开发、部署和维护提供了全面的指导，确保项目的技术质量和可持续发展。