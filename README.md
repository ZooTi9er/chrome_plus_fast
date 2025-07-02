# Chrome扩展AI助手 🤖

[![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-blue?logo=google-chrome)](https://chrome.google.com/webstore)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个功能强大的Chrome扩展，集成AI助手功能，支持智能对话、文件操作、Markdown渲染和代码高亮。基于Chrome Manifest V3和FastAPI构建。

![Chrome扩展AI助手演示](images/demo-screenshot.png)

## ✨ 主要特性

### 🎯 核心功能
- **🤖 智能对话**: 集成DeepSeek AI模型，支持多轮对话
- **📁 文件操作**: 在安全沙箱环境中进行文件管理
- **📝 Markdown渲染**: 完整支持Markdown格式显示
- **🎨 代码高亮**: 多种编程语言语法高亮
- **⚙️ 灵活配置**: 自定义API端点和模型参数

### 🌍 代理功能 (NEW!)
- **🚀 地理位置限制解决**: 完美解决 "User location is not supported" 错误
- **🔧 多协议支持**: HTTP、HTTPS、SOCKS5代理协议
- **🔐 认证机制**: 完整的用户名/密码认证支持
- **🧪 连接测试**: 一键测试代理连接状态和可用性
- **📋 预设配置**: 常用代理配置快速应用
- **💾 配置管理**: 支持配置文件导入/导出功能
- **📊 状态监控**: 实时代理连接状态指示器

### 🛡️ 安全特性
- **🔒 安全存储**: API密钥加密存储
- **🚧 沙箱隔离**: 文件操作限制在安全目录
- **🛡️ 输入验证**: 完善的输入清理和验证
- **🔐 CORS保护**: 严格的跨域请求控制

### 🚀 技术亮点
- **Chrome Manifest V3**: 最新扩展标准
- **FastAPI后端**: 高性能异步API服务
- **现代化UI**: 响应式设计，支持暗色主题
- **完整测试**: 自动化和手动测试覆盖

## 🎬 快速演示

```bash
# 1. 一键安装
git clone <repository-url> && cd chrome_plus
chmod +x scripts/dev-setup.sh && ./scripts/dev-setup.sh

# 2. 配置API密钥
echo "DEEPSEEK_API_KEY=sk-your-key" > server/.env

# 3. 启动服务
./start-dev.sh

# 4. 在Chrome中加载扩展 (chrome://extensions/)
```

## 📚 文档导航

| 文档 | 描述 | 适用人群 |
|------|------|----------|
| [🚀 快速开始](QUICK_START.md) | 5分钟快速安装指南 | 所有用户 |
| [🌍 代理功能指南](PROXY_USER_GUIDE.md) | 解决地理位置限制问题 | 所有用户 |
| [📖 代理功能详解](PROXY_FEATURE_README.md) | 代理功能技术说明 | 开发者 |
| [🎬 代理功能演示](PROXY_DEMO.md) | 完整功能演示文档 | 所有用户 |
| [📖 开发者指南](DEVELOPER_GUIDE.md) | 完整的开发文档 | 开发者 |
| [🏗️ 架构设计](ARCHITECTURE.md) | 系统架构说明 | 架构师 |
| [📋 更新日志](CHANGELOG.md) | 版本更新记录 | 所有用户 |
| [🔧 Flask迁移指南](server/FASTAPI_MIGRATION.md) | Flask到FastAPI迁移 | 开发者 |

## 🛠️ 技术栈

### 前端 (Chrome扩展)
- **Chrome Extension API**: Manifest V3
- **JavaScript**: ES6+ 现代语法
- **CSS3**: 响应式设计
- **marked.js**: Markdown渲染
- **highlight.js**: 代码语法高亮

### 后端 (API服务)
- **FastAPI**: 现代Python Web框架
- **pydantic-ai**: AI模型集成
- **uvicorn**: ASGI服务器
- **pydantic**: 数据验证
- **python-dotenv**: 环境变量管理
- **httpx**: HTTP客户端，支持代理
- **socksio**: SOCKS5代理支持

### AI集成
- **DeepSeek API**: 主要AI模型
- **兼容OpenAI API**: 支持多种模型
- **流式响应**: 实时对话体验

## 📦 项目结构

```
chrome_plus/
├── 📄 manifest.json          # Chrome扩展配置
├── 🎨 sidepanel.html         # 主界面
├── 💅 sidepanel.css          # 样式文件
├── ⚙️ background.js          # 后台服务
├── 💬 chat.js                # 聊天逻辑
├── 🔌 api.js                 # API通信
├── 🖼️ images/                # 图标资源
├── 🚀 scripts/               # 构建脚本
│   ├── dev-setup.sh          # 开发环境设置
│   └── build-extension.sh    # 扩展打包
└── 🖥️ server/                # 后端服务
    ├── main.py               # FastAPI应用
    ├── config.py             # 配置管理
    ├── start_server.py       # 启动脚本
    └── test/                 # 沙箱目录
```

## 🚀 快速开始

### 前置要求
- Chrome 88+
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) 包管理器

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd chrome_plus
   ```

2. **自动安装**
   ```bash
   chmod +x scripts/dev-setup.sh
   ./scripts/dev-setup.sh
   ```

3. **配置API密钥**
   ```bash
   # 编辑 server/.env 文件
   DEEPSEEK_API_KEY=sk-your-actual-api-key
   ```

4. **启动服务**
   ```bash
   ./start-dev.sh
   ```

5. **安装Chrome扩展**
   - 访问 `chrome://extensions/`
   - 开启开发者模式
   - 加载项目目录

