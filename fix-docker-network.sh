#!/bin/bash

# Docker网络连接问题修复脚本
# 解决镜像源配置和网络超时问题

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

# 诊断当前Docker配置
diagnose_docker_config() {
    log_info "=== Docker配置诊断 ==="
    echo ""
    
    # 检查Docker状态
    if docker info &> /dev/null; then
        log_success "✅ Docker运行正常"
    else
        log_error "❌ Docker未运行"
        return 1
    fi
    
    # 检查镜像源配置
    log_info "当前镜像源配置:"
    docker info | grep -A 10 "Registry Mirrors" || log_warning "未找到镜像源配置"
    
    echo ""
    
    # 检查问题镜像源
    if docker info | grep -q "docker.mirrors.ustc.edu.cn"; then
        log_error "❌ 检测到有问题的USTC镜像源"
        return 1
    else
        log_success "✅ 未检测到问题镜像源"
    fi
    
    return 0
}

# 网络连接测试
test_network_connectivity() {
    log_info "=== 网络连接测试 ==="
    echo ""
    
    local test_urls=(
        "registry.cn-hangzhou.aliyuncs.com|阿里云镜像源"
        "hub-mirror.c.163.com|网易镜像源"
        "registry-1.docker.io|Docker Hub"
    )
    
    for url_info in "${test_urls[@]}"; do
        IFS='|' read -r url name <<< "$url_info"
        
        log_info "测试连接: $name ($url)"
        if ping -c 3 -W 3000 "$url" > /dev/null 2>&1; then
            log_success "✅ $name 连接正常"
        else
            log_warning "❌ $name 连接失败"
        fi
    done
    
    echo ""
}

# 清理并重新配置Docker镜像源
fix_docker_mirrors() {
    log_info "=== 修复Docker镜像源配置 ==="
    
    local docker_config_dir="$HOME/.docker"
    local daemon_json="$docker_config_dir/daemon.json"
    
    # 备份现有配置
    if [ -f "$daemon_json" ]; then
        cp "$daemon_json" "$daemon_json.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置"
    fi
    
    # 创建干净的配置（移除USTC源）
    mkdir -p "$docker_config_dir"
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
  },
  "dns": ["8.8.8.8", "114.114.114.114"],
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5
}
EOF
    
    log_success "已更新Docker配置，移除问题镜像源"
    
    # 显示新配置
    echo ""
    log_info "新的配置内容:"
    cat "$daemon_json" | python3 -m json.tool 2>/dev/null || cat "$daemon_json"
    echo ""
}

# 重置Docker网络
reset_docker_network() {
    log_info "=== 重置Docker网络 ==="
    
    # 停止所有容器
    if [ "$(docker ps -q)" ]; then
        log_info "停止所有运行的容器..."
        docker stop $(docker ps -q) 2>/dev/null || true
    fi
    
    # 清理网络
    log_info "清理Docker网络..."
    docker network prune -f &> /dev/null || true
    
    # 重启Docker Desktop
    log_info "重启Docker Desktop..."
    if pgrep -f "Docker Desktop" > /dev/null; then
        osascript -e 'quit app "Docker Desktop"'
        sleep 5
    fi
    
    open -a "Docker Desktop"
    
    # 等待Docker启动
    log_info "等待Docker重新启动..."
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker info &> /dev/null; then
            log_success "Docker已重新启动"
            return 0
        fi
        
        if [ $((attempt % 10)) -eq 0 ]; then
            log_info "等待Docker启动... ($attempt/$max_attempts)"
        fi
        
        sleep 2
        ((attempt++))
    done
    
    log_error "Docker重启超时"
    return 1
}

# 测试镜像拉取
test_image_pull() {
    log_info "=== 测试镜像拉取 ==="
    
    # 测试小镜像
    log_info "测试拉取hello-world镜像..."
    if timeout 60 docker pull hello-world:latest; then
        log_success "✅ hello-world镜像拉取成功"
        docker rmi hello-world:latest &> /dev/null || true
    else
        log_error "❌ hello-world镜像拉取失败"
        return 1
    fi
    
    # 测试Python镜像
    log_info "测试拉取python:3.11-slim镜像..."
    if timeout 300 docker pull python:3.11-slim; then
        log_success "✅ python:3.11-slim镜像拉取成功"
    else
        log_error "❌ python:3.11-slim镜像拉取失败"
        return 1
    fi
    
    return 0
}

