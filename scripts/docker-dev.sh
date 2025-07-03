#!/bin/bash

# Chrome Plus V2.0 Docker开发环境启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 检查环境文件
check_env_files() {
    if [ ! -f "server/.env" ]; then
        log_warning "未找到server/.env文件"
        if [ -f "server/.env.example" ]; then
            log_info "复制.env.example到.env"
            cp server/.env.example server/.env
            log_warning "请编辑server/.env文件，填入正确的API密钥"
        else
            log_error "未找到.env.example文件"
            exit 1
        fi
    fi
    
    log_success "环境文件检查完成"
}

# 构建和启动服务
start_services() {
    log_info "开始构建和启动Docker服务..."
    
    # 停止现有服务
    docker-compose down --remove-orphans
    
    # 构建镜像
    log_info "构建Docker镜像..."
    docker-compose build --no-cache
    
    # 启动服务
    log_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    check_services_health
}

# 检查服务健康状态
check_services_health() {
    log_info "检查服务健康状态..."
    
    # 检查Redis
    if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis服务正常"
    else
        log_error "Redis服务异常"
        return 1
    fi
    
    # 检查后端API
    sleep 5
    if curl -f http://localhost:5001/health &> /dev/null; then
        log_success "后端API服务正常"
    else
        log_warning "后端API服务可能还在启动中，请稍后检查"
    fi
    
    # 检查Celery Worker
    if docker-compose exec worker celery -A tasks inspect ping | grep -q "pong"; then
        log_success "Celery Worker正常"
    else
        log_warning "Celery Worker可能还在启动中"
    fi
    
    log_success "服务健康检查完成"
}

# 显示服务信息
show_service_info() {
    echo ""
    log_info "=== Chrome Plus V2.0 服务信息 ==="
    echo ""
    echo "🌐 后端API服务:     http://localhost:5001"
    echo "📊 任务监控(Flower): http://localhost:5555"
    echo "🔴 Redis服务:       localhost:6379"
    echo ""
    echo "📋 常用命令:"
    echo "  查看日志:         docker-compose logs -f"
    echo "  查看特定服务日志:  docker-compose logs -f [backend|worker|redis]"
    echo "  停止服务:         docker-compose down"
    echo "  重启服务:         docker-compose restart"
    echo "  进入容器:         docker-compose exec [backend|worker] bash"
    echo ""
    echo "🧪 测试命令:"
    echo "  测试API:          curl http://localhost:5001/health"
    echo "  测试WebSocket:    wscat -c ws://localhost:5001/ws"
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "=== Chrome Plus V2.0 Docker开发环境启动 ==="
    echo ""
    
    # 检查当前目录
    if [ ! -f "docker-compose.yml" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行检查和启动
    check_docker
    check_env_files
    start_services
    show_service_info
    
    log_success "Chrome Plus V2.0 开发环境启动完成！"
}

# 处理命令行参数
case "${1:-start}" in
    "start")
        main
        ;;
    "stop")
        log_info "停止所有服务..."
        docker-compose down
        log_success "服务已停止"
        ;;
    "restart")
        log_info "重启所有服务..."
        docker-compose restart
        log_success "服务已重启"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "clean")
        log_warning "清理所有容器和镜像..."
        docker-compose down --volumes --remove-orphans
        docker system prune -f
        log_success "清理完成"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|logs|status|clean}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动开发环境 (默认)"
        echo "  stop    - 停止所有服务"
        echo "  restart - 重启所有服务"
        echo "  logs    - 查看实时日志"
        echo "  status  - 查看服务状态"
        echo "  clean   - 清理容器和镜像"
        exit 1
        ;;
esac
