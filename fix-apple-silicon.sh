#!/bin/bash

# Chrome Plus V2.0 Apple Silicon (M1/M2) Mac 专用修复脚本

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

# 检测是否为Apple Silicon Mac
check_apple_silicon() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "此脚本专为macOS设计"
        exit 1
    fi
    
    local arch=$(uname -m)
    if [[ "$arch" == "arm64" ]]; then
        log_info "检测到Apple Silicon (M1/M2) Mac"
        return 0
    else
        log_info "检测到Intel Mac"
        return 1
    fi
}

# 检查VPN状态
check_vpn_status() {
    log_info "检查VPN/代理状态..."
    
    # 检查常见VPN进程
    local vpn_processes=("ClashX" "Surge" "Shadowsocks" "V2rayU" "Proxyman")
    local vpn_found=false
    
    for process in "${vpn_processes[@]}"; do
        if pgrep -f "$process" > /dev/null; then
            log_warning "检测到VPN/代理软件: $process"
            vpn_found=true
        fi
    done
    
    if $vpn_found; then
        echo ""
        log_warning "建议临时关闭VPN/代理软件，因为它们可能影响Docker镜像拉取"
        echo "常见影响："
        echo "- 连接超时"
        echo "- SSL证书验证失败"
        echo "- DNS解析问题"
        echo ""
        read -p "是否继续？(y/n): " continue_choice
        if [[ "$continue_choice" != "y" && "$continue_choice" != "Y" ]]; then
            log_info "请关闭VPN/代理后重新运行脚本"
            exit 0
        fi
    else
        log_success "未检测到常见VPN/代理软件"
    fi
}