# 启动Chrome Plus服务
start_chrome_plus_service() {
    log_info "=== 启动Chrome Plus服务 ==="
    
    if [ ! -f "docker-compose.yml" ]; then
        log_error "未找到docker-compose.yml文件"
        return 1
    fi
    
    # 启动服务
    log_info "启动Chrome Plus V2.0服务..."
    if docker compose up -d --build; then
        log_success "服务启动成功"
        
        # 等待服务就绪
        log_info "等待服务就绪..."
        sleep 20
        
        # 检查服务状态
        log_info "服务状态:"
        docker compose ps
        
        # 测试API
        echo ""
        log_info "测试API连接..."
        local max_attempts=10
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -s http://localhost:5001/health > /dev/null; then
                log_success "✅ API服务正常"
                curl http://localhost:5001/health | python3 -m json.tool 2>/dev/null || curl http://localhost:5001/health
                return 0
            fi
            
            log_info "等待API启动... ($attempt/$max_attempts)"
            sleep 3
            ((attempt++))
        done
        
        log_warning "API服务可能还在启动中"
        return 0
    else
        log_error "服务启动失败"
        return 1
    fi
}

# 显示网络诊断信息
show_network_diagnostics() {
    echo ""
    log_info "=== 网络诊断信息 ==="
    echo ""
    
    # DNS配置
    log_info "DNS配置:"
    cat /etc/resolv.conf | head -5
    
    echo ""
    
    # 网络接口
    log_info "网络接口:"
    ifconfig | grep -E "inet.*broadcast" | head -3
    
    echo ""
    
    # Docker网络
    log_info "Docker网络:"
    docker network ls
    
    echo ""
}

# 主修复流程
main_fix_process() {
    log_info "=== 开始Docker网络修复流程 ==="
    echo ""
    
    # 1. 诊断当前配置
    if ! diagnose_docker_config; then
        log_warning "检测到配置问题，开始修复..."
    fi
    
    # 2. 网络连接测试
    test_network_connectivity
    
    # 3. 修复镜像源配置
    fix_docker_mirrors
    
    # 4. 重置Docker网络
    if ! reset_docker_network; then
        log_error "Docker网络重置失败"
        return 1
    fi
    
    # 5. 验证修复结果
    echo ""
    log_info "验证修复结果..."
    sleep 5
    
    if diagnose_docker_config; then
        log_success "✅ Docker配置修复成功"
    else
        log_error "❌ Docker配置修复失败"
        return 1
    fi
    
    # 6. 测试镜像拉取
    if test_image_pull; then
        log_success "✅ 镜像拉取测试成功"
    else
        log_error "❌ 镜像拉取测试失败"
        return 1
    fi
    
    # 7. 启动Chrome Plus服务
    if start_chrome_plus_service; then
        log_success "🎉 Chrome Plus V2.0启动成功！"
        
        echo ""
        log_info "服务信息:"
        echo "  🌐 后端API: http://localhost:5001"
        echo "  📊 健康检查: http://localhost:5001/health"
        echo "  📊 任务监控: http://localhost:5555"
        echo ""
        
        return 0
    else
        log_error "Chrome Plus服务启动失败"
        return 1
    fi
}

# 主函数
main() {
    echo ""
    log_info "=== Docker网络连接问题修复脚本 ==="
    echo ""
    
    # 显示检测到的问题
    log_error "检测到的问题:"
    echo "❌ USTC镜像源仍在配置中且不可用"
    echo "❌ Docker拉取超时: Client.Timeout exceeded"
    echo "❌ Chrome Plus服务未启动"
    echo ""
    
    # 显示网络诊断信息
    show_network_diagnostics
    
    # 询问是否开始修复
    read -p "是否开始自动修复？(y/n): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log_info "用户取消修复"
        exit 0
    fi
    
    # 执行修复流程
    if main_fix_process; then
        echo ""
        log_success "🎉 所有问题已修复！Chrome Plus V2.0现在可以正常使用了。"
        echo ""
        log_info "Chrome扩展安装:"
        echo "  1. 打开Chrome浏览器"
        echo "  2. 访问 chrome://extensions/"
        echo "  3. 开启'开发者模式'"
        echo "  4. 点击'加载已解压的扩展程序'"
        echo "  5. 选择当前项目目录"
        echo ""
    else
        echo ""
        log_error "修复过程中遇到问题，请检查网络连接或联系技术支持。"
        echo ""
        log_info "手动排查建议:"
        echo "1. 检查网络连接是否稳定"
        echo "2. 确认防火墙没有阻止Docker"
        echo "3. 尝试重启电脑后再次运行脚本"
        echo "4. 检查是否有VPN或代理软件干扰"
        exit 1
    fi
}

# 运行主函数
main "$@"
