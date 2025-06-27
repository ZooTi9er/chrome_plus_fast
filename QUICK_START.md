# 🚀 快速开始指南

欢迎使用Chrome扩展AI助手！本指南将帮助您在5分钟内完成安装和配置。

## 📋 前置要求

- Chrome浏览器 88+ 
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) 包管理器

## ⚡ 一键安装

### 1. 克隆项目
```bash
git clone <repository-url>
cd chrome_plus
```

### 2. 运行安装脚本
```bash
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh
```

### 3. 配置API密钥
编辑 `server/.env` 文件：
```bash
DEEPSEEK_API_KEY=sk-your-actual-api-key-here
```

> 💡 **获取API密钥**: 访问 [DeepSeek官网](https://platform.deepseek.com/) 注册并获取免费API密钥

### 4. 启动服务
```bash
./start-dev.sh
```

### 5. 安装Chrome扩展
1. 打开Chrome浏览器
2. 访问 `chrome://extensions/`
3. 开启"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择项目根目录

## 🎯 验证安装

### 测试后端服务
```bash
curl -X POST "http://127.0.0.1:5001/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

预期响应：
```json
{"response": "你好！我是ShellAI，一个专注于文件和目录操作的助手..."}
```

### 测试Chrome扩展
1. 点击Chrome工具栏中的扩展图标
2. 在侧边栏中输入"你好"
3. 应该收到AI助手的回复

## 🔧 常见问题

### Q: 扩展无法加载
**A**: 检查manifest.json语法：
```bash
python3 -c "import json; json.load(open('manifest.json'))"
```

### Q: API请求失败
**A**: 确认服务器运行状态：
```bash
curl http://127.0.0.1:5001/docs
```

### Q: 没有API密钥
**A**: 
1. 访问 [DeepSeek官网](https://platform.deepseek.com/)
2. 注册账号（免费）
3. 创建API密钥
4. 复制到 `server/.env` 文件

## 📚 下一步

- 📖 阅读 [完整开发者指南](DEVELOPER_GUIDE.md)
- 🧪 运行测试: `./test-all.sh`
- 📦 构建发布包: `./scripts/build-extension.sh`
- 🔍 查看API文档: http://127.0.0.1:5001/docs

## 🆘 获取帮助

- 📋 查看 [故障排查指南](DEVELOPER_GUIDE.md#常见问题排查)
- 🐛 报告问题: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 讨论交流: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**🎉 恭喜！您已成功安装Chrome扩展AI助手！**

现在您可以：
- 💬 与AI助手聊天
- 📁 执行文件操作
- 🎨 享受Markdown和代码高亮
- ⚙️ 自定义API配置

开始探索吧！ 🚀
