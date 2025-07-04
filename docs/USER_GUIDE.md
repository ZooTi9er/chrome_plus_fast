# Chrome Plus V2.0 用户使用指南

## 📋 文档信息

| 项目名称 | Chrome Plus V2.1 用户指南 |
|---------|-------------------------|
| 版本 | 2.1.0稳定版 |
| 目标用户 | 最终用户 |
| 最后更新 | 2025-01-04 |
| 文档类型 | 用户使用说明文档 |

## 🎯 产品介绍

Chrome Plus V2.1稳定版是一款智能AI助手Chrome扩展，为您提供便捷的AI聊天体验和强大的文件操作功能。通过侧边栏界面，您可以与AI进行实时对话，执行文件操作，进行网络搜索，享受流畅的智能助手服务。

### ✨ 核心特性

- **🤖 智能AI对话**：支持自然语言交互，理解上下文
- **📁 文件操作工具**：15+种文件和目录操作功能
- **🌐 网络搜索**：实时信息检索和智能摘要
- **⚡ 实时通信**：WebSocket实时响应，HTTP降级保障
- **🛡️ 安全可靠**：沙箱环境，安全隔离
- **🎨 用户友好**：侧边栏设计，不干扰浏览

## 📖 目录

1. [快速开始](#1-快速开始)
2. [安装配置](#2-安装配置)
3. [功能使用](#3-功能使用)
4. [高级功能](#4-高级功能)
5. [常见问题](#5-常见问题)
6. [故障排除](#6-故障排除)

---

## 1. 快速开始

### 1.1 系统要求

- **Chrome浏览器**：版本88或更高
- **网络连接**：稳定的互联网连接
- **系统支持**：Windows、macOS、Linux

### 1.2 三步快速启动

#### 步骤1：获取扩展
下载Chrome Plus V2.1稳定版扩展包并解压到本地目录

#### 步骤2：安装扩展
1. 打开Chrome浏览器
2. 访问 `chrome://extensions/`
3. 开启右上角的"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择扩展目录

#### 步骤3：启动服务
```bash
# 方法1：直接运行（推荐新手）
cd server
python main.py

# 方法2：Docker运行（推荐进阶用户）
docker-compose up -d
```

### 1.3 验证安装

1. **检查扩展**：Chrome工具栏出现Chrome Plus图标
2. **测试连接**：点击图标打开侧边栏
3. **发送消息**：输入"你好"测试AI响应

---

## 2. 安装配置

### 2.1 Chrome扩展安装

#### 详细安装步骤

1. **下载扩展包**
   - 获取Chrome Plus V2.0扩展文件
   - 解压到易于访问的目录

2. **加载扩展**
   ```
   1. 打开Chrome浏览器
   2. 地址栏输入：chrome://extensions/
   3. 右上角开启"开发者模式"开关
   4. 点击"加载已解压的扩展程序"按钮
   5. 浏览并选择扩展目录
   6. 点击"选择文件夹"
   ```

3. **确认安装**
   - 扩展列表中出现"Chrome Plus V2.1"
   - 工具栏显示扩展图标
   - 状态显示为"已启用"

### 2.2 后端服务配置

#### 方法1：Python直接运行

**环境准备**：
```bash
# 确保Python 3.10+已安装
python --version

# 进入服务器目录
cd server

# 安装依赖（推荐使用uv）
pip install uv
uv venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows
uv pip install -r requirements.txt
```

**启动服务**：
```bash
# 启动开发服务器
python main.py

# 看到以下信息表示启动成功：
# Chrome Plus V2.0 后端服务启动中...
# 后端服务启动完成
# INFO: Uvicorn running on http://127.0.0.1:5001
```

#### 方法2：Docker部署

**环境准备**：
```bash
# 确保Docker已安装
docker --version
docker-compose --version
```

**启动服务**：
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 可选：查看Celery任务监控
# 访问 http://localhost:5555 查看任务执行情况
```

### 2.3 API密钥配置（可选但推荐）

#### DeepSeek API配置

1. **获取API密钥**
   - 访问 [DeepSeek官网](https://platform.deepseek.com/)
   - 注册账号并获取API密钥

2. **配置密钥**
   ```bash
   # 创建环境变量文件
   cd server
   cp .env.example .env
   
   # 编辑.env文件，添加：
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   ```

#### Tavily搜索API配置（可选）

1. **获取API密钥**
   - 访问 [Tavily官网](https://tavily.com/)
   - 注册账号并获取API密钥

2. **配置密钥**
   ```bash
   # 在.env文件中添加：
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

**注意**：
- 不配置API密钥时，系统会运行在测试模式
- 配置API密钥后可享受完整的AI功能
- 网络搜索功能需要Tavily API密钥

### 2.4 服务架构说明

Chrome Plus V2.1稳定版 使用Docker Compose编排多个服务：

#### 核心服务
- **backend**: FastAPI主服务（端口5001）
- **redis**: 消息队列和缓存（端口6379）

#### 可选服务
- **worker**: Celery异步任务处理器
- **flower**: Celery任务监控界面（端口5555）

#### 服务管理命令
```bash
# 启动所有服务
docker-compose up -d

# 仅启动核心服务（backend + redis）
docker-compose up -d backend redis

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart backend

# 查看服务日志
docker-compose logs -f backend
docker-compose logs -f worker

# 进入容器调试
docker-compose exec backend bash
```

---

## 3. 功能使用

### 3.1 基础对话

#### 开始聊天

1. **打开扩展**
   - 点击Chrome工具栏的Chrome Plus图标
   - 侧边栏自动打开

2. **发送消息**
   - 在底部输入框输入消息
   - 按Enter键或点击发送按钮
   - AI会实时回复您的消息

3. **查看回复**
   - AI回复支持Markdown格式
   - 代码块自动语法高亮
   - 支持一键复制消息内容

#### 对话示例

```
用户：你好，请介绍一下你自己
AI：你好！我是ShellAI，一个专注于文件和目录操作的程序员助手。我可以帮助您：

🔧 **文件操作**：读取、写入、创建、删除文件和目录
🔍 **信息查询**：获取系统信息、目录结构等  
🌐 **网络搜索**：使用Tavily API进行实时信息检索

我的所有文件操作都在安全的沙箱环境中进行，确保您的系统安全。有什么我可以帮助您的吗？
```

### 3.2 文件操作功能

Chrome Plus V2.1稳定版内置了强大的文件操作工具，所有操作都在安全的沙箱环境中进行。

#### 基础文件操作

**创建和编辑文件**：
```
用户：创建一个hello.txt文件，内容是"Hello World"
AI：我来为您创建文件。
    write_file('hello.txt', 'Hello World')
    ✅ 文件 'hello.txt' 写入成功，共写入 11 字符

用户：读取hello.txt的内容
AI：read_file('hello.txt')
    📄 Hello World
```

**文件管理**：
```
用户：列出当前目录的所有文件
AI：list_files('.')
    📁 当前目录 '.' 的内容：
    - hello.txt (文件, 11 bytes, 2025-01-03 10:30:00)

用户：将hello.txt重命名为greeting.txt
AI：rename_file('hello.txt', 'greeting.txt')
    ✅ 文件 'hello.txt' 已重命名为 'greeting.txt'

用户：删除greeting.txt文件
AI：delete_file('greeting.txt')
    ✅ 文件 'greeting.txt' 已删除
```

#### 目录操作

**创建和管理目录**：
```
用户：创建一个名为projects的目录
AI：create_directory('projects')
    ✅ 目录 'projects' 创建成功

用户：显示目录树结构
AI：tree('.')
    📁 目录树结构：
    .
    └── projects/

用户：显示当前工作目录
AI：pwd()
    📍 当前AI操作的基础目录：/path/to/server/test
```

#### 高级文件操作

**文件搜索**：
```
用户：搜索所有.txt文件
AI：find_files('*.txt')
    🔍 搜索模式: *.txt
    📄 找到的文件：
    - document.txt
    - notes.txt
    - readme.txt
```

**文件比较**：
```
用户：比较file1.txt和file2.txt的差异
AI：diff_files('file1.txt', 'file2.txt')
    📊 文件差异比较：
    --- file1.txt
    +++ file2.txt
    @@ -1,3 +1,3 @@
     第一行内容
    -第二行内容
    +第二行修改内容
     第三行内容
```

**文件备份和归档**：
```
用户：备份重要文件important.txt
AI：backup_file('important.txt')
    💾 文件 'important.txt' 已成功备份到：'backups/important_20250103_103000.txt'

用户：将所有.txt文件打包为archive.zip
AI：archive_files('archive.zip', ['file1.txt', 'file2.txt'])
    📦 归档文件 'archive.zip' 创建成功，包含 2 个项目
```

### 3.3 网络搜索功能

**实时信息检索**：
```
用户：搜索2024年人工智能的最新发展
AI：tavily_search_tool('2024年人工智能的最新发展')
    🔍 搜索查询: 2024年人工智能的最新发展
    
    📝 答案摘要:
    2024年AI发展聚焦于大语言模型的突破、多模态AI技术的成熟、
    以及AI伦理治理的完善。主要趋势包括...
    
    🌐 相关链接:
    1. **2024年AI发展报告**
       🔗 https://example.com/ai-report-2024
       📄 详细分析了2024年AI技术的重要突破和应用场景
    
    2. **人工智能技术趋势**
       🔗 https://example.com/ai-trends
       📄 探讨了AI在各行业的应用前景和挑战
```

### 3.4 系统信息查询

**获取系统信息**：
```
用户：获取系统信息
AI：get_system_info()
    💻 系统信息：
    {
      "操作系统": "macOS 14.0",
      "主机名": "MacBook-Pro",
      "CPU核心数": 8,
      "总内存(GB)": 16.0,
      "当前用户": "user"
    }
```

---

## 4. 高级功能

### 4.1 连接模式

Chrome Plus V2.1稳定版支持两种通信模式：

#### WebSocket模式（推荐）
- **特点**：实时双向通信，响应速度快
- **状态显示**：侧边栏显示"WebSocket已连接"
- **自动重连**：网络中断时自动重新连接

#### HTTP模式（降级）
- **特点**：传统HTTP请求，兼容性好
- **状态显示**：侧边栏显示"HTTP模式"
- **自动切换**：WebSocket不可用时自动启用

### 4.2 代理配置

如果您的网络环境需要代理，可以配置代理设置：

```json
{
  "proxy_config": {
    "enabled": true,
    "type": "http",
    "host": "proxy.company.com",
    "port": 8080,
    "auth": {
      "username": "your_username",
      "password": "your_password"
    }
  }
}
```

### 4.3 批量操作

**批量文件处理**：
```
用户：将目录下所有.log文件移动到logs目录
AI：我来帮您批量处理文件：
    1. create_directory('logs')
    2. find_files('*.log')
    3. 逐个移动文件到logs目录
    
    ✅ 已将3个.log文件移动到logs目录
```

### 4.4 复杂任务处理

**多步骤任务**：
```
用户：帮我整理项目文件，创建合理的目录结构
AI：我来帮您整理项目文件：
    
    1. 分析当前文件类型
    2. 创建分类目录
    3. 移动文件到对应目录
    4. 生成项目结构报告
    
    📁 创建的目录结构：
    project/
    ├── src/          # 源代码文件
    ├── docs/         # 文档文件
    ├── tests/        # 测试文件
    └── assets/       # 资源文件
    
    ✅ 项目文件整理完成
```

---

## 5. 常见问题

### 5.1 安装问题

**Q: 扩展安装后图标不显示？**
A: 请检查：
1. 确认扩展已启用（在chrome://extensions/中查看）
2. 重启Chrome浏览器
3. 检查扩展是否被其他扩展隐藏

**Q: 提示"开发者模式"无法开启？**
A: 这通常是企业策略限制，请：
1. 联系IT管理员获取权限
2. 或使用个人Chrome浏览器

### 5.2 连接问题

**Q: 显示"连接失败"怎么办？**
A: 请按以下步骤排查：
1. 确认后端服务已启动（访问 http://127.0.0.1:5001/health）
2. 检查防火墙是否阻止了5001端口
3. 确认没有其他程序占用5001端口
4. 系统会自动切换到HTTP模式，功能不受影响

**Q: WebSocket连接不稳定？**
A: 这是正常现象，系统设计了智能降级：
1. WebSocket断开时自动切换到HTTP模式
2. 功能完全不受影响
3. 可以尝试刷新页面重新连接

### 5.3 功能问题

**Q: AI不回复或回复"测试模式"？**
A: 这表示未配置API密钥：
1. 获取DeepSeek API密钥
2. 在server/.env文件中配置DEEPSEEK_API_KEY
3. 重启后端服务

**Q: 文件操作提示"路径超出范围"？**
A: 这是安全限制：
1. 所有文件操作仅限于./test/目录
2. 使用相对路径，如"document.txt"而不是"/home/user/document.txt"
3. 这是为了保护您的系统安全

**Q: 网络搜索功能不可用？**
A: 需要配置Tavily API密钥：
1. 获取Tavily API密钥
2. 在server/.env文件中配置TAVILY_API_KEY
3. 重启后端服务

### 5.4 性能问题

**Q: 响应速度较慢？**
A: 可能的原因和解决方案：
1. **网络延迟**：检查网络连接质量
2. **API限制**：DeepSeek API可能有速率限制
3. **服务器负载**：重启后端服务
4. **代理设置**：如使用代理，检查代理性能

**Q: 内存使用过高？**
A: 正常情况下内存使用应该很低：
1. 重启Chrome浏览器
2. 重启后端服务
3. 检查是否有内存泄漏

---

## 6. 故障排除

### 6.1 诊断步骤

#### 步骤1：基础检查
```bash
# 检查服务状态
curl http://127.0.0.1:5001/health

# 预期响应：
{
  "status": "healthy",
  "version": "2.1.0",
  "features": {
    "intelligent_agent": "enabled",
    "file_operations": "enabled",
    "network_search": "enabled",
    "ai_api": "enabled"
  }
}
```

#### 步骤2：测试API
```bash
# 测试聊天功能
curl -X POST http://127.0.0.1:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 预期响应：
{
  "response": "你好！有什么可以帮助你的吗？"
}
```

#### 步骤3：检查日志
```bash
# 查看服务日志
# 如果是Python直接运行，查看终端输出
# 如果是Docker运行：
docker-compose logs -f backend
```

### 6.2 常见错误解决

**错误1：端口被占用**
```
错误信息：Address already in use
解决方案：
1. 查找占用进程：lsof -i :5001
2. 终止进程：kill -9 <PID>
3. 或更改端口：修改main.py中的端口号
```

**错误2：依赖包缺失**
```
错误信息：ModuleNotFoundError
解决方案：
1. 重新安装依赖：pip install -r requirements.txt
2. 检查Python版本：python --version（需要3.10+）
3. 使用虚拟环境：python -m venv venv
```

**错误3：权限问题**
```
错误信息：Permission denied
解决方案：
1. 检查文件权限：ls -la server/
2. 修改权限：chmod +x server/main.py
3. 使用管理员权限运行
```

### 6.3 重置和恢复

**完全重置**：
```bash
# 1. 停止所有服务
docker-compose down
# 或 Ctrl+C 停止Python进程

# 2. 清理数据
rm -rf server/test/*
rm -rf server/__pycache__

# 3. 重新启动
docker-compose up -d
# 或 python server/main.py
```

**恢复默认配置**：
```bash
# 1. 备份当前配置
cp server/.env server/.env.backup

# 2. 恢复默认配置
cp server/.env.example server/.env

# 3. 重新配置API密钥
# 编辑server/.env文件
```

### 6.4 获取帮助

如果问题仍未解决：

1. **收集信息**：
   - 错误信息截图
   - 浏览器控制台日志
   - 服务器日志
   - 系统环境信息

2. **检查文档**：
   - 重新阅读相关章节
   - 查看开发设计文档
   - 参考API文档

3. **社区支持**：
   - 提交详细的问题描述
   - 包含错误日志和环境信息
   - 说明已尝试的解决方案

---

## 🎉 开始使用

现在您已经了解了Chrome Plus V2.1稳定版的完整功能，可以开始享受智能AI助手带来的便利了！

**快速提示**：
- 💬 随时与AI对话，获取帮助和建议
- 📁 使用文件操作功能管理您的文档
- 🔍 利用网络搜索获取最新信息
- 🛡️ 所有操作都在安全环境中进行

**祝您使用愉快！** 🚀
