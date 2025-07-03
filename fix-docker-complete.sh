#!/bin/bash

# Chrome Plus V2.0 Docker完整修复脚本
# 解决镜像拉取问题和配置问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# 停止所有Docker容器和服务
stop_docker_services() {
    log_info "停止现有Docker服务..."
    
    # 停止Chrome Plus服务
    if [ -f "docker-compose.yml" ]; then
        docker compose down --remove-orphans 2>/dev/null || docker-compose down --remove-orphans 2>/dev/null || true
    fi
    
    # 停止所有运行的容器
    if [ "$(docker ps -q)" ]; then
        log_info "停止所有运行的容器..."
        docker stop $(docker ps -q) 2>/dev/null || true
    fi
    
    log_success "Docker服务已停止"
}

# 清理Docker配置（macOS）
clean_macos_docker_config() {
    log_info "清理macOS Docker Desktop配置..."
    
    DOCKER_CONFIG_DIR="$HOME/.docker"
    DAEMON_JSON="$DOCKER_CONFIG_DIR/daemon.json"
    
    # 备份现有配置
    if [ -f "$DAEMON_JSON" ]; then
        cp "$DAEMON_JSON" "$DAEMON_JSON.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置"
    fi
    
    # 创建干净的配置（不使用任何镜像源）
    mkdir -p "$DOCKER_CONFIG_DIR"
    cat > "$DAEMON_JSON" << 'EOF'
{
  "experimental": false,
  "debug": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    
    log_success "已创建干净的Docker配置"
}

# 清理Docker配置（Linux）
clean_linux_docker_config() {
    log_info "清理Linux Docker配置..."
    
    DAEMON_JSON="/etc/docker/daemon.json"
    
    # 检查权限
    if [ "$EUID" -ne 0 ]; then
        log_error "Linux系统需要root权限修改Docker配置"
        log_info "请使用: sudo $0"
        exit 1
    fi
    
    # 备份现有配置
    if [ -f "$DAEMON_JSON" ]; then
        cp "$DAEMON_JSON" "$DAEMON_JSON.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置"
    fi
    
    # 创建干净的配置
    mkdir -p /etc/docker
    cat > "$DAEMON_JSON" << 'EOF'
{
  "experimental": false,
  "debug": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    
    log_success "已创建干净的Docker配置"
}

# 重启Docker服务
restart_docker() {
    OS=$(detect_os)
    
    case "$OS" in
        "macos")
            log_warning "请手动重启Docker Desktop:"
            echo "1. 点击菜单栏的Docker图标"
            echo "2. 选择 'Restart Docker Desktop'"
            echo "3. 等待重启完成后按任意键继续..."
            read -n 1 -s
            ;;
        "linux")
            log_info "重启Docker服务..."
            systemctl daemon-reload
            systemctl restart docker
            sleep 5
            log_success "Docker服务已重启"
            ;;
        *)
            log_error "不支持的操作系统"
            exit 1
            ;;
    esac
}

# 测试Docker连接
test_docker_connection() {
    log_info "测试Docker连接..."
    
    # 等待Docker启动
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker info &> /dev/null; then
            log_success "Docker连接正常"
            return 0
        fi
        
        log_info "等待Docker启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_error "Docker连接失败"
    return 1
}

# 测试镜像拉取
test_image_pull() {
    log_info "测试镜像拉取..."
    
    # 测试拉取小镜像
    if docker pull hello-world:latest; then
        log_success "镜像拉取测试成功"
        docker rmi hello-world:latest &> /dev/null || true
        return 0
    else
        log_error "镜像拉取失败"
        return 1
    fi
}

# 清理Docker缓存
clean_docker_cache() {
    log_info "清理Docker缓存..."
    
    # 清理构建缓存
    docker builder prune -f &> /dev/null || true
    
    # 清理未使用的镜像
    docker image prune -f &> /dev/null || true
    
    # 清理未使用的容器
    docker container prune -f &> /dev/null || true
    
    log_success "Docker缓存已清理"
}

