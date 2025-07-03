# Chrome Plus V2.0 Fast 🚀

[![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-V2.0-blue?logo=google-chrome)](https://chrome.google.com/webstore)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-orange?logo=websocket)](https://websockets.spec.whatwg.org/)
[![AI Agent](https://img.shields.io/badge/AI-Agent-purple?logo=openai)](https://openai.com/)
[![Tavily Search](https://img.shields.io/badge/Tavily-Search-blue?logo=search)](https://tavily.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Chrome Plus V2.0 Fast** - 快速部署的智能AI助手Chrome扩展，集成**文件操作工具**、**网络搜索**和**实时通信**。基于Chrome Manifest V3、FastAPI和智能体架构的轻量化解决方案。

![Chrome Plus V2.0 演示](images/demo-screenshot.png)

> 🎉 **重大升级！** V2.0版本带来了全新的实时通信体验和强大的异步处理能力！

## ✨ V2.0 核心特性

### 🚀 **全新架构升级**
- **⚡ WebSocket实时通信**: 双向实时消息传输，告别HTTP轮询
- **🔄 异步任务处理**: Celery分布式任务队列，支持长时间AI处理
- **🏗️ 微服务架构**: Redis消息队列 + FastAPI网关 + Celery Worker
- **🐳 容器化部署**: Docker Compose一键启动所有服务
- **📊 实时状态监控**: 连接状态、任务进度实时反馈

### 🎯 **智能AI功能**
- **🤖 多模型支持**: DeepSeek、OpenAI等多种AI模型
- **💬 流式响应**: 实时显示AI生成过程
- **📁 文件操作**: 安全沙箱环境中的文件管理
- **📝 Markdown渲染**: 完整支持Markdown格式显示
- **🎨 代码高亮**: 多种编程语言语法高亮

### 🌍 **网络代理功能**
- **🚀 地理限制解决**: 完美解决 "User location is not supported" 错误
- **🔧 多协议支持**: HTTP、HTTPS、SOCKS5代理协议
- **🔐 认证机制**: 完整的用户名/密码认证支持
- **🧪 连接测试**: 一键测试代理连接状态和可用性
- **📊 状态监控**: 实时代理连接状态指示器

### 🛡️ **安全与可靠性**
- **🔒 安全存储**: API密钥加密存储
- **🚧 沙箱隔离**: 文件操作限制在安全目录
- **🛡️ 输入验证**: 完善的输入清理和验证
- **🔐 CORS保护**: 严格的跨域请求控制
- **🔄 自动降级**: WebSocket失败时自动切换到HTTP模式
- **💪 容错机制**: 服务异常时的优雅处理

### 🚀 **V2.0技术亮点**
- **Chrome Manifest V3**: 最新扩展标准
- **WebSocket实时通信**: 双向实时数据传输
- **Celery分布式任务**: 异步任务处理和调度
- **Redis消息队列**: 高性能消息传递
- **Docker容器化**: 一键部署和扩展
- **微服务架构**: 可扩展的服务设计

## 🎬 V2.0 快速开始

### 🚀 一键启动 (推荐)
```bash
# 1. 克隆项目
git clone <repository-url> && cd chrome_plus

# 2. 快速验证
python3 quick_test.py

# 3. 一键启动V2.0服务
./start-v2.sh

# 4. 在Chrome中加载扩展
# 访问 chrome://extensions/ → 开启开发者模式 → 加载已解压的扩展程序
```

### 🐳 Docker方式
```bash
# 使用Docker Compose
docker-compose up -d --build

# 或使用开发脚本
./scripts/docker-dev.sh
```

### ⚙️ 配置API密钥 (可选)
```bash
# 复制环境配置文件
cp server/.env.example server/.env

# 编辑配置文件，添加你的API密钥
# DEEPSEEK_API_KEY=sk-your-deepseek-key
# OPENAI_API_KEY=sk-your-openai-key
```

## 📚 文档导航

| 文档 | 描述 | 适用人群 |
|------|------|----------|
| [📖 用户手册](docs/USER_MANUAL.md) | 完整的用户使用指南 | 所有用户 |
| [🛠️ 开发者文档](docs/DEVELOPMENT_GUIDE.md) | 完整的开发和技术文档 | 开发者 |
| [📋 更新日志](CHANGELOG.md) | 版本更新记录 | 所有用户 |

### 📖 用户手册包含内容
- 🚀 快速开始和安装指南
- 💬 基础功能使用方法
- 🌍 代理功能配置详解
- ⚙️ 高级功能和自定义配置
- ❓ 常见问题解答和故障排除

### 🛠️ 开发者文档包含内容
- 🏗️ 完整的系统架构设计
- 📝 详细的代码结构说明
- 🔌 API接口文档和数据流设计
- 🚀 开发环境搭建和部署指南
- 🧪 测试策略和代码贡献规范
- 🔧 FastAPI迁移说明和技术债务

## 🛠️ V2.0 技术栈

### 🌐 前端 (Chrome扩展)
- **Chrome Extension API**: Manifest V3
- **WebSocket Client**: 实时通信客户端
- **JavaScript**: ES6+ 现代语法，支持异步处理
- **CSS3**: 响应式设计，连接状态指示器
- **marked.js**: Markdown渲染
- **highlight.js**: 代码语法高亮

### 🖥️ 后端 (微服务架构)
#### API网关 (FastAPI)
- **FastAPI**: 现代Python Web框架，支持WebSocket
- **WebSocket**: 实时双向通信
- **uvicorn**: ASGI服务器
- **pydantic**: 数据验证和序列化

#### 任务处理 (Celery)
- **Celery**: 分布式任务队列
- **Redis**: 消息代理和结果存储
- **异步处理**: 长时间AI任务处理

#### 容器化 (Docker)
- **Docker**: 容器化部署
- **Docker Compose**: 服务编排
- **多服务架构**: Redis + FastAPI + Celery

#### AI集成
- **DeepSeek API**: 主要AI模型
- **OpenAI兼容**: 支持多种AI模型
- **流式响应**: 实时对话体验
- **代理支持**: HTTP/SOCKS5代理

## 📦 V2.0 项目结构

```
chrome_plus/
├── 📄 manifest.json              # Chrome扩展配置 (V2.0)
├── 🎨 sidepanel.html             # 主界面
├── 💅 sidepanel.css              # 样式文件
├── ⚙️ background.js              # 后台服务
├── 💬 chat.js                    # 聊天逻辑 (支持WebSocket)
├── 🔌 api.js                     # API通信 (HTTP + WebSocket)
├── 🌐 websocket-api.js           # WebSocket客户端 (NEW!)
├── 🖼️ images/                    # 图标资源
├── 🚀 scripts/                   # 脚本工具
│   ├── docker-dev.sh             # Docker开发脚本
│   └── build-extension.sh        # 扩展打包
├── 🐳 docker-compose.yml         # 服务编排配置 (NEW!)
├── 🚀 start-v2.sh                # V2.0启动脚本 (NEW!)
├── 🧪 quick_test.py              # 快速验证脚本 (NEW!)
├── 🧪 test_chrome_plus_v2.py     # 综合测试脚本 (NEW!)
├── 📚 UPGRADE_COMPLETE.md        # 升级完成文档 (NEW!)
└── 🖥️ server/                    # 后端服务
    ├── main.py                   # FastAPI应用 (支持WebSocket)
    ├── tasks.py                  # Celery任务处理 (NEW!)
    ├── Dockerfile                # 容器配置 (NEW!)
    ├── pyproject.toml            # 依赖配置 (更新)
    ├── .env.example              # 环境配置示例
    ├── test_v2_architecture.py   # 架构测试 (NEW!)
    └── test/                     # 沙箱目录
```

## 🚀 V2.0 安装指南

### 📋 前置要求
- **Chrome 88+**: 支持Manifest V3
- **Python 3.10+**: 后端运行环境
- **Docker & Docker Compose**: 容器化部署 (推荐)
- **uv**: Python包管理器 (可选)

### ⚡ 快速安装 (推荐)

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd chrome_plus
   ```

2. **快速验证**
   ```bash
   python3 quick_test.py
   ```

3. **一键启动V2.0**
   ```bash
   ./start-v2.sh
   ```

4. **安装Chrome扩展**
   - 访问 `chrome://extensions/`
   - 开启"开发者模式"
   - 点击"加载已解压的扩展程序"
   - 选择项目根目录

### 🐳 Docker方式 (生产推荐)

```bash
# 使用Docker Compose
docker-compose up -d --build

# 或使用开发脚本
./scripts/docker-dev.sh
```

### ⚙️ 手动安装

1. **安装Python依赖**
   ```bash
   cd server
   pip install -r requirements.txt
   # 或使用uv: uv sync
   ```

2. **配置环境变量**
   ```bash
   cp server/.env.example server/.env
   # 编辑 .env 文件，添加API密钥
   ```

3. **启动Redis (如果没有Docker)**
   ```bash
   redis-server
   ```

4. **启动后端服务**
   ```bash
   cd server
   python main.py
   ```

5. **启动Celery Worker**
   ```bash
   cd server
   celery -A tasks worker --loglevel=info
   ```

详细安装和配置指南请参考 [用户手册](docs/USER_MANUAL.md)。

## 🎯 V2.0 使用方法

### 🚀 实时对话体验
1. 点击Chrome工具栏中的扩展图标
2. 查看连接状态指示器 (WebSocket/HTTP)
3. 在侧边栏输入框中输入消息
4. 享受实时响应和状态反馈
5. 查看AI助手的流式回复

### 📁 智能文件操作
```
创建文件: "请创建一个名为test.txt的文件"
读取文件: "请读取test.txt的内容"
列出文件: "显示当前目录的文件列表"
修改文件: "请在test.txt中添加一行内容"
```

### ⚙️ 高级配置
1. 点击设置按钮 ⚙️
2. 配置自定义API端点和密钥
3. 选择AI模型 (DeepSeek/OpenAI)
4. 配置代理设置 (如需要)
5. 保存设置并测试连接

### 🌍 代理配置
1. 在设置中启用代理功能
2. 选择代理类型 (HTTP/SOCKS5)
3. 输入代理服务器信息
4. 测试代理连接
5. 享受无地域限制的AI服务

## 🧪 V2.0 测试套件

### 🚀 快速验证
```bash
# 验证所有组件
python3 quick_test.py

# 启动并测试
./start-v2.sh test
```

### 🏗️ 架构测试
```bash
# 测试WebSocket和Celery
python3 server/test_v2_architecture.py

# 综合测试
python3 test_chrome_plus_v2.py
```

### 🔧 服务测试
```bash
# 检查服务状态
./start-v2.sh status

# 查看服务日志
./start-v2.sh logs

# API健康检查
curl http://localhost:5001/health
```

### 🌐 WebSocket测试
```bash
# 使用wscat测试WebSocket连接
npm install -g wscat
wscat -c ws://localhost:5001/ws

# 发送测试消息
{"type": "chat", "data": {"message": "Hello WebSocket!"}}
```

## 📦 V2.0 构建和部署

### 🚀 开发环境
```bash
# V2.0一键启动
./start-v2.sh

# 传统方式
./scripts/docker-dev.sh
```

### 🐳 生产部署
```bash
# Docker生产环境
docker-compose -f docker-compose.prod.yml up -d

# 扩展打包
./scripts/build-extension.sh
```

### 📱 Chrome Web Store发布
1. 运行 `./scripts/build-extension.sh` 生成V2.0扩展包
2. 访问 [Chrome开发者控制台](https://chrome.google.com/webstore/devconsole)
3. 上传zip包，强调V2.0新特性
4. 提交审核

### 🔧 服务器部署
```bash
# 生产环境配置
cp server/.env.example server/.env.prod
# 编辑生产环境配置

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范
- 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范
- 确保所有测试通过
- 更新相关文档
- 代码风格一致

详细指南请参考 [开发者文档](docs/DEVELOPMENT_GUIDE.md)。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 V2.0 致谢

### 🏗️ 核心技术
- [Chrome Extensions](https://developer.chrome.com/docs/extensions/) - 扩展开发平台
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [WebSocket](https://websockets.spec.whatwg.org/) - 实时通信协议
- [Celery](https://docs.celeryproject.org/) - 分布式任务队列
- [Redis](https://redis.io/) - 内存数据库和消息队列
- [Docker](https://www.docker.com/) - 容器化平台

### 🤖 AI服务
- [DeepSeek](https://platform.deepseek.com/) - 主要AI模型服务
- [OpenAI](https://openai.com/) - AI模型兼容支持

### 🎨 前端库
- [marked.js](https://marked.js.org/) - Markdown解析器
- [highlight.js](https://highlightjs.org/) - 代码高亮库

## 📞 联系我们

- 🐛 **问题报告**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 **邮件联系**: your-email@example.com
- 📚 **文档反馈**: 欢迎改进建议

## 🌟 Star History

如果Chrome Plus V2.0对您有帮助，请给我们一个 ⭐️！

[![Star History Chart](https://api.star-history.com/svg?repos=your-username/chrome_plus&type=Date)](https://star-history.com/#your-username/chrome_plus&Date)

---

<div align="center">

**🚀 体验Chrome Plus V2.0，享受下一代AI助手的强大功能！**

[📖 用户手册](docs/USER_MANUAL.md) • [🛠️ 开发者文档](docs/DEVELOPMENT_GUIDE.md) • [🎉 升级指南](UPGRADE_COMPLETE.md) • [🐛 问题反馈](https://github.com/your-repo/issues)

**WebSocket实时通信 • 异步任务处理 • 微服务架构 • 容器化部署**

</div>