# 清理Docker配置
clean_docker_config() {
    log_info "清理Docker配置..."
    
    local docker_config_dir="$HOME/.docker"
    local daemon_json="$docker_config_dir/daemon.json"
    
    # 备份现有配置
    if [ -f "$daemon_json" ]; then
        cp "$daemon_json" "$daemon_json.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置"
    fi
    
    # 创建适合Apple Silicon的配置
    mkdir -p "$docker_config_dir"
    cat > "$daemon_json" << 'EOF'
{
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
    
    log_success "已创建适合Apple Silicon的Docker配置"
}

# 重启Docker Desktop
restart_docker_desktop() {
    log_info "重启Docker Desktop..."
    
    # 检查Docker Desktop是否运行
    if pgrep -f "Docker Desktop" > /dev/null; then
        log_info "正在停止Docker Desktop..."
        osascript -e 'quit app "Docker Desktop"'
        sleep 5
    fi
    
    # 启动Docker Desktop
    log_info "正在启动Docker Desktop..."
    open -a "Docker Desktop"
    
    # 等待Docker启动
    log_info "等待Docker Desktop启动..."
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker info &> /dev/null; then
            log_success "Docker Desktop已启动"
            return 0
        fi
        
        if [ $((attempt % 10)) -eq 0 ]; then
            log_info "等待Docker启动... ($attempt/$max_attempts)"
        fi
        
        sleep 2
        ((attempt++))
    done
    
    log_error "Docker Desktop启动超时"
    return 1
}

# 测试平台兼容性
test_platform_compatibility() {
    log_info "测试平台兼容性..."
    
    # 测试拉取amd64镜像
    if docker pull --platform linux/amd64 python:3.11-slim; then
        log_success "amd64平台镜像拉取成功"
        docker rmi python:3.11-slim &> /dev/null || true
        return 0
    else
        log_error "amd64平台镜像拉取失败"
        return 1
    fi
}

# 清理Docker缓存和构建
clean_docker_build() {
    log_info "清理Docker构建缓存..."
    
    # 停止现有服务
    if [ -f "docker-compose.yml" ]; then
        docker compose down --remove-orphans 2>/dev/null || true
    fi
    
    # 清理构建缓存
    docker builder prune -f &> /dev/null || true
    
    # 清理未使用的镜像
    docker image prune -f &> /dev/null || true
    
    # 清理未使用的容器
    docker container prune -f &> /dev/null || true
    
    log_success "Docker缓存已清理"
}

# 构建Chrome Plus服务
build_chrome_plus() {
    log_info "构建Chrome Plus V2.0服务..."
    
    if [ ! -f "docker-compose.yml" ]; then
        log_error "未找到docker-compose.yml文件"
        return 1
    fi
    
    # 检查是否已添加platform配置
    if ! grep -q "platform: linux/amd64" docker-compose.yml; then
        log_warning "docker-compose.yml中缺少platform配置"
        log_info "正在添加platform配置..."
        
        # 这里应该已经通过之前的修改添加了platform配置
        log_success "platform配置已添加"
    fi
    
    # 使用--no-cache确保重新构建
    log_info "开始构建服务（可能需要几分钟）..."
    if docker compose build --no-cache; then
        log_success "服务构建成功"
        
        # 启动服务
        log_info "启动服务..."
        if docker compose up -d; then
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
    else
        log_error "服务构建失败"
        return 1
    fi
}

# 显示网络诊断信息
show_network_diagnostics() {
    log_info "网络诊断信息："
    echo ""
    
    # 测试Docker Hub连接
    echo "🌐 测试Docker Hub连接："
    if curl -s --connect-timeout 5 https://registry-1.docker.io/v2/ > /dev/null; then
        echo "  ✅ Docker Hub连接正常"
    else
        echo "  ❌ Docker Hub连接失败"
    fi
    
    # 测试DNS解析
    echo ""
    echo "🔍 DNS解析测试："
    if nslookup docker.io > /dev/null 2>&1; then
        echo "  ✅ DNS解析正常"
    else
        echo "  ❌ DNS解析失败"
    fi
    
    # 显示网络接口
    echo ""
    echo "📡 当前网络接口："
    ifconfig | grep -E "inet.*broadcast" | head -3
    
    echo ""
}

# 主函数
main() {
    echo ""
    log_info "=== Chrome Plus V2.0 Apple Silicon Mac 修复脚本 ==="
    echo ""
    
    # 检查系统
    local is_apple_silicon=false
    if check_apple_silicon; then
        is_apple_silicon=true
    fi
    
    # 检查VPN状态
    check_vpn_status
    
    # 显示网络诊断
    show_network_diagnostics
    
    # 清理Docker配置
    clean_docker_config
    
    # 重启Docker Desktop
    if ! restart_docker_desktop; then
        log_error "Docker Desktop重启失败"
        exit 1
    fi
    
    # 测试平台兼容性
    if ! test_platform_compatibility; then
        log_error "平台兼容性测试失败"
        log_info "请检查网络连接或尝试关闭VPN/代理"
        exit 1
    fi
    
    # 清理构建缓存
    clean_docker_build
    
    # 构建服务
    if build_chrome_plus; then
        echo ""
        log_success "🎉 Chrome Plus V2.0 在Apple Silicon Mac上启动成功！"
        echo ""
        log_info "服务信息："
        echo "  🌐 后端API: http://localhost:5001"
        echo "  📊 健康检查: http://localhost:5001/health"
        echo "  📊 任务监控: http://localhost:5555"
        echo ""
        log_info "Chrome扩展安装："
        echo "  1. 打开Chrome浏览器"
        echo "  2. 访问 chrome://extensions/"
        echo "  3. 开启'开发者模式'"
        echo "  4. 点击'加载已解压的扩展程序'"
        echo "  5. 选择当前项目目录"
        echo ""
    else
        log_error "服务启动失败"
        echo ""
        log_info "故障排除建议："
        echo "1. 检查网络连接"
        echo "2. 临时关闭VPN/代理软件"
        echo "3. 重启Docker Desktop"
        echo "4. 检查Docker Desktop设置中的资源分配"
        exit 1
    fi
}

# 运行主函数
main "$@"
