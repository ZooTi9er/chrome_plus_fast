# Chrome Plus V2.1.1 用户使用指南

## 📋 文档信息

| 项目名称 | Chrome Plus V2.1.1 用户使用指南 |
|---------|------------------------------|
| 版本 | 2.1.1 |
| 文档类型 | 用户操作手册 |
| 目标受众 | 最终用户、产品使用者、系统管理员 |
| 最后更新 | 2025-01-04 |
| 用途 | 安装配置、功能使用、问题解决、最佳实践 |

## 🎯 指南概述

本指南为Chrome Plus V2.1.1的完整用户使用手册，基于V2.1.1版本的实际功能实现提供：

- **📦 详细安装步骤**：Chrome扩展安装和后端服务部署的完整流程（Docker和手动两种方式）
- **🚀 功能使用说明**：AI对话、15种文件操作工具、网络搜索、代理配置等核心功能详解
- **⚙️ 配置选项详解**：API密钥配置、代理设置、服务器地址配置、环境变量管理等
- **🔧 故障排除指南**：连接错误、权限问题、性能问题、服务异常的诊断和解决方案
- **🛡️ 安全最佳实践**：API密钥保护、网络安全、文件系统安全等使用建议
- **🚀 性能优化建议**：系统配置优化、网络配置优化、监控和调优指南

## 📚 目录