# 启动Chrome Plus服务
start_chrome_plus() {
    log_info "启动Chrome Plus V2.0服务..."
    
    if [ ! -f "docker-compose.yml" ]; then
        log_error "未找到docker-compose.yml文件"
        return 1
    fi
    
    # 尝试使用新版Docker Compose
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
    
    log_info "使用命令: $DOCKER_COMPOSE_CMD"
    
    # 启动服务
    if $DOCKER_COMPOSE_CMD up -d --build; then
        log_success "Chrome Plus V2.0服务启动成功"
        
        # 等待服务就绪
        log_info "等待服务就绪..."
        sleep 15
        
        # 检查服务状态
        $DOCKER_COMPOSE_CMD ps
        
        return 0
    else
        log_error "服务启动失败"
        return 1
    fi
}

# 显示解决方案选项
show_solutions() {
    echo ""
    log_info "=== 可选解决方案 ==="
    echo ""
    echo "1. 完全重置Docker配置（推荐）"
    echo "2. 仅清理缓存并重试"
    echo "3. 使用国外镜像源"
    echo "4. 手动拉取镜像"
    echo "5. 退出"
    echo ""
    read -p "请选择解决方案 (1-5): " choice
    
    case $choice in
        1)
            full_reset_solution
            ;;
        2)
            cache_clean_solution
            ;;
        3)
            foreign_mirror_solution
            ;;
        4)
            manual_pull_solution
            ;;
        5)
            log_info "退出脚本"
            exit 0
            ;;
        *)
            log_error "无效选择"
            show_solutions
            ;;
    esac
}

# 解决方案1：完全重置
full_reset_solution() {
    log_info "=== 执行完全重置解决方案 ==="
    
    stop_docker_services
    clean_docker_cache
    
    OS=$(detect_os)
    case "$OS" in
        "macos")
            clean_macos_docker_config
            ;;
        "linux")
            clean_linux_docker_config
            ;;
    esac
    
    restart_docker
    
    if test_docker_connection && test_image_pull; then
        start_chrome_plus
    else
        log_error "Docker测试失败，请检查网络连接"
    fi
}

# 解决方案2：清理缓存
cache_clean_solution() {
    log_info "=== 执行缓存清理解决方案 ==="
    
    stop_docker_services
    clean_docker_cache
    
    if test_docker_connection && test_image_pull; then
        start_chrome_plus
    else
        log_error "缓存清理后仍然失败"
        show_solutions
    fi
}

# 解决方案3：使用国外镜像源
foreign_mirror_solution() {
    log_info "=== 配置国外镜像源 ==="
    
    OS=$(detect_os)
    DOCKER_CONFIG_DIR="$HOME/.docker"
    DAEMON_JSON="$DOCKER_CONFIG_DIR/daemon.json"
    
    if [ "$OS" = "linux" ] && [ "$EUID" -ne 0 ]; then
        DAEMON_JSON="/etc/docker/daemon.json"
        log_error "Linux系统需要root权限"
        return 1
    fi
    
    mkdir -p "$DOCKER_CONFIG_DIR"
    cat > "$DAEMON_JSON" << 'EOF'
{
  "registry-mirrors": [
    "https://registry-1.docker.io"
  ],
  "experimental": false,
  "debug": false
}
EOF
    
    restart_docker
    
    if test_docker_connection && test_image_pull; then
        start_chrome_plus
    else
        log_error "国外镜像源配置失败"
    fi
}

# 解决方案4：手动拉取镜像
manual_pull_solution() {
    log_info "=== 手动拉取所需镜像 ==="
    
    # 从docker-compose.yml中提取镜像
    local images=(
        "redis:7-alpine"
        "python:3.11-slim"
    )
    
    for image in "${images[@]}"; do
        log_info "拉取镜像: $image"
        if docker pull "$image"; then
            log_success "成功拉取: $image"
        else
            log_error "拉取失败: $image"
            return 1
        fi
    done
    
    start_chrome_plus
}

# 主函数
main() {
    echo ""
    log_info "=== Chrome Plus V2.0 Docker完整修复脚本 ==="
    echo ""
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 显示当前问题
    log_warning "检测到的问题:"
    echo "- Docker镜像拉取失败"
    echo "- 镜像源连接问题"
    echo "- 可能的配置冲突"
    echo ""
    
    show_solutions
}

# 运行主函数
main "$@"