详细安装指南请参考 [快速开始文档](QUICK_START.md)。

## 🎯 使用方法

### 基础对话
1. 点击Chrome工具栏中的扩展图标
2. 在侧边栏输入框中输入消息
3. 按Enter或点击发送按钮
4. 查看AI助手的回复

### 文件操作
```
创建文件: "请创建一个名为test.txt的文件"
读取文件: "请读取test.txt的内容"
列出文件: "显示当前目录的文件列表"
```

### 自定义配置
1. 点击设置按钮 ⚙️
2. 配置API端点和密钥
3. 选择AI模型
4. 保存设置

## 🧪 测试

### 自动化测试
```bash
cd server
uv run python -m pytest test_fastapi.py -v
```

### 手动测试
```bash
./test-all.sh
```

### API测试
```bash
curl -X POST "http://127.0.0.1:5001/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

## 📦 构建和发布

### 开发构建
```bash
./start-dev.sh
```

### 生产构建
```bash
./scripts/build-extension.sh
```

### Chrome Web Store发布
1. 运行构建脚本生成zip包
2. 访问 [Chrome开发者控制台](https://chrome.google.com/webstore/devconsole)
3. 上传zip包并填写信息
4. 提交审核

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

详细指南请参考 [开发者文档](DEVELOPER_GUIDE.md)。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Chrome Extensions](https://developer.chrome.com/docs/extensions/) - 扩展开发平台
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [DeepSeek](https://platform.deepseek.com/) - AI模型服务
- [marked.js](https://marked.js.org/) - Markdown解析器
- [highlight.js](https://highlightjs.org/) - 代码高亮库

## 📞 联系我们

- 🐛 **问题报告**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **讨论交流**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 **邮件联系**: your-email@example.com

## 🌟 Star History

如果这个项目对您有帮助，请给我们一个 ⭐️！

[![Star History Chart](https://api.star-history.com/svg?repos=your-username/chrome_plus&type=Date)](https://star-history.com/#your-username/chrome_plus&Date)

---

<div align="center">

**🚀 开始使用Chrome扩展AI助手，让AI成为您的得力助手！**

[快速开始](QUICK_START.md) • [开发文档](DEVELOPER_GUIDE.md) • [问题反馈](https://github.com/your-repo/issues)

</div>
