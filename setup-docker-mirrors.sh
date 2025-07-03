#!/bin/bash

# Docker镜像加速器配置脚本 - 解决拉取限制和网络问题
# 支持多个中国镜像源，自动测试可用性

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

# 中国镜像源列表（按推荐程度排序）
MIRROR_SOURCES=(
    "https://registry.cn-hangzhou.aliyuncs.com|阿里云杭州"
    "https://hub-mirror.c.163.com|网易云"
    "https://mirror.baidubce.com|百度云"
    "https://ccr.ccs.tencentyun.com|腾讯云"
    "https://reg-mirror.qiniu.com|七牛云"
    "https://docker.m.daocloud.io|DaoCloud"
)

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

# 测试镜像源可用性
test_mirror_availability() {
    local mirror_url="$1"
    local mirror_name="$2"
    
    log_info "测试镜像源: $mirror_name ($mirror_url)"
    
    # 测试连接性
    if curl -s --connect-timeout 5 --max-time 10 "$mirror_url/v2/" > /dev/null 2>&1; then
        log_success "✅ $mirror_name 可用"
        return 0
    else
        log_warning "❌ $mirror_name 不可用"
        return 1
    fi
}

# 获取可用的镜像源
get_available_mirrors() {
    local available_mirrors=()
    
    log_info "正在测试镜像源可用性..."
    echo ""
    
    for mirror_info in "${MIRROR_SOURCES[@]}"; do
        IFS='|' read -r mirror_url mirror_name <<< "$mirror_info"
        
        if test_mirror_availability "$mirror_url" "$mirror_name"; then
            available_mirrors+=("$mirror_url")
        fi
        
        sleep 1  # 避免请求过快
    done
    
    echo ""
    
    if [ ${#available_mirrors[@]} -eq 0 ]; then
        log_error "没有找到可用的镜像源"
        return 1
    fi
    
    log_success "找到 ${#available_mirrors[@]} 个可用镜像源"
    
    # 返回可用镜像源（通过全局变量）
    AVAILABLE_MIRRORS=("${available_mirrors[@]}")
    return 0
}

# 配置macOS Docker Desktop
configure_macos_docker() {
    local mirrors=("$@")
    
    log_info "配置macOS Docker Desktop镜像源..."
    
    local docker_config_dir="$HOME/.docker"
    local daemon_json="$docker_config_dir/daemon.json"
    
    # 备份现有配置
    if [ -f "$daemon_json" ]; then
        cp "$daemon_json" "$daemon_json.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置"
    fi
    
    # 创建配置目录
    mkdir -p "$docker_config_dir"
    
    # 生成镜像源JSON数组
    local mirrors_json=""
    for mirror in "${mirrors[@]}"; do
        if [ -n "$mirrors_json" ]; then
            mirrors_json="$mirrors_json,"
        fi
        mirrors_json="$mirrors_json\"$mirror\""
    done
    
    # 创建daemon.json配置
    cat > "$daemon_json" << EOF
{
  "registry-mirrors": [
    $mirrors_json
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
    
    log_success "已配置Docker镜像源: $daemon_json"
    
    # 显示配置内容
    echo ""
    log_info "配置内容:"
    cat "$daemon_json" | python3 -m json.tool 2>/dev/null || cat "$daemon_json"
    echo ""
}

# 配置Linux Docker
configure_linux_docker() {
    local mirrors=("$@")
    
    log_info "配置Linux Docker镜像源..."
    
    local daemon_json="/etc/docker/daemon.json"
    
    # 检查权限
    if [ "$EUID" -ne 0 ]; then
        log_error "Linux系统需要root权限修改Docker配置"
        log_info "请使用: sudo $0"
        exit 1
    fi
    
    # 备份现有配置
    if [ -f "$daemon_json" ]; then
        cp "$daemon_json" "$daemon_json.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置"
    fi
    
    # 创建配置目录
    mkdir -p /etc/docker
    
    # 生成镜像源JSON数组
    local mirrors_json=""
    for mirror in "${mirrors[@]}"; do
        if [ -n "$mirrors_json" ]; then
            mirrors_json="$mirrors_json,"
        fi
        mirrors_json="$mirrors_json\"$mirror\""
    done
    
    # 创建daemon.json配置
    cat > "$daemon_json" << EOF
{
  "registry-mirrors": [
    $mirrors_json
  ],
  "experimental": false,
  "debug": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    
    log_success "已配置Docker镜像源: $daemon_json"
}

# 重启Docker服务
restart_docker_service() {
    local os=$(detect_os)
    
    case "$os" in
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

# 验证Docker配置
verify_docker_config() {
    log_info "验证Docker配置..."
    
    # 等待Docker启动
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker info &> /dev/null; then
            break
        fi
        
        if [ $((attempt % 5)) -eq 0 ]; then
            log_info "等待Docker启动... ($attempt/$max_attempts)"
        fi
        
        sleep 2
        ((attempt++))
    done
    
    if ! docker info &> /dev/null; then
        log_error "Docker未启动"
        return 1
    fi
    
    # 显示镜像源配置
    log_info "当前Docker镜像源配置:"
    docker info | grep -A 20 "Registry Mirrors" || log_warning "未找到镜像源配置"
    
    echo ""
    
    # 测试镜像拉取
    log_info "测试镜像拉取..."
    if docker pull hello-world:latest; then
        log_success "镜像拉取测试成功"
        docker rmi hello-world:latest &> /dev/null || true
        return 0
    else
        log_error "镜像拉取测试失败"
        return 1
    fi
}

# 显示使用建议
show_usage_tips() {
    echo ""
    log_info "=== 使用建议 ==="
    echo ""
    echo "🚀 现在可以正常使用Docker命令："
    echo "   docker pull python:3.11-slim"
    echo "   docker compose up -d --build"
    echo ""
    echo "🔧 如果仍有问题，可以尝试："
    echo "   1. 清理Docker缓存: docker system prune -f"
    echo "   2. 重新运行此脚本选择其他镜像源"
    echo "   3. 检查网络连接和防火墙设置"
    echo ""
    echo "📊 监控镜像拉取："
    echo "   docker pull --progress=plain <image>"
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "=== Docker镜像加速器配置脚本 ==="
    echo ""
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 显示当前问题
    log_warning "检测到的问题:"
    echo "- Docker Hub拉取限制 (toomanyrequests)"
    echo "- 镜像源连接失败"
    echo "- 需要配置可用的镜像加速器"
    echo ""
    
    # 获取可用镜像源
    if ! get_available_mirrors; then
        log_error "无法找到可用的镜像源，请检查网络连接"
        exit 1
    fi
    
    # 配置Docker
    local os=$(detect_os)
    case "$os" in
        "macos")
            configure_macos_docker "${AVAILABLE_MIRRORS[@]}"
            ;;
        "linux")
            configure_linux_docker "${AVAILABLE_MIRRORS[@]}"
            ;;
        *)
            log_error "不支持的操作系统: $OSTYPE"
            exit 1
            ;;
    esac
    
    # 重启Docker服务
    restart_docker_service
    
    # 验证配置
    if verify_docker_config; then
        log_success "🎉 Docker镜像加速器配置成功！"
        show_usage_tips
    else
        log_error "配置验证失败，请检查Docker状态"
        exit 1
    fi
}

# 运行主函数
main "$@"