1. [产品介绍](#1-产品介绍)
2. [系统要求](#2-系统要求)
3. [安装指南](#3-安装指南)
4. [功能使用](#4-功能使用)
5. [配置选项](#5-配置选项)
6. [常见问题](#6-常见问题)
7. [安全注意事项](#7-安全注意事项)
8. [性能优化建议](#8-性能优化建议)

---

## 1. 产品介绍

### 1.1 产品概述

Chrome Plus V2.1.1是一款基于Chrome Manifest V3的智能AI助手扩展，采用前后端分离的微服务架构，提供强大的AI对话和文件操作能力。

**🚀 核心特性**：
- **🤖 智能AI对话**：支持DeepSeek、OpenAI等多种AI模型，流式响应体验
- **📁 文件操作工具**：18种文件和目录操作功能，安全沙箱环境隔离
- **🗂️ 文件夹管理界面**：可视化文件夹浏览、创建、删除、重命名等操作
- **🔍 网络搜索**：Tavily API实时信息检索和智能摘要功能
- **⚡ 实时通信**：WebSocket双向通信，HTTP自动降级保障
- **🌍 代理支持**：HTTP、HTTPS、SOCKS5代理协议，解决地理限制
- **🐳 容器化部署**：Docker Compose一键启动所有服务，包含监控界面

**🎯 主要使用场景**：
- **日常AI对话**：智能问答、技术咨询、创意写作
- **文件管理**：文件读写、目录操作、备份归档、可视化文件夹管理
- **信息搜索**：实时网络搜索、资料收集、信息验证
- **开发辅助**：代码编写、调试支持、技术文档处理
- **内容创作**：文档编写、Markdown处理、格式转换
- **系统管理**：系统信息查看、性能监控、日志分析
- **项目管理**：文件夹结构管理、项目文件组织、批量操作

**💡 产品优势**：
- **安全可靠**：沙箱隔离、权限控制、数据加密
- **高性能**：异步处理、任务队列、负载均衡
- **易于使用**：直观界面、一键安装、智能配置
- **可扩展**：模块化设计、插件架构、API开放

### 1.2 技术亮点

**🔧 前端技术**：
- **Chrome Manifest V3**：最新扩展标准，更安全更高效的Service Worker
- **WebSocket实时通信**：毫秒级响应，支持流式AI回复和状态反馈
- **自动降级机制**：WebSocket失败时自动切换到HTTP，保证服务可用性
- **Markdown渲染**：完整支持GitHub风格Markdown和代码高亮

**⚙️ 后端架构**：
- **微服务架构**：Redis + FastAPI + Celery分布式处理，可扩展设计
- **异步任务队列**：Celery支持长时间AI处理，避免超时问题
- **智能代理系统**：15种文件操作工具的安全实现和管理
- **多协议代理**：HTTP/HTTPS/SOCKS5代理支持，解决地理限制

**🛡️ 安全特性**：
- **沙箱安全机制**：文件操作限制在安全目录内，防止系统文件访问
- **API密钥加密**：本地加密存储，安全的密钥管理
- **输入验证**：完善的输入清理和验证机制
- **CORS保护**：严格的跨域请求控制

### 1.3 界面预览

Chrome Plus V2.1.1采用侧边栏设计，不干扰正常浏览体验：

**🎨 主要界面元素**：
- **聊天区域**：支持Markdown渲染的对话界面
- **输入框**：智能输入提示和快捷键支持
- **状态指示器**：实时显示连接状态和通信模式
- **设置面板**：API配置、代理设置、系统选项
- **工具栏**：快速访问常用功能和设置

```
┌─────────────────────────────────┐
│ 🤖 AI助手                    ⚙️ │
├─────────────────────────────────┤
│                                 │
│ 用户: 请创建一个test.txt文件     │
│                                 │
│ 🤖 AI: 我来为您创建test.txt文件  │
│ ✅ 文件创建成功                  │
│                                 │
│ 用户: 列出当前目录的文件         │
│                                 │
│ 🤖 AI: 当前目录包含以下文件：    │
│ 📄 test.txt (文件, 0 bytes)     │
│                                 │
├─────────────────────────────────┤
│ 输入你的消息...            [发送] │
└─────────────────────────────────┘
```

---

## 2. 系统要求

### 2.1 浏览器要求

**🌐 Chrome浏览器**：
- **最低版本**：Chrome 88+ (支持Manifest V3)
- **推荐版本**：Chrome 120+ (最新稳定版)
- **必需功能**：支持Manifest V3扩展标准
- **权限要求**：允许安装开发者扩展

**🔍 检查Chrome版本**：
1. 打开Chrome浏览器
2. 地址栏输入：`chrome://version/`
3. 查看版本号是否满足要求
4. 如版本过低，请更新到最新版本

**💻 操作系统支持**：
- **Windows**：Windows 10+ (64位)
- **macOS**：macOS 10.15+ (Catalina及以上)
- **Linux**：Ubuntu 18.04+、CentOS 8+、Debian 10+

### 2.2 后端服务要求

**🐍 Python环境**：
- **Python版本**：3.10+ (推荐3.11或3.12)
- **包管理器**：uv (推荐，速度快) 或 pip 23.0+
- **虚拟环境**：强烈建议使用venv、conda或uv环境

**🗄️ 系统依赖**：
- **Redis服务器**：6.0+ (消息队列、缓存、会话存储)
- **网络连接**：稳定的互联网连接访问AI API
- **磁盘空间**：至少2GB可用空间 (包含依赖和缓存)

**🐳 Docker环境（推荐）**：
- **Docker**：20.10+ (容器运行时)
- **Docker Compose**：2.0+ (多服务编排)
- **系统内存**：至少4GB可用内存 (推荐8GB)
- **CPU**：2核心以上 (推荐4核心)

### 2.3 网络要求

**🌍 必需连接**：
- `api.deepseek.com` - DeepSeek AI API (主要AI服务)
- `api.openai.com` - OpenAI API (备用AI服务)
- `api.tavily.com` - Tavily搜索API (网络搜索功能)
- `localhost:5001` - 本地后端服务
- `localhost:5555` - Flower监控界面 (可选)

**🔗 代理支持**：
- **HTTP/HTTPS代理**：标准代理协议
- **SOCKS5代理**：高级代理协议
- **认证代理**：支持用户名/密码认证
- **代理测试**：内置代理连接测试功能

**📊 网络性能要求**：
- **带宽**：建议10Mbps以上
- **延迟**：低于100ms (影响WebSocket体验)
- **稳定性**：持续稳定连接 (避免频繁断线)

---

## 3. 安装指南

### 3.1 Chrome扩展安装

#### 3.1.1 下载项目

**📥 方法1：Git克隆（推荐）**
```bash
# 克隆项目到本地
git clone https://github.com/ZooTi9er/chrome_plus_fast.git
cd chrome_plus_fast

# 检查项目完整性
ls -la  # 应该看到manifest.json等文件
```

**📦 方法2：下载ZIP包**
1. 访问GitHub项目页面
2. 点击绿色"Code"按钮
3. 选择"Download ZIP"
4. 解压到本地目录

**✅ 验证下载完整性**
```bash
# 检查关键文件是否存在
ls manifest.json sidepanel.html server/main.py
# 应该显示所有文件都存在
```

#### 3.1.2 启用开发者模式

**🔧 步骤详解**：

1. **打开扩展管理页面**
   - 方法1：地址栏输入 `chrome://extensions/`
   - 方法2：Chrome菜单 → 更多工具 → 扩展程序
   - 方法3：快捷键 `Ctrl+Shift+E` (Windows/Linux) 或 `Cmd+Shift+E` (Mac)

2. **启用开发者模式**
   - 找到页面右上角的"开发者模式"开关
   - 点击开关，确保处于启用状态（蓝色/绿色）
   - 页面会刷新并显示开发者选项

3. **验证开发者模式**
   - 应该看到"加载已解压的扩展程序"按钮
   - 应该看到"打包扩展程序"按钮
   - 如果没有看到，请刷新页面重试

#### 3.1.3 加载扩展

**📂 安装步骤**：

1. **加载扩展程序**
   - 点击"加载已解压的扩展程序"按钮
   - 在文件选择器中导航到项目根目录
   - 选择包含`manifest.json`的文件夹
   - 点击"选择文件夹"确认

2. **验证安装成功**
   - 扩展列表中应出现"Chrome Plus V2.1.1"
   - 扩展图标应显示在Chrome工具栏
   - 扩展状态应为"已启用"
   - 版本号应显示为"2.1.1"

3. **固定扩展图标（推荐）**
   - 点击Chrome工具栏右侧的拼图图标（扩展菜单）
   - 找到"Chrome Plus V2.1.1"
   - 点击图钉图标将其固定到工具栏
   - 图标会出现在工具栏中，方便快速访问

#### 3.1.4 测试扩展功能

**🧪 功能验证**：

1. **打开侧边栏**
   - 点击Chrome工具栏的Chrome Plus图标
   - 侧边栏应在浏览器右侧打开
   - 界面应显示"AI助手"标题

2. **检查连接状态**
   - 侧边栏顶部应显示连接状态指示器
   - 初次使用可能显示"未连接"或"连接失败"
   - 这是正常现象，需要先启动后端服务

3. **验证界面元素**
   - 应该看到聊天消息区域
   - 应该看到底部的输入框和发送按钮
   - 应该看到右上角的设置按钮（⚙️）

**⚠️ 常见问题**：
- 如果扩展无法加载，检查manifest.json文件是否存在
- 如果图标不显示，尝试刷新扩展页面
- 如果侧边栏无法打开，检查Chrome版本是否支持Manifest V3

### 3.2 后端服务安装

#### 3.2.1 Docker方式安装（推荐）

**🐳 优势**：一键部署，环境隔离，易于管理，生产就绪

**📋 前置要求**：
- Docker 20.10+ 已安装
- Docker Compose 2.0+ 已安装
- 至少4GB可用内存

**🚀 安装步骤**：

```bash
# 1. 进入项目目录
cd chrome_plus_fast

# 2. 配置环境变量（重要）
cp server/.env.example server/.env

# 3. 编辑环境配置文件
nano server/.env  # 或使用其他编辑器

# 在.env文件中添加以下配置：
# DEEPSEEK_API_KEY=your_deepseek_api_key_here
# TAVILY_API_KEY=your_tavily_api_key_here  # 可选
# OPENAI_API_KEY=your_openai_api_key_here  # 可选

# 4. 启动所有服务
docker-compose up -d --build

# 5. 验证服务状态
docker-compose ps
```

**✅ 预期输出**：
```
NAME                    IMAGE                   STATUS
chrome_plus_backend     chrome_plus_backend     Up (healthy)
chrome_plus_redis       redis:7-alpine          Up (healthy)
chrome_plus_worker      chrome_plus_backend     Up
chrome_plus_flower      chrome_plus_backend     Up
```

**🔧 服务说明**：
- **backend**：FastAPI主服务（端口5001）- 处理API请求和WebSocket连接
- **redis**：Redis缓存服务（端口6379）- 消息队列和会话存储
- **worker**：Celery异步任务处理器 - 处理AI API调用和文件操作
- **flower**：Celery监控界面（端口5555）- 任务监控和性能指标

**🌐 访问地址**：
- 主服务：http://localhost:5001
- API文档：http://localhost:5001/docs
- 健康检查：http://localhost:5001/health
- Flower监控：http://localhost:5555

#### 3.2.2 手动安装方式

**🛠️ 适用场景**：开发调试，自定义配置，学习研究

**📋 前置要求**：
- Python 3.10+ 已安装
- Redis服务器可用
- 网络连接正常

**🐍 Python环境配置**：

```bash
# 1. 进入服务器目录
cd server

# 2. 创建虚拟环境（推荐使用uv）
# 方法1：使用uv（推荐，速度快）
uv venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows
uv pip install -r requirements.txt

# 方法2：使用传统pip
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. 验证依赖安装
python -c "import fastapi, celery, redis; print('依赖安装成功')"
```

**🗄️ Redis服务配置**：

```bash
# macOS (使用Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis

# Windows
# 下载Redis for Windows或使用WSL
```

**⚙️ 环境变量配置**：

```bash
# 1. 复制环境配置模板
cp .env.example .env

# 2. 编辑配置文件
nano .env  # 或使用其他编辑器

# 3. 添加必要的API密钥
echo "DEEPSEEK_API_KEY=your_api_key_here" >> .env
echo "TAVILY_API_KEY=your_tavily_key_here" >> .env  # 可选
```

**🚀 服务启动**：

```bash
# 1. 启动FastAPI主服务
python main.py

# 2. 启动Celery Worker（新终端窗口）
source .venv/bin/activate  # 激活虚拟环境
celery -A tasks worker --loglevel=info

# 3. 启动Flower监控（可选，新终端窗口）
source .venv/bin/activate  # 激活虚拟环境
celery -A tasks flower --port=5555
```

**📝 启动顺序说明**：
1. **Redis服务**：必须首先启动
2. **FastAPI主服务**：提供API和WebSocket服务
3. **Celery Worker**：处理异步任务
4. **Flower监控**：可选，用于监控任务状态

#### 3.2.3 验证安装

**🔍 健康检查**：

```bash
# 1. 检查主服务健康状态
curl http://localhost:5001/health

# 预期响应：
{
  "status": "healthy",
  "version": "2.1.1",
  "features": {
    "redis": "healthy",
    "intelligent_agent": "enabled",
    "file_operations": "enabled",
    "network_search": "enabled",
    "ai_api": "enabled"
  },
  "websocket_connections": 0,
  "uptime": "0:05:23"
}
```

**🌐 WebSocket连接测试**：

```javascript
// 在浏览器控制台执行：
const ws = new WebSocket('ws://localhost:5001/ws');
ws.onopen = () => console.log('✅ WebSocket连接成功');
ws.onerror = (error) => console.log('❌ WebSocket连接失败:', error);
ws.onmessage = (event) => console.log('📨 收到消息:', event.data);
```

**🧪 运行验证脚本**：

```bash
# 进入服务器目录
cd server

# 运行快速验证脚本
python quick_verify.py

# 预期输出：
# 📊 功能完整性验证:
#   配置检查: 5/5 (100%)
#   文件操作: 14/14 (100%)
#   智能体功能: 7/7 (100%)
#   代理功能: 3/3 (100%)
#   路由端点: 4/4 (100%)
#   智能体工具: 16/16 (100%)
#
# 总体完整性: 33/33 (100.0%)
```

**📊 服务状态检查**：

```bash
# 检查所有服务端口
netstat -tlnp | grep -E ':(5001|5555|6379)'

# 预期输出：
# tcp 0.0.0.0:5001 LISTEN  # FastAPI主服务
# tcp 0.0.0.0:5555 LISTEN  # Flower监控
# tcp 127.0.0.1:6379 LISTEN  # Redis服务
```

### 3.3 配置API密钥

#### 3.3.1 获取API密钥

**🤖 DeepSeek API（推荐）**：
1. 访问：https://platform.deepseek.com/
2. 注册账号并完成邮箱验证
3. 登录后进入"API密钥"管理页面
4. 点击"创建新密钥"按钮
5. 设置密钥名称（如：Chrome Plus）
6. 复制生成的API密钥（格式：sk-xxxxxxxx）
7. **重要**：密钥只显示一次，请妥善保存

**🧠 OpenAI API（备用）**：
1. 访问：https://platform.openai.com/
2. 注册账号并完成身份验证
3. 进入"API Keys"页面
4. 点击"Create new secret key"
5. 设置密钥名称并复制密钥（格式：sk-xxxxxxxx）
6. **注意**：需要绑定信用卡并充值

**🔍 Tavily API（网络搜索，可选）**：
1. 访问：https://tavily.com/
2. 注册账号并登录
3. 进入Dashboard获取API密钥
4. 复制密钥（格式：tvly-xxxxxxxx）
5. 用于增强网络搜索功能

#### 3.3.2 配置密钥

**🔧 方法1：环境变量文件（推荐）**

```bash
# 编辑 server/.env 文件
nano server/.env

# 添加以下配置：
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 可选
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 可选

# 其他可选配置：
REDIS_URL=redis://localhost:6379/0
SERVER_HOST=0.0.0.0
SERVER_PORT=5001
LOG_LEVEL=INFO
```

**🌐 方法2：Chrome扩展设置界面**

1. 点击Chrome工具栏的Chrome Plus图标
2. 在侧边栏中点击右上角设置按钮（⚙️）
3. 在"API配置"部分：
   - **DeepSeek API密钥**：输入sk-开头的密钥
   - **OpenAI API密钥**：输入sk-开头的密钥（可选）
   - **Tavily API密钥**：输入tvly-开头的密钥（可选）
4. 点击"测试连接"验证密钥有效性
5. 点击"保存配置"按钮
6. 配置会加密存储在Chrome本地存储中

**方法3：系统环境变量**
```bash
# Linux/macOS
export DEEPSEEK_API_KEY="sk-your-deepseek-api-key"
export OPENAI_API_KEY="sk-your-openai-api-key"

# Windows
set DEEPSEEK_API_KEY=sk-your-deepseek-api-key
set OPENAI_API_KEY=sk-your-openai-api-key
```

#### 3.3.3 验证配置

```bash
# 测试API连接
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，请介绍一下你自己"}'

# 预期响应：包含AI回复的JSON数据
```

---

## 4. 功能使用

### 4.1 基础AI对话

#### 4.1.1 开始对话

1. **打开扩展**
   - 点击Chrome工具栏的Chrome Plus图标
   - 侧边栏自动在右侧打开

2. **检查连接状态**
   - 查看侧边栏顶部的连接指示器
   - 🟢 绿色：WebSocket连接正常
   - 🟡 黄色：HTTP模式（降级）
   - 🔴 红色：连接失败

3. **发送消息**
   - 在底部输入框输入消息
   - 按Enter键或点击"发送"按钮
   - AI会实时回复您的消息

#### 4.1.2 对话示例

**基础问答**：
```
用户：你好，请介绍一下你自己
AI：您好！我是ShellAI，一个经验丰富的程序员助手。我可以帮助您进行文件操作、回答技术问题、进行网络搜索等。有什么我可以帮助您的吗？

用户：今天天气怎么样？
AI：我需要进行网络搜索来获取最新的天气信息。让我为您查询一下...
[调用网络搜索工具]
根据最新信息，今天的天气情况是...
```

**技术问答**：
```
用户：如何在Python中读取JSON文件？
AI：在Python中读取JSON文件有几种方法，最常用的是使用json模块：

```python
import json

# 方法1：读取JSON文件
with open('data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    print(data)

# 方法2：解析JSON字符串
json_string = '{"name": "张三", "age": 30}'
data = json.loads(json_string)
print(data['name'])
```

这种方法安全且高效，建议在生产环境中使用。
```

#### 4.1.3 Markdown渲染

Chrome Plus V2.1.1支持完整的Markdown渲染：

- **文本格式**：**粗体**、*斜体*、~~删除线~~
- **代码块**：语法高亮，支持多种编程语言
- **列表**：有序列表、无序列表
- **链接**：自动识别和渲染链接
- **表格**：完整的表格支持
- **引用**：> 引用块渲染

### 4.2 文件操作功能

Chrome Plus V2.1.1内置15种文件操作工具，所有操作在安全沙箱环境中执行。

#### 4.2.1 基础文件操作

**创建文件**：
```
用户：请创建一个名为hello.txt的文件，内容是"Hello, World!"
AI：我来为您创建hello.txt文件。
[调用write_file工具]
✅ 成功向 'hello.txt' 写入 13 字节。
文件已创建完成！
```

**读取文件**：
```
用户：请读取hello.txt的内容
AI：我来读取hello.txt文件的内容。
[调用read_file工具]
文件内容：
Hello, World!
```

**列出文件**：
```
用户：显示当前目录的文件列表
AI：我来列出当前目录的文件。
[调用list_files工具]
当前目录包含以下文件：
📄 hello.txt (文件, 13 bytes, 2025-01-04 10:30:00)
📁 backup/ (目录, ---, 2025-01-04 10:25:00)
```

#### 4.2.2 高级文件操作

**文件搜索**：
```
用户：查找所有.txt文件
AI：我来搜索所有.txt文件。
[调用find_files工具]
找到以下.txt文件：
📄 hello.txt
📄 notes.txt
📄 backup/old.txt
```

**文件对比**：
```
用户：比较file1.txt和file2.txt的差异
AI：我来对比这两个文件的差异。
[调用diff_files工具]
文件差异：
--- file1.txt
+++ file2.txt
@@ -1,3 +1,3 @@
 第一行内容
-第二行内容（旧）
+第二行内容（新）
 第三行内容
```

**文件压缩**：
```
用户：将所有.txt文件压缩成archive.zip
AI：我来将所有.txt文件压缩成archive.zip。
[调用archive_files工具]
✅ 成功创建压缩文件 'archive.zip'，包含 3 个文件。
```

#### 4.2.3 完整工具列表

| 工具名称 | 功能描述 | 使用示例 |
|---------|---------|---------|
| `read_file` | 读取文件内容 | "读取config.json的内容" |
| `write_file` | 写入文件内容 | "创建一个Python脚本文件" |
| `list_files` | 列出目录内容 | "显示当前目录的文件" |
| `create_directory` | 创建目录 | "创建一个名为backup的文件夹" |
| `delete_file` | 删除文件 | "删除temp.txt文件" |
| `rename_file` | 重命名文件 | "将old.txt重命名为new.txt" |
| `diff_files` | 文件差异对比 | "比较两个配置文件的差异" |
| `tree` | 目录树显示 | "显示项目的目录结构" |
| `find_files` | 文件搜索 | "查找所有Python文件" |
| `replace_in_file` | 文件内容替换 | "替换配置文件中的端口号" |
| `archive_files` | 文件压缩 | "压缩所有日志文件" |
| `extract_archive` | 解压文件 | "解压backup.zip文件" |
| `backup_file` | 文件备份 | "备份重要的配置文件" |
| `get_system_info` | 系统信息 | "显示系统配置信息" |
| `pwd` | 当前目录 | "显示当前工作目录" |
| `get_folder_tree` | 文件夹树结构 | "显示文件夹的树状结构" |
| `delete_folder` | 删除文件夹 | "递归删除文件夹及其内容" |
| `get_folder_info` | 文件夹信息 | "获取文件夹的详细统计信息" |

### 4.3 文件夹管理界面

Chrome Plus V2.1.1新增了可视化文件夹管理界面，提供直观的文件夹操作体验。

#### 4.3.1 访问文件管理器

1. **打开文件管理标签页**：
   - 点击Chrome Plus侧边栏顶部的"📁 文件管理"标签
   - 界面会自动加载文件夹树状结构

2. **界面布局**：
   - **左侧**：文件夹树状结构，支持展开/折叠
   - **右侧**：文件详情面板，显示选中项的详细信息
   - **顶部**：工具栏，包含刷新、新建文件夹等操作按钮

#### 4.3.2 文件夹浏览

**树状结构浏览**：
- 📁 文件夹图标：可点击展开/折叠子目录
- 📄 文件图标：显示文件名、大小和修改时间
- 🔄 自动刷新：切换到文件管理标签页时自动加载最新状态

**文件详情查看**：
- 点击任意文件或文件夹查看详细信息
- 显示内容：名称、路径、类型、大小、修改时间、创建时间
- 文件夹额外信息：包含的文件数量、子文件夹数量、总大小

#### 4.3.3 文件夹操作

**创建文件夹**：
1. 点击工具栏的"📁+"按钮
2. 在弹出的对话框中输入文件夹名称
3. 确认创建位置（默认为当前路径）
4. 点击"确认"完成创建

**重命名文件夹**：
1. 右键点击要重命名的文件夹
2. 选择"✏️ 重命名"
3. 输入新的文件夹名称
4. 点击"确认"完成重命名

**删除文件夹**：
1. 右键点击要删除的文件夹
2. 选择"🗑️ 删除"
3. 确认删除操作（注意：会递归删除所有内容）
4. 点击"确认"完成删除

**右键菜单功能**：
- 📂 打开：进入文件夹（仅限文件夹）
- ✏️ 重命名：重命名文件或文件夹
- 🗑️ 删除：删除文件或文件夹
- ℹ️ 属性：查看详细信息

#### 4.3.4 AI智能代理集成

文件夹管理功能完全集成到AI智能代理中，支持自然语言操作：

**AI文件夹操作示例**：
```
用户：显示当前目录的文件夹结构
AI：我来显示当前目录的文件夹树状结构。
[调用get_folder_tree工具]
📁 ./
├── 📄 hello.txt (13 B, 2025-01-04 10:30:00)
├── 📁 documents/
│   ├── 📄 readme.md (1.2 KB, 2025-01-04 09:15:00)
│   └── 📁 images/
│       └── 📄 logo.png (45 KB, 2025-01-04 08:30:00)
└── 📁 backup/
    └── 📄 old_data.txt (256 B, 2025-01-03 15:20:00)

总计：3个文件夹，4个文件
```

```
用户：获取documents文件夹的详细信息
AI：我来获取documents文件夹的详细信息。
[调用get_folder_info工具]
📁 documents文件夹信息：
- 路径：./documents
- 类型：文件夹
- 修改时间：2025-01-04 09:15:00
- 创建时间：2025-01-04 08:00:00
- 总大小：46.2 KB
- 文件数量：2个
- 子文件夹数量：1个
```

#### 4.3.5 安全特性

**沙箱限制**：
- 所有文件夹操作限制在`./server/test/`目录内
- 自动路径验证，防止路径遍历攻击
- 操作日志记录，便于审计和调试

**权限控制**：
- 只能操作沙箱目录内的文件和文件夹
- 自动检查文件系统权限
- 错误处理和用户友好的提示信息

### 4.4 网络搜索功能

#### 4.3.1 实时信息搜索

**新闻和时事**：
```
用户：最新的人工智能发展动态
AI：我来为您搜索最新的人工智能发展动态。
[调用tavily_search_tool]
根据最新搜索结果：

1. **GPT-4 Turbo发布**：OpenAI发布了更快、更便宜的GPT-4 Turbo模型...
2. **谷歌Gemini更新**：谷歌发布了Gemini Pro模型的重大更新...
3. **AI监管政策**：欧盟通过了新的AI监管法案...

[详细信息和链接]
```

**技术问题**：
```
用户：Python 3.12的新特性有哪些？
AI：我来搜索Python 3.12的新特性信息。
[调用tavily_search_tool]
Python 3.12的主要新特性包括：

1. **性能提升**：比Python 3.11快15%
2. **新语法特性**：改进的错误消息和类型提示
3. **标准库更新**：新增pathlib增强功能
4. **开发者工具**：改进的调试器和性能分析工具

[详细技术文档链接]
```

#### 4.3.2 搜索配置

**启用网络搜索**：
1. 获取Tavily API密钥（https://tavily.com/）
2. 在.env文件中配置：`TAVILY_API_KEY=tvly-your-key`
3. 重启后端服务
4. 测试搜索功能

**搜索限制**：
- 每次搜索返回最多5个结果
- 搜索结果包含标题、摘要和链接
- 支持中文和英文搜索
- 自动过滤低质量内容

### 4.4 代理功能

#### 4.4.1 代理配置

**打开代理设置**：
1. 点击Chrome Plus图标打开侧边栏
2. 点击右上角的⚙️设置按钮
3. 切换到"代理设置"标签页

**配置代理服务器**：
1. 勾选"启用代理"
2. 选择代理类型：HTTP、HTTPS或SOCKS5
3. 输入代理服务器地址和端口
4. 如需认证，输入用户名和密码
5. 点击"测试代理连接"验证
6. 点击"保存设置"

#### 4.4.2 代理预设

Chrome Plus V2.1.1提供常用代理预设：

- **本地HTTP代理**：127.0.0.1:8080
- **本地SOCKS5代理**：127.0.0.1:1080
- **Squid默认配置**：127.0.0.1:3128

#### 4.4.3 代理测试

```bash
# 测试代理连接
curl -X POST http://localhost:5001/test-proxy \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "type": "http",
    "host": "proxy.example.com",
    "port": 8080,
    "auth": {
      "username": "user",
      "password": "pass"
    }
  }'

# 预期响应：
{
  "success": true,
  "message": "代理连接测试成功"
}
```

---

## 5. 配置选项

### 5.1 服务器配置

#### 5.1.1 服务器地址配置

**本地开发环境**：
```javascript
// config.js
const CONFIG = {
    SERVER: {
        HOST: 'localhost',  // 本地开发
        PORT: 5001
    }
};
```

**网络部署环境**：
```javascript
// config.js
const CONFIG = {
    SERVER: {
        HOST: '192.168.1.100',  // 局域网IP
        PORT: 5001
    }
};
```

**Docker部署环境**：
```bash
# server/.env
SERVER_HOST=0.0.0.0  # 监听所有网络接口
API_PORT=5001
```

#### 5.1.2 通信模式配置

**WebSocket优先模式**（推荐）：
```javascript
const CONFIG = {
    COMMUNICATION: {
        PREFER_WEBSOCKET: true,  // 优先使用WebSocket
        RECONNECT: {
            MAX_ATTEMPTS: 5,     // 最大重连次数
            DELAY: 1000,         // 重连延迟（毫秒）
            BACKOFF_FACTOR: 1.5  // 退避因子
        }
    }
};
```

**HTTP模式**：
```javascript
const CONFIG = {
    COMMUNICATION: {
        PREFER_WEBSOCKET: false,  // 仅使用HTTP
    }
};
```

### 5.2 AI模型配置

#### 5.2.1 模型选择

**DeepSeek模型**（推荐）：
- **模型名称**：`deepseek-chat`
- **特点**：中文支持好，响应速度快，成本低
- **适用场景**：日常对话、代码生成、文档处理

**OpenAI模型**：
- **GPT-3.5-turbo**：快速响应，成本较低
- **GPT-4**：更强能力，成本较高
- **适用场景**：复杂推理、创意写作

#### 5.2.2 模型参数配置

```python
# server/agent_tools.py - AI API调用参数
data = {
    'model': 'deepseek-chat',
    'messages': [{'role': 'user', 'content': prompt}],
    'stream': False,
    'temperature': 0.7,      # 创造性（0-1）
    'max_tokens': 4000,      # 最大回复长度
    'top_p': 0.9,           # 核采样参数
    'frequency_penalty': 0   # 频率惩罚
}
```

**参数说明**：
- `temperature`：控制回复的随机性和创造性
  - 0.1-0.3：更准确、一致的回复
  - 0.7-0.9：更有创意、多样的回复
- `max_tokens`：限制回复的最大长度
- `top_p`：核采样，控制词汇选择的多样性

### 5.3 安全配置

#### 5.3.1 沙箱目录配置

```python
# server/config.py - 沙箱配置
class Settings:
    # 文件操作基础目录
    BASE_DIR: Path = Path(__file__).parent.resolve() / "test"

    # 最大文件大小（字节）
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS: List[str] = [
        '.txt', '.md', '.json', '.yaml', '.yml',
        '.py', '.js', '.html', '.css', '.xml'
    ]
```

#### 5.3.2 CORS配置

```python
# server/main.py - CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # Chrome扩展
        "http://localhost:*",    # 本地开发
        "http://127.0.0.1:*"     # 本地回环
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 5.4 性能配置

#### 5.4.1 Celery Worker配置

```bash
# 启动多个Worker进程
celery -A tasks worker --loglevel=info --concurrency=4

# 设置任务超时
celery -A tasks worker --time-limit=300 --soft-time-limit=240
```

#### 5.4.2 Redis配置

```bash
# server/.env - Redis性能配置
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=20
REDIS_RETRY_ON_TIMEOUT=true
```

#### 5.4.3 HTTP客户端配置

```python
# server/agent_tools.py - HTTP客户端优化
client_kwargs = {
    'timeout': httpx.Timeout(30.0, connect=10.0),
    'limits': httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10
    ),
    'follow_redirects': True,
}
```

---

## 6. 常见问题

### 6.1 安装问题

#### Q1: Chrome扩展安装失败

**问题描述**：点击"加载已解压的扩展程序"后出现错误

**可能原因**：
- 选择的文件夹不正确
- manifest.json文件格式错误
- Chrome版本不支持Manifest V3

**解决方案**：
1. 确保选择包含manifest.json的根目录
2. 检查manifest.json语法：
   ```bash
   # 验证JSON格式
   python -c "import json; json.load(open('manifest.json'))"
   ```
3. 更新Chrome到最新版本
4. 重启Chrome浏览器

#### Q2: 后端服务启动失败

**问题描述**：运行`python main.py`时出现错误

**常见错误和解决方案**：

**端口占用错误**：
```bash
# 错误：Address already in use
# 解决：查找并终止占用进程
lsof -i :5001
kill -9 <PID>
```

**依赖缺失错误**：
```bash
# 错误：ModuleNotFoundError
# 解决：重新安装依赖
pip install -r requirements.txt
```

**Redis连接错误**：
```bash
# 错误：Connection refused
# 解决：启动Redis服务
# macOS: brew services start redis
# Ubuntu: sudo systemctl start redis-server
```

### 6.2 连接问题

#### Q3: WebSocket连接失败

**问题描述**：Chrome扩展显示"连接失败"

**诊断步骤**：
1. **检查后端服务状态**：
   ```bash
   curl http://localhost:5001/health
   ```

2. **测试WebSocket连接**：
   ```javascript
   // 在浏览器控制台执行
   const ws = new WebSocket('ws://localhost:5001/ws');
   ws.onopen = () => console.log('连接成功');
   ws.onerror = (e) => console.error('连接失败', e);
   ```

3. **检查防火墙设置**：
   - 确保5001端口未被防火墙阻止
   - 检查杀毒软件是否拦截连接

**解决方案**：
- 重启后端服务
- 检查config.js中的服务器地址
- 尝试使用HTTP模式（设置PREFER_WEBSOCKET为false）

#### Q4: API调用失败

**问题描述**：AI回复显示"API调用失败"

**可能原因**：
- API密钥未配置或无效
- 网络连接问题
- API服务商限制

**解决方案**：
1. **验证API密钥**：
   ```bash
   # 测试DeepSeek API
   curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
        https://api.deepseek.com/v1/models
   ```

2. **检查网络连接**：
   ```bash
   # 测试网络连通性
   ping api.deepseek.com
   curl -I https://api.deepseek.com
   ```

3. **配置代理**（如需要）：
   - 在Chrome扩展设置中配置代理
   - 或在.env文件中设置HTTP_PROXY

### 6.3 功能问题

#### Q5: 文件操作权限错误

**问题描述**：文件操作返回"权限被拒绝"

**可能原因**：
- 沙箱目录不存在或无权限
- Docker容器权限配置错误
- 文件路径超出沙箱范围

**解决方案**：
1. **检查沙箱目录**：
   ```bash
   ls -la server/test/
   # 如果不存在，创建目录
   mkdir -p server/test && chmod 755 server/test
   ```

2. **Docker权限修复**：
   ```bash
   # 重新构建容器
   docker-compose down
   docker-compose up -d --build
   ```

3. **验证路径**：
   - 确保文件路径在沙箱目录内
   - 避免使用绝对路径或../等相对路径

#### Q6: 搜索功能不可用

**问题描述**：网络搜索返回"未配置API密钥"

**解决方案**：
1. **获取Tavily API密钥**：
   - 访问https://tavily.com/注册账号
   - 获取API密钥（格式：tvly-xxx）

2. **配置密钥**：
   ```bash
   # 在.env文件中添加
   TAVILY_API_KEY=tvly-your-api-key
   ```

3. **重启服务**：
   ```bash
   # Docker方式
   docker-compose restart backend

   # 手动方式
   # 重启Python服务
   ```

### 6.4 性能问题

#### Q7: 响应速度慢

**问题描述**：AI回复需要很长时间

**优化方案**：
1. **增加Worker并发**：
   ```bash
   celery -A tasks worker --concurrency=8
   ```

2. **优化网络连接**：
   - 使用更快的网络连接
   - 配置CDN或代理加速

3. **调整超时设置**：
   ```python
   # 减少超时时间
   timeout=httpx.Timeout(15.0, connect=5.0)
   ```

#### Q8: 内存使用过高

**问题描述**：系统内存占用过多

**解决方案**：
1. **限制连接数**：
   ```python
   # 减少最大连接数
   max_connections=5
   ```

2. **定期重启Worker**：
   ```bash
   # 设置Worker自动重启
   celery -A tasks worker --max-tasks-per-child=100
   ```

3. **监控资源使用**：
   ```bash
   # 查看容器资源使用
   docker stats
   ```

---

## 7. 安全注意事项

### 7.1 API密钥安全

#### 7.1.1 密钥保护

**存储安全**：
- ✅ 使用环境变量存储密钥
- ✅ 使用.env文件（不要提交到版本控制）
- ❌ 不要在代码中硬编码密钥
- ❌ 不要在前端JavaScript中暴露密钥

**权限控制**：
```bash
# 设置.env文件权限
chmod 600 server/.env

# 确保.env文件在.gitignore中
echo "server/.env" >> .gitignore
```

#### 7.1.2 密钥轮换

**定期更换密钥**：
1. 每3-6个月更换一次API密钥
2. 发现泄露时立即更换
3. 使用API服务商的密钥管理功能

**密钥监控**：
- 监控API使用量异常
- 设置使用量告警
- 定期检查API访问日志

### 7.2 网络安全

#### 7.2.1 HTTPS配置

**生产环境HTTPS**：
```nginx
# nginx配置示例
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 7.2.2 防火墙配置

**端口访问控制**：
```bash
# 仅允许本地访问
iptables -A INPUT -p tcp --dport 5001 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 5001 -j DROP

# 允许特定IP访问
iptables -A INPUT -p tcp --dport 5001 -s 192.168.1.0/24 -j ACCEPT
```

### 7.3 文件系统安全

#### 7.3.1 沙箱限制

**路径验证**：
```python
def _validate_path(target_path: Path) -> tuple[bool, str]:
    """严格的路径验证"""
    resolved_path = target_path.resolve()
    base_resolved = base_dir.resolve()

    # 检查是否在沙箱内
    if not str(resolved_path).startswith(str(base_resolved)):
        return False, "路径超出允许范围"

    # 检查危险路径
    dangerous_paths = ['/etc', '/usr', '/var', '/sys', '/proc']
    for dangerous in dangerous_paths:
        if str(resolved_path).startswith(dangerous):
            return False, "访问系统目录被禁止"

    return True, ""
```

#### 7.3.2 文件类型限制

**允许的文件类型**：
```python
ALLOWED_EXTENSIONS = {
    '.txt', '.md', '.json', '.yaml', '.yml',
    '.py', '.js', '.html', '.css', '.xml',
    '.csv', '.log', '.conf', '.ini'
}

def validate_file_type(filename: str) -> bool:
    """验证文件类型"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS
```

### 7.4 Docker安全

#### 7.4.1 容器安全

**非root用户**：
```dockerfile
# 创建非特权用户
RUN useradd --create-home --shell /bin/bash app
USER app
```

**资源限制**：
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

#### 7.4.2 网络隔离

**内部网络**：
```yaml
# docker-compose.yml
networks:
  chrome_plus_network:
    driver: bridge
    internal: true  # 内部网络，不能访问外网
```

### 7.5 数据保护

#### 7.5.1 敏感数据处理

**数据脱敏**：
- 不要在日志中记录敏感信息
- 对用户输入进行清理和验证
- 定期清理临时文件

**数据备份**：
```bash
# 定期备份沙箱数据
tar -czf backup_$(date +%Y%m%d).tar.gz server/test/

# 加密备份
gpg --symmetric --cipher-algo AES256 backup.tar.gz
```

#### 7.5.2 隐私保护

**用户数据**：
- 不存储用户的聊天记录
- 不上传用户文件到外部服务
- 遵循最小权限原则

**日志管理**：
```python
# 配置安全的日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# 避免记录敏感信息
logger.info(f"用户请求: {message[:50]}...")  # 只记录前50个字符
```

---

## 8. 性能优化建议

### 8.1 系统性能优化

#### 8.1.1 硬件配置建议

**最低配置**：
- CPU：2核心
- 内存：4GB
- 存储：10GB可用空间
- 网络：10Mbps

**推荐配置**：
- CPU：4核心或更多
- 内存：8GB或更多
- 存储：SSD，50GB可用空间
- 网络：100Mbps或更快

#### 8.1.2 操作系统优化

**Linux系统优化**：
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化网络参数
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 1024" >> /etc/sysctl.conf
sysctl -p
```

### 8.2 应用性能优化

#### 8.2.1 FastAPI优化

**异步处理**：
```python
# 使用异步函数
@app.post("/chat")
async def chat(request: ChatRequest):
    # 异步处理逻辑
    result = await process_chat_async(request)
    return result

# 连接池优化
app.state.http_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
)
```

#### 8.2.2 Redis优化

**连接池配置**：
```python
# 优化Redis连接池
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=20,
    retry_on_timeout=True
)
```

**缓存策略**：
```python
# 缓存AI响应
@cache.memoize(timeout=3600)  # 缓存1小时
def get_ai_response(prompt_hash):
    return call_ai_api(prompt)
```

#### 8.2.3 Celery优化

**Worker配置**：
```bash
# 优化Worker设置
celery -A tasks worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=1000 \
  --time-limit=300 \
  --soft-time-limit=240
```

**任务路由**：
```python
# 任务路由配置
app.conf.task_routes = {
    'tasks.ai_task': {'queue': 'ai_queue'},
    'tasks.file_task': {'queue': 'file_queue'},
}
```

### 8.3 网络性能优化

#### 8.3.1 HTTP客户端优化

**连接复用**：
```python
# 全局HTTP客户端
class HTTPClientManager:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=50
            ),
            http2=True  # 启用HTTP/2
        )

    async def close(self):
        await self.client.aclose()
```

#### 8.3.2 WebSocket优化

**连接管理**：
```python
class OptimizedConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.heartbeat_interval = 30  # 心跳间隔

    async def start_heartbeat(self, channel_id):
        """启动心跳检测"""
        while channel_id in self.active_connections:
            try:
                await self.send_personal_message(
                    {"type": "ping"}, channel_id
                )
                await asyncio.sleep(self.heartbeat_interval)
            except Exception:
                self.disconnect(channel_id)
                break
```

### 8.4 前端性能优化

#### 8.4.1 JavaScript优化

**防抖处理**：
```javascript
// 输入防抖
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 应用到输入框
const debouncedSend = debounce(sendMessage, 300);
```

#### 8.4.2 DOM优化

**虚拟滚动**：
```javascript
// 大量消息的虚拟滚动
class VirtualScroll {
    constructor(container, itemHeight) {
        this.container = container;
        this.itemHeight = itemHeight;
        this.visibleItems = Math.ceil(container.clientHeight / itemHeight) + 2;
    }

    render(items, startIndex) {
        // 只渲染可见的消息
        const visibleItems = items.slice(startIndex, startIndex + this.visibleItems);
        this.container.innerHTML = visibleItems.map(item =>
            this.renderItem(item)
        ).join('');
    }
}
```

### 8.5 监控和调优

#### 8.5.1 性能监控

**系统监控**：
```bash
# 安装监控工具
pip install psutil prometheus-client

# 监控脚本
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"
```

**应用监控**：
```python
# 添加性能指标
from prometheus_client import Counter, Histogram, start_http_server

REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('request_duration_seconds', 'Request latency')

@REQUEST_LATENCY.time()
async def timed_endpoint():
    REQUEST_COUNT.inc()
    # 处理逻辑
```

#### 8.5.2 性能调优

**定期优化**：
1. **监控关键指标**：响应时间、内存使用、CPU使用率
2. **分析瓶颈**：使用profiling工具找出性能瓶颈
3. **优化配置**：根据监控数据调整配置参数
4. **压力测试**：定期进行负载测试

**自动化优化**：
```bash
# 自动重启脚本
#!/bin/bash
# restart_if_high_memory.sh

MEMORY_THRESHOLD=80
CURRENT_MEMORY=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')

if [ $CURRENT_MEMORY -gt $MEMORY_THRESHOLD ]; then
    echo "Memory usage is ${CURRENT_MEMORY}%, restarting services..."
    docker-compose restart backend worker
fi
```

---

## 📞 技术支持

### 获取帮助

**官方资源**：
- **GitHub仓库**：https://github.com/ZooTi9er/chrome_plus_fast
- **问题反馈**：GitHub Issues
- **文档中心**：docs/README.md

**社区支持**：
- **开发文档**：[开发设计文档](DEVELOPMENT_DESIGN_DOCUMENT.md)
- **配置指南**：[服务器配置指南](SERVER_HOST_CONFIGURATION_GUIDE.md)
- **版本信息**：[版本升级报告](VERSION_UPGRADE_REPORT_V2.1.0.md)

### 反馈问题

**问题报告格式**：
1. **环境信息**：操作系统、Chrome版本、Python版本
2. **问题描述**：详细描述遇到的问题
3. **重现步骤**：提供问题重现的具体步骤
4. **错误日志**：附上相关的错误日志
5. **期望结果**：说明期望的正确行为

**日志收集**：
```bash
# 收集系统日志
docker-compose logs --tail=100 backend > backend.log
docker-compose logs --tail=100 worker > worker.log

# 收集Chrome扩展日志
# 1. 打开Chrome开发者工具（F12）
# 2. 切换到Console标签页
# 3. 复制相关错误信息
```

---

**文档版本**：V2.1.1
**最后更新**：2025-01-04
**维护状态**：活跃维护
**适用版本**：Chrome Plus V2.1.1

---

*感谢您使用Chrome Plus V2.1.1！如有任何问题或建议，欢迎通过GitHub Issues与我们联系。*
