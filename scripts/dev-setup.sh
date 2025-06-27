#!/bin/bash
# 开发环境设置脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 >/dev/null 2>&1; then
        log_error "$1 未安装，请先安装 $1"
        exit 1
    fi
}

# 主函数
main() {
    log_info "开始设置Chrome扩展AI助手开发环境..."
    
    # 检查必需的工具
    log_info "检查必需的工具..."
    check_command "python3"
    check_command "uv"
    check_command "git"
    
    # 检查Python版本
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$python_version >= 3.10" | bc -l) -eq 0 ]]; then
        log_error "需要Python 3.10或更高版本，当前版本: $python_version"
        exit 1
    fi
    log_success "Python版本检查通过: $python_version"
    
    # 进入项目目录
    if [ ! -f "manifest.json" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 设置后端环境
    log_info "设置后端环境..."
    cd server
    
    # 安装依赖
    log_info "安装Python依赖..."
    uv sync
    log_success "Python依赖安装完成"
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        log_warning "未找到.env文件，创建示例文件..."
        cat > .env << EOF
# API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# 服务器配置
SERVER_HOST=127.0.0.1
SERVER_PORT=5001
DEBUG=true

# 日志配置
LOG_LEVEL=INFO
EOF
        log_warning "请编辑 server/.env 文件，添加您的API密钥"
    else
        log_success "找到.env文件"
    fi
    
    # 创建测试目录
    mkdir -p test
    mkdir -p logs
    log_success "创建必要的目录"
    
    # 运行测试
    log_info "运行基础测试..."
    if uv run python -c "import fastapi; import pydantic; print('依赖检查通过')"; then
        log_success "依赖检查通过"
    else
        log_error "依赖检查失败"
        exit 1
    fi
    
    # 返回项目根目录
    cd ..
    
    # 创建启动脚本
    log_info "创建便捷启动脚本..."
    cat > start-dev.sh << 'EOF'
#!/bin/bash
# 开发环境启动脚本

echo "🚀 启动Chrome扩展AI助手开发环境..."

# 启动后端服务
cd server
echo "📡 启动FastAPI服务器..."
uv run python start_server.py &
SERVER_PID=$!

echo "✅ 服务器已启动 (PID: $SERVER_PID)"
echo "📖 API文档: http://127.0.0.1:5001/docs"
echo "🔧 请在Chrome中加载扩展: chrome://extensions/"
echo ""
echo "按 Ctrl+C 停止服务器"

# 等待中断信号
trap "echo '🛑 停止服务器...'; kill $SERVER_PID; exit" INT
wait $SERVER_PID
EOF
    chmod +x start-dev.sh
    
    # 创建测试脚本
    cat > test-all.sh << 'EOF'
#!/bin/bash
# 完整测试脚本

echo "🧪 运行完整测试套件..."

cd server

# 运行自动化测试
echo "📋 运行自动化测试..."
uv run python -m pytest test_fastapi.py -v

# 运行手动测试
echo "🔧 运行手动测试..."
echo "请确保服务器正在运行，然后按Enter继续..."
read -p ""
uv run python test_manual.py

echo "✅ 测试完成!"
EOF
    chmod +x test-all.sh
    
    log_success "便捷脚本创建完成"
    
    # 显示下一步操作
    echo ""
    log_success "🎉 开发环境设置完成!"
    echo ""
    echo "下一步操作:"
    echo "1. 编辑 server/.env 文件，添加您的API密钥"
    echo "2. 运行 ./start-dev.sh 启动开发服务器"
    echo "3. 在Chrome中访问 chrome://extensions/"
    echo "4. 开启开发者模式，点击'加载已解压的扩展程序'"
    echo "5. 选择当前目录加载扩展"
    echo ""
    echo "有用的命令:"
    echo "  ./start-dev.sh     - 启动开发环境"
    echo "  ./test-all.sh      - 运行完整测试"
    echo "  cd server && uv run python start_server.py - 手动启动服务器"
    echo ""
    log_info "开发愉快! 🚀"
}

# 运行主函数
main "$@"
