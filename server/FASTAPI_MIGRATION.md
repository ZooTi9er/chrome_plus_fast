# Flask到FastAPI迁移指南

## 🎯 迁移概述

本项目已成功从Flask迁移到FastAPI，保持了所有原有功能的同时，增加了以下优势：

- ✅ 自动API文档生成 (Swagger UI)
- ✅ 类型提示和自动验证
- ✅ 更好的性能
- ✅ 现代异步支持
- ✅ 更清晰的错误处理

## 📋 主要变更

### 1. 依赖变更
- **移除**: Flask, Flask-CORS
- **添加**: FastAPI, uvicorn

### 2. 代码变更
- 路由装饰器: `@app.route()` → `@app.post()`
- 请求处理: `request.get_json()` → Pydantic模型
- 响应处理: `jsonify()` → 直接返回Pydantic模型
- 错误处理: 自定义错误响应 → `HTTPException`

### 3. 新增功能
- 自动API文档: `/docs` 和 `/redoc`
- OpenAPI模式: `/openapi.json`
- 请求/响应模型验证
- 更好的错误信息

## 🚀 运行指南

### 方法1: 直接运行主文件
```bash
cd other/chrome_plus/server
python main.py
```

### 方法2: 使用启动脚本 (推荐)
```bash
cd other/chrome_plus/server
python start_server.py
```

### 方法3: 使用uvicorn命令
```bash
cd other/chrome_plus/server
uvicorn main:app --host 127.0.0.1 --port 5001 --reload
```

## 📚 API文档

启动服务器后，可以访问以下地址：

- **交互式API文档**: http://127.0.0.1:5001/docs
- **ReDoc文档**: http://127.0.0.1:5001/redoc
- **OpenAPI模式**: http://127.0.0.1:5001/openapi.json

## 🧪 测试

### 自动化测试
```bash
# 安装pytest (如果还没有)
pip install pytest httpx

# 运行测试
python test_fastapi.py
```

### 手动测试
```bash
# 确保服务器正在运行，然后：
python test_manual.py
```

## 🔧 配置

### 环境变量
在 `.env` 文件中设置：
```
DEEPSEEK_API_KEY=your_api_key_here
TAVILY_API_KEY=your_tavily_key_here
```

### 服务器配置
可以在 `config.py` 中修改：
- 服务器地址和端口
- CORS设置
- API信息
- 文件操作基础目录

## 🔄 与原Flask版本的兼容性

### API端点保持不变
- `POST /chat` - 聊天API端点

### 请求格式保持不变
```json
{
  "message": "用户消息"
}
```

### 响应格式保持不变
```json
{
  "response": "AI回复"
}
```

### 错误响应格式略有变化
**Flask版本**:
```json
{
  "error": "错误信息"
}
```

**FastAPI版本**:
```json
{
  "detail": "错误信息"
}
```

## 🛠️ 故障排除

### 常见问题

1. **导入错误**: 确保安装了所有依赖
   ```bash
   pip install -r requirements.txt
   ```

2. **端口占用**: 修改 `config.py` 中的端口设置

3. **CORS问题**: 检查 `config.py` 中的 `ALLOWED_ORIGINS` 设置

4. **API密钥问题**: 确保 `.env` 文件中设置了正确的API密钥

### 调试模式
启动时添加调试信息：
```bash
uvicorn main:app --host 127.0.0.1 --port 5001 --reload --log-level debug
```

## 📈 性能优化

FastAPI版本相比Flask版本有以下性能提升：
- 更快的JSON序列化/反序列化
- 自动请求验证减少错误处理开销
- 更好的异步支持（为未来扩展做准备）

## 🔮 未来扩展

FastAPI为以下功能提供了更好的支持：
- 异步文件操作
- WebSocket支持
- 后台任务
- 依赖注入
- 中间件扩展
