# Chrome Plus V2.0 部署指南

本指南详细介绍了Chrome Plus V2.0的各种部署方式，从开发环境到生产环境的完整部署流程。

## 📋 目录

- [快速开始](#快速开始)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker部署](#docker部署)
- [手动部署](#手动部署)
- [监控和维护](#监控和维护)
- [故障排除](#故障排除)

## 🚀 快速开始

### 前置要求
- **Docker & Docker Compose**: 推荐使用容器化部署
- **Python 3.10+**: 如果选择手动部署
- **Chrome 88+**: 支持Manifest V3的Chrome浏览器
- **Redis**: 消息队列和缓存 (Docker会自动提供)

### 一键部署
```bash
# 1. 克隆项目
git clone <repository-url>
cd chrome_plus

# 2. 快速验证
python3 quick_test.py

# 3. 启动V2.0服务
./start-v2.sh

# 4. 安装Chrome扩展
# 访问 chrome://extensions/ → 开启开发者模式 → 加载已解压的扩展程序
```

## 🛠️ 开发环境部署

### 方式1: 使用启动脚本 (推荐)
```bash
# 一键启动开发环境
./start-v2.sh

# 查看服务状态
./start-v2.sh status

# 查看日志
./start-v2.sh logs

# 停止服务
./start-v2.sh stop
```

### 方式2: 使用Docker开发脚本
```bash
# 使用专门的开发脚本
./scripts/docker-dev.sh

# 或手动启动
docker-compose up -d --build
```

### 开发环境配置
1. **环境变量配置**
   ```bash
   # 复制环境配置文件
   cp server/.env.example server/.env
   
   # 编辑配置文件
   vim server/.env
   ```

2. **必要的环境变量**
   ```bash
   # 基础配置
   ENVIRONMENT=development
   DEBUG=true
   
   # Redis配置
   REDIS_URL=redis://localhost:6379/0
   
   # AI API配置 (可选)
   DEEPSEEK_API_KEY=sk-your-deepseek-key
   OPENAI_API_KEY=sk-your-openai-key
   ```

3. **验证部署**
   ```bash
   # 快速验证
   python3 quick_test.py
   
   # 架构测试
   python3 server/test_v2_architecture.py
   
   # 综合测试
   python3 test_chrome_plus_v2.py
   ```

## 🏭 生产环境部署

### Docker生产部署 (推荐)

1. **准备生产配置**
   ```bash
   # 创建生产环境配置
   cp server/.env.example server/.env.prod
   
   # 编辑生产配置
   vim server/.env.prod
   ```

2. **生产环境变量**
   ```bash
   # 基础配置
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=INFO
   
   # 安全配置
   SECRET_KEY=your-production-secret-key
   
   # Redis配置
   REDIS_URL=redis://redis:6379/0
   
   # AI API配置
   DEEPSEEK_API_KEY=sk-your-production-deepseek-key
   OPENAI_API_KEY=sk-your-production-openai-key
   
   # 性能配置
   WORKER_CONCURRENCY=8
   TASK_TIME_LIMIT=600
   ```

3. **创建生产Docker Compose**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   
   services:
     redis:
       image: redis:7-alpine
       restart: unless-stopped
       volumes:
         - redis_prod_data:/data
       command: redis-server --appendonly yes
   
     backend:
       build:
         context: ./server
         dockerfile: Dockerfile
       restart: unless-stopped
       ports:
         - "5001:5001"
       environment:
         - ENVIRONMENT=production
       env_file:
         - server/.env.prod
       depends_on:
         - redis
   
     worker:
       build:
         context: ./server
         dockerfile: Dockerfile
       restart: unless-stopped
       command: celery -A tasks worker --loglevel=info --concurrency=8
       env_file:
         - server/.env.prod
       depends_on:
         - redis
         - backend
   
     flower:
       build:
         context: ./server
         dockerfile: Dockerfile
       restart: unless-stopped
       command: celery -A tasks flower --port=5555
       ports:
         - "5555:5555"
       env_file:
         - server/.env.prod
       depends_on:
         - redis
         - worker
   
   volumes:
     redis_prod_data:
   ```

4. **启动生产服务**
   ```bash
   # 启动生产环境
   docker-compose -f docker-compose.prod.yml up -d --build
   
   # 查看服务状态
   docker-compose -f docker-compose.prod.yml ps
   
   # 查看日志
   docker-compose -f docker-compose.prod.yml logs -f
   ```

### 反向代理配置 (Nginx)

```nginx
# /etc/nginx/sites-available/chrome-plus
server {
    listen 80;
    server_name your-domain.com;
    
    # API服务
    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
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
    
    # 任务监控
    location /flower/ {
        proxy_pass http://localhost:5555/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🐳 Docker部署详解

### 服务架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chrome扩展    │◄──►│   API网关       │◄──►│   Redis消息队列  │
│   (前端)        │    │   (FastAPI)     │    │   (消息/缓存)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲                       ▲
                                │                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Celery Worker │◄──►│   Flower监控    │
                       │   (任务处理)     │    │   (任务监控)     │
                       └─────────────────┘    └─────────────────┘
```

### 容器说明
- **redis**: 消息队列和缓存服务
- **backend**: FastAPI API网关，处理WebSocket和HTTP请求
- **worker**: Celery任务处理器，处理AI请求
- **flower**: Celery任务监控界面

### 数据持久化
```bash
# 查看数据卷
docker volume ls | grep chrome_plus

# 备份Redis数据
docker run --rm -v chrome_plus_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .

# 恢复Redis数据
docker run --rm -v chrome_plus_redis_data:/data -v $(pwd):/backup alpine tar xzf /backup/redis-backup.tar.gz -C /data
```

## 🔧 手动部署

### 1. 安装依赖
```bash
# 安装Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                 # macOS

# 安装Python依赖
cd server
pip install -r requirements.txt
# 或使用uv: uv sync
```

### 2. 启动Redis
```bash
# 启动Redis服务
redis-server

# 或作为后台服务
sudo systemctl start redis-server
```

### 3. 启动后端服务
```bash
# 启动FastAPI服务
cd server
python main.py

# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

### 4. 启动Celery Worker
```bash
# 新终端窗口
cd server
celery -A tasks worker --loglevel=info --concurrency=4
```

### 5. 启动Flower监控 (可选)
```bash
# 新终端窗口
cd server
celery -A tasks flower --port=5555
```

## 📊 监控和维护

### 服务监控
```bash
# 查看服务状态
./start-v2.sh status

# 查看实时日志
./start-v2.sh logs

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f redis
```

### 健康检查
```bash
# API健康检查
curl http://localhost:5001/health

# WebSocket连接测试
wscat -c ws://localhost:5001/ws

# Redis连接测试
redis-cli ping
```

### 性能监控
```bash
# 查看容器资源使用
docker stats

# 查看任务队列状态
# 访问 http://localhost:5555 (Flower界面)

# 查看Redis状态
redis-cli info
```

### 日志管理
```bash
# 查看日志大小
docker-compose logs --tail=100 backend

# 清理日志
docker-compose down
docker system prune -f

# 配置日志轮转
# 在docker-compose.yml中添加logging配置
```

## 🔧 故障排除

### 常见问题

#### 1. WebSocket连接失败
```bash
# 检查后端服务
curl http://localhost:5001/health

# 检查WebSocket端口
netstat -tlnp | grep 5001

# 查看后端日志
docker-compose logs -f backend
```

#### 2. Celery任务不执行
```bash
# 检查Worker状态
docker-compose ps worker

# 查看Worker日志
docker-compose logs -f worker

# 检查Redis连接
docker-compose exec redis redis-cli ping
```

#### 3. 服务启动失败
```bash
# 检查端口占用
lsof -i :5001
lsof -i :6379

# 检查Docker状态
docker-compose ps
docker-compose logs
```

#### 4. Chrome扩展加载失败
```bash
# 验证文件完整性
python3 quick_test.py

# 检查manifest.json
python3 -m json.tool manifest.json

# 查看Chrome扩展错误
# 在chrome://extensions/页面查看错误信息
```

### 性能优化

#### 1. Worker并发调优
```bash
# 根据CPU核心数调整Worker并发
# 在.env中设置
WORKER_CONCURRENCY=8  # 推荐为CPU核心数的2倍
```

#### 2. Redis内存优化
```bash
# 在docker-compose.yml中添加Redis配置
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

#### 3. 任务超时配置
```bash
# 在.env中设置任务超时
TASK_TIME_LIMIT=300      # 5分钟硬超时
TASK_SOFT_TIME_LIMIT=240 # 4分钟软超时
```

### 备份和恢复

#### 1. 配置备份
```bash
# 备份配置文件
tar czf chrome-plus-config-$(date +%Y%m%d).tar.gz server/.env* docker-compose*.yml
```

#### 2. 数据备份
```bash
# 备份Redis数据
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb
```

#### 3. 完整备份
```bash
# 创建完整备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_$DATE"

mkdir -p $BACKUP_DIR
cp -r server/.env* $BACKUP_DIR/
cp docker-compose*.yml $BACKUP_DIR/
docker-compose exec redis redis-cli BGSAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb $BACKUP_DIR/

tar czf chrome-plus-backup-$DATE.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "备份完成: chrome-plus-backup-$DATE.tar.gz"
```

---

## 📞 获取帮助

如果在部署过程中遇到问题：

1. **查看日志**: `./start-v2.sh logs`
2. **运行测试**: `python3 quick_test.py`
3. **检查文档**: [故障排除指南](TROUBLESHOOTING.md)
4. **提交Issue**: [GitHub Issues](https://github.com/your-repo/issues)

**Chrome Plus V2.0** - 让部署变得简单高效！ 🚀
