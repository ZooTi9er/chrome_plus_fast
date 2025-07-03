#!/bin/bash

# Docker镜像源修复脚本

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

# 修复macOS Docker Desktop镜像源
fix_macos_docker() {
    log_info "检测到macOS系统，修复Docker Desktop镜像源..."
    
    # Docker Desktop配置文件路径
    DOCKER_CONFIG_DIR="$HOME/.docker"
    DAEMON_JSON="$DOCKER_CONFIG_DIR/daemon.json"
    
    # 创建配置目录
    mkdir -p "$DOCKER_CONFIG_DIR"
    
    # 备份现有配置
    if [ -f "$DAEMON_JSON" ]; then
        cp "$DAEMON_JSON" "$DAEMON_JSON.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置到 $DAEMON_JSON.backup.*"
    fi
    
    # 创建新的daemon.json配置
    cat > "$DAEMON_JSON" << 'EOF'
{
  "registry-mirrors": [
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
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
    
    log_success "已更新Docker配置文件: $DAEMON_JSON"
    log_warning "请重启Docker Desktop以使配置生效"
    
    # 提示用户重启Docker Desktop
    echo ""
    log_info "请按以下步骤重启Docker Desktop:"
    echo "1. 点击菜单栏的Docker图标"
    echo "2. 选择 'Restart Docker Desktop'"
    echo "3. 等待Docker重启完成"
    echo ""
}

# 修复Linux Docker镜像源
fix_linux_docker() {
    log_info "检测到Linux系统，修复Docker镜像源..."
    
    DAEMON_JSON="/etc/docker/daemon.json"
    
    # 检查权限
    if [ "$EUID" -ne 0 ]; then
        log_error "Linux系统需要root权限修改Docker配置"
        log_info "请使用: sudo $0"
        exit 1
    fi
    
    # 创建配置目录
    mkdir -p /etc/docker
    
    # 备份现有配置
    if [ -f "$DAEMON_JSON" ]; then
        cp "$DAEMON_JSON" "$DAEMON_JSON.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置"
    fi
    
    # 创建新的daemon.json配置
    cat > "$DAEMON_JSON" << 'EOF'
{
  "registry-mirrors": [
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://ccr.ccs.tencentyun.com"
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
    
    log_success "已更新Docker配置文件: $DAEMON_JSON"
    
    # 重启Docker服务
    log_info "重启Docker服务..."
    systemctl daemon-reload
    systemctl restart docker
    
    log_success "Docker服务已重启"
}

# 验证Docker配置
verify_docker_config() {
    log_info "验证Docker配置..."
    
    # 等待Docker启动
    sleep 5
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker未运行，请手动启动Docker"
        return 1
    fi
    
    # 显示镜像源配置
    log_info "当前Docker镜像源配置:"
    docker info | grep -A 10 "Registry Mirrors" || log_warning "未找到镜像源配置"
    
    # 测试镜像拉取
    log_info "测试镜像拉取..."
    if docker pull hello-world:latest; then
        log_success "镜像拉取测试成功"
        docker rmi hello-world:latest &> /dev/null || true
    else
        log_error "镜像拉取测试失败"
        return 1
    fi
    
    return 0
}

# 主函数
main() {
    echo ""
    log_info "=== Docker镜像源修复脚本 ==="
    echo ""
    
    OS=$(detect_os)
    
    case "$OS" in
        "macos")
            fix_macos_docker
            ;;
        "linux")
            fix_linux_docker
            ;;
        *)
            log_error "不支持的操作系统: $OSTYPE"
            exit 1
            ;;
    esac
    
    echo ""
    log_info "配置完成，验证Docker配置..."
    
    if verify_docker_config; then
        log_success "Docker镜像源修复完成！"
    else
        log_error "Docker配置验证失败，请检查Docker状态"
        exit 1
    fi
}

# 运行主函数
main "$@"
