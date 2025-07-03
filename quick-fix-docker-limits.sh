#!/bin/bash

# 快速修复Docker拉取限制 - 立即解决方案

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

# 快速配置阿里云镜像源
quick_setup_aliyun_mirror() {
    log_info "快速配置阿里云镜像源..."
    
    local docker_config_dir="$HOME/.docker"
    local daemon_json="$docker_config_dir/daemon.json"
    
    # 备份现有配置
    if [ -f "$daemon_json" ]; then
        cp "$daemon_json" "$daemon_json.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # 创建配置目录
    mkdir -p "$docker_config_dir"
    
    # 配置阿里云镜像源
    cat > "$daemon_json" << 'EOF'
{
  "registry-mirrors": [
    "https://registry.cn-hangzhou.aliyuncs.com",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "experimental": false,
  "debug": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "features": {
    "buildkit": true
  }
}
EOF
    
    log_success "已配置阿里云等镜像源"
}

# 重启Docker Desktop
restart_docker_desktop() {
    log_info "重启Docker Desktop..."
    
    # 检查Docker Desktop是否运行
    if pgrep -f "Docker Desktop" > /dev/null; then
        log_info "正在停止Docker Desktop..."
        osascript -e 'quit app "Docker Desktop"'
        sleep 3
    fi
    
    # 启动Docker Desktop
    log_info "正在启动Docker Desktop..."
    open -a "Docker Desktop"
    
    # 等待Docker启动
    log_info "等待Docker Desktop启动..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker info &> /dev/null; then
            log_success "Docker Desktop已启动"
            return 0
        fi
        
        if [ $((attempt % 5)) -eq 0 ]; then
            log_info "等待Docker启动... ($attempt/$max_attempts)"
        fi
        
        sleep 2
        ((attempt++))
    done
    
    log_error "Docker Desktop启动超时"
    return 1
}

# 预拉取所需镜像
pre_pull_images() {
    log_info "预拉取Chrome Plus所需镜像..."
    
    local images=(
        "redis:7-alpine"
        "python:3.11-slim"
    )
    
    for image in "${images[@]}"; do
        log_info "拉取镜像: $image"
        if docker pull "$image"; then
            log_success "✅ 成功拉取: $image"
        else
            log_error "❌ 拉取失败: $image"
            return 1
        fi
    done
    
    log_success "所有镜像拉取完成"
}

# 启动Chrome Plus服务
start_chrome_plus() {
    log_info "启动Chrome Plus V2.0服务..."
    
    if [ ! -f "docker-compose.yml" ]; then
        log_error "未找到docker-compose.yml文件"
        return 1
    fi
    
    # 停止现有服务
    docker compose down --remove-orphans 2>/dev/null || true
    
    # 启动服务
    if docker compose up -d --build; then
        log_success "Chrome Plus V2.0服务启动成功"
        
        # 等待服务就绪
        log_info "等待服务就绪..."
        sleep 15
        
        # 检查服务状态
        docker compose ps
        
        return 0
    else
        log_error "服务启动失败"
        return 1
    fi
}

# 显示解决方案选项
show_quick_solutions() {
    echo ""
    log_info "=== 快速解决方案 ==="
    echo ""
    echo "1. 配置阿里云镜像源并重启Docker (推荐)"
    echo "2. 仅重启Docker Desktop"
    echo "3. 手动拉取镜像后启动"
    echo "4. 使用完整镜像源配置脚本"
    echo "5. 退出"
    echo ""
    read -p "请选择解决方案 (1-5): " choice
    
    case $choice in
        1)
            solution_aliyun_mirror
            ;;
        2)
            solution_restart_only
            ;;
        3)
            solution_manual_pull
            ;;
        4)
            solution_full_config
            ;;
        5)
            log_info "退出脚本"
            exit 0
            ;;
        *)
            log_error "无效选择"
            show_quick_solutions
            ;;
    esac
}

# 解决方案1：配置阿里云镜像源
solution_aliyun_mirror() {
    log_info "=== 执行阿里云镜像源配置 ==="
    
    quick_setup_aliyun_mirror
    
    if restart_docker_desktop; then
        if pre_pull_images; then
            start_chrome_plus
        else
            log_error "镜像拉取失败，请检查网络连接"
        fi
    else
        log_error "Docker重启失败"
    fi
}

# 解决方案2：仅重启Docker
solution_restart_only() {
    log_info "=== 仅重启Docker Desktop ==="
    
    if restart_docker_desktop; then
        start_chrome_plus
    else
        log_error "Docker重启失败"
    fi
}

# 解决方案3：手动拉取镜像
solution_manual_pull() {
    log_info "=== 手动拉取镜像 ==="
    
    if pre_pull_images; then
        start_chrome_plus
    else
        log_error "镜像拉取失败"
        show_quick_solutions
    fi
}

# 解决方案4：使用完整配置脚本
solution_full_config() {
    log_info "=== 使用完整镜像源配置脚本 ==="
    
    if [ -f "setup-docker-mirrors.sh" ]; then
        ./setup-docker-mirrors.sh
    else
        log_error "未找到setup-docker-mirrors.sh脚本"
        log_info "请先运行完整的镜像源配置脚本"
    fi
}

# 显示当前状态
show_current_status() {
    echo ""
    log_info "=== 当前状态检查 ==="
    echo ""
    
    # 检查Docker状态
    if docker info &> /dev/null; then
        log_success "✅ Docker运行正常"
        
        # 显示镜像源配置
        echo ""
        log_info "当前镜像源配置:"
        docker info | grep -A 10 "Registry Mirrors" || log_warning "未配置镜像源"
        
    else
        log_error "❌ Docker未运行"
    fi
    
    echo ""
    
    # 检查镜像
    log_info "检查本地镜像:"
    docker images | grep -E "(python|redis)" || log_warning "未找到相关镜像"
    
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "=== Docker拉取限制快速修复脚本 ==="
    echo ""
    
    # 显示问题描述
    log_error "检测到的问题:"
    echo "❌ Docker Hub拉取限制: toomanyrequests"
    echo "❌ USTC镜像源不可用: dial tcp: lookup docker.mirrors.ustc.edu.cn: no such host"
    echo ""
    
    # 显示当前状态
    show_current_status
    
    # 显示解决方案
    show_quick_solutions
}

# 运行主函数
main "$@"
