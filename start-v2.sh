#!/bin/bash

# Chrome Plus V2.0 启动脚本

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

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose (支持新旧版本)
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
        log_success "检测到Docker Compose (旧版本)"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
        log_success "检测到Docker Compose (新版本)"
    else
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装，请先安装Python3"
        exit 1
    fi
    
    log_success "系统依赖检查通过"
}

# 快速验证
quick_verify() {
    log_info "运行快速验证..."
    
    if python3 quick_test.py; then
        log_success "快速验证通过"
        return 0
    else
        log_error "快速验证失败"
        return 1
    fi
}

# 启动服务
start_services() {
    log_info "启动Chrome Plus V2.0服务..."
    
    # 停止现有服务
    $DOCKER_COMPOSE_CMD down --remove-orphans 2>/dev/null || true

    # 启动服务
    if $DOCKER_COMPOSE_CMD up -d --build; then
        log_success "服务启动成功"
        
        # 等待服务就绪
        log_info "等待服务就绪..."
        sleep 15
        
        return 0
    else
        log_error "服务启动失败"
        return 1
    fi
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    # 检查容器状态
    if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
        log_success "Docker容器运行正常"
    else
        log_error "Docker容器状态异常"
        $DOCKER_COMPOSE_CMD ps
        return 1
    fi
    
    # 检查API健康状态
    log_info "检查API健康状态..."
    sleep 5
    
    if curl -f http://localhost:5001/health &> /dev/null; then
        log_success "API服务健康检查通过"
    else
        log_warning "API服务可能还在启动中，请稍后检查"
    fi
    
    return 0
}

# 显示服务信息
show_service_info() {
    echo ""
    log_info "=== Chrome Plus V2.0 服务信息 ==="
    echo ""
    echo "🌐 后端API服务:      http://localhost:5001"
    echo "📊 API健康检查:      http://localhost:5001/health"
    echo "📊 任务监控(Flower): http://localhost:5555"
    echo "🔴 Redis服务:        localhost:6379"
    echo ""
    echo "📋 常用命令:"
    echo "  查看服务状态:       $DOCKER_COMPOSE_CMD ps"
    echo "  查看日志:           $DOCKER_COMPOSE_CMD logs -f"
    echo "  查看特定服务日志:    $DOCKER_COMPOSE_CMD logs -f [backend|worker|redis]"
    echo "  停止服务:           $DOCKER_COMPOSE_CMD down"
    echo "  重启服务:           $DOCKER_COMPOSE_CMD restart"
    echo ""
    echo "🧪 测试命令:"
    echo "  快速验证:           python3 quick_test.py"
    echo "  完整测试:           python3 test_chrome_plus_v2.py"
    echo "  架构测试:           python3 server/test_v2_architecture.py"
    echo ""
    echo "🔧 Chrome扩展安装:"
    echo "  1. 打开Chrome浏览器"
    echo "  2. 访问 chrome://extensions/"
    echo "  3. 开启'开发者模式'"
    echo "  4. 点击'加载已解压的扩展程序'"
    echo "  5. 选择当前项目目录"
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "=== Chrome Plus V2.0 启动脚本 ==="
    echo ""
    
    # 检查当前目录
    if [ ! -f "docker-compose.yml" ]; then
        log_error "请在Chrome Plus项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行启动流程
    check_dependencies
    
    if ! quick_verify; then
        log_error "快速验证失败，请检查项目文件"
        exit 1
    fi
    
    if ! start_services; then
        log_error "服务启动失败"
        exit 1
    fi
    
    if ! check_services; then
        log_warning "服务状态检查有问题，但服务可能仍在启动中"
    fi
    
    show_service_info
    
    log_success "Chrome Plus V2.0 启动完成！"
    echo ""
    log_info "提示: 使用 Ctrl+C 可以查看实时日志，或运行 'docker-compose down' 停止服务"
}

# 处理命令行参数
case "${1:-start}" in
    "start")
        main
        ;;
    "stop")
        log_info "停止Chrome Plus V2.0服务..."
        ${DOCKER_COMPOSE_CMD:-docker-compose} down
        log_success "服务已停止"
        ;;
    "restart")
        log_info "重启Chrome Plus V2.0服务..."
        ${DOCKER_COMPOSE_CMD:-docker-compose} restart
        log_success "服务已重启"
        ;;
    "status")
        log_info "Chrome Plus V2.0服务状态:"
        ${DOCKER_COMPOSE_CMD:-docker-compose} ps
        echo ""
        log_info "API健康检查:"
        curl -s http://localhost:5001/health | python3 -m json.tool 2>/dev/null || echo "API服务未响应"
        ;;
    "logs")
        ${DOCKER_COMPOSE_CMD:-docker-compose} logs -f
        ;;
    "test")
        log_info "运行快速测试..."
        python3 quick_test.py
        ;;
    "clean")
        log_warning "清理所有容器和镜像..."
        ${DOCKER_COMPOSE_CMD:-docker-compose} down --volumes --remove-orphans
        docker system prune -f
        log_success "清理完成"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|test|clean}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动Chrome Plus V2.0 (默认)"
        echo "  stop    - 停止所有服务"
        echo "  restart - 重启所有服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看实时日志"
        echo "  test    - 运行快速测试"
        echo "  clean   - 清理容器和镜像"
        exit 1
        ;;
esac
