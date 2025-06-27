#!/bin/bash
# Chrome扩展构建和打包脚本

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

# 获取版本号
get_version() {
    if [ -f "manifest.json" ]; then
        grep '"version"' manifest.json | cut -d'"' -f4
    else
        echo "1.0.0"
    fi
}

# 清理函数
cleanup() {
    if [ -d "dist" ]; then
        rm -rf dist
    fi
}

# 主函数
main() {
    log_info "开始构建Chrome扩展发布包..."
    
    # 检查是否在项目根目录
    if [ ! -f "manifest.json" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 获取版本号
    VERSION=$(get_version)
    log_info "当前版本: $VERSION"
    
    # 清理旧的构建文件
    cleanup
    
    # 创建构建目录
    mkdir -p dist
    log_info "创建构建目录..."
    
    # 复制扩展文件
    log_info "复制扩展文件..."
    cp -r . dist/chrome_plus_temp
    
    # 进入临时目录进行清理
    cd dist/chrome_plus_temp
    
    # 删除不需要的文件和目录
    log_info "清理不需要的文件..."
    
    # 删除后端服务器文件
    rm -rf server/
    
    # 删除开发文件
    rm -rf .git/
    rm -rf .vscode/
    rm -rf node_modules/
    rm -rf __pycache__/
    rm -rf .pytest_cache/
    rm -rf scripts/
    
    # 删除文档和配置文件
    rm -f *.md
    rm -f .env*
    rm -f .gitignore
    rm -f .gitattributes
    rm -f *.sh
    rm -f *.yml
    rm -f *.yaml
    rm -f requirements.txt
    rm -f pyproject.toml
    rm -f uv.lock
    
    # 删除测试文件
    rm -f test_*
    rm -rf test/
    rm -rf tests/
    
    # 验证必需文件存在
    log_info "验证必需文件..."
    required_files=("manifest.json" "sidepanel.html" "sidepanel.css" "background.js" "chat.js" "api.js")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "缺少必需文件: $file"
            exit 1
        fi
    done
    
    # 检查图标文件
    if [ ! -d "images" ] || [ ! -f "images/icon-16.png" ]; then
        log_warning "缺少图标文件，请确保images目录包含所需的图标"
    fi
    
    # 验证manifest.json
    log_info "验证manifest.json..."
    if ! python3 -c "import json; json.load(open('manifest.json'))" 2>/dev/null; then
        log_error "manifest.json格式无效"
        exit 1
    fi
    
    # 返回dist目录
    cd ..
    
    # 创建zip包
    PACKAGE_NAME="chrome_plus_v${VERSION}.zip"
    log_info "创建发布包: $PACKAGE_NAME"
    
    zip -r "$PACKAGE_NAME" chrome_plus_temp/ -x "*.DS_Store" "*/.*"
    
    # 清理临时目录
    rm -rf chrome_plus_temp
    
    # 获取包大小
    PACKAGE_SIZE=$(du -h "$PACKAGE_NAME" | cut -f1)
    
    # 返回项目根目录
    cd ..
    
    log_success "🎉 构建完成!"
    echo ""
    echo "📦 发布包信息:"
    echo "   文件名: $PACKAGE_NAME"
    echo "   大小: $PACKAGE_SIZE"
    echo "   位置: dist/$PACKAGE_NAME"
    echo ""
    echo "📤 下一步操作:"
    echo "1. 访问 Chrome Web Store 开发者控制台"
    echo "2. 上传 dist/$PACKAGE_NAME"
    echo "3. 填写扩展信息和描述"
    echo "4. 提交审核"
    echo ""
    echo "🔍 本地测试:"
    echo "1. 访问 chrome://extensions/"
    echo "2. 开启开发者模式"
    echo "3. 点击'加载已解压的扩展程序'"
    echo "4. 解压并选择 dist/$PACKAGE_NAME 的内容"
    
    # 生成校验和
    if command -v sha256sum >/dev/null 2>&1; then
        CHECKSUM=$(sha256sum "dist/$PACKAGE_NAME" | cut -d' ' -f1)
        echo ""
        echo "🔐 SHA256校验和: $CHECKSUM"
    fi
}

# 显示帮助信息
show_help() {
    echo "Chrome扩展构建脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -c, --clean    清理构建目录"
    echo "  -v, --version  显示版本信息"
    echo ""
    echo "示例:"
    echo "  $0              # 构建扩展包"
    echo "  $0 --clean     # 清理构建目录"
}

# 处理命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -c|--clean)
        log_info "清理构建目录..."
        cleanup
        log_success "清理完成"
        exit 0
        ;;
    -v|--version)
        VERSION=$(get_version)
        echo "Chrome扩展版本: $VERSION"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "未知选项: $1"
        show_help
        exit 1
        ;;
esac
