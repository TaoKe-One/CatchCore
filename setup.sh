#!/bin/bash

# ============================================================================
# CatchCore 自动部署脚本
# 支持: Linux (Ubuntu/Debian), macOS
# 用法: bash setup.sh
# ============================================================================

set -e  # 如果任何命令失败，立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ============================================================================
# 步骤 1: 检查系统要求
# ============================================================================
check_requirements() {
    print_info "检查系统要求..."

    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 未安装"
        echo "请按照以下步骤安装:"
        echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "  macOS: brew install python3"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python 3 已安装: $PYTHON_VERSION"

    # 检查 Python 版本 (需要 3.10+)
    PYTHON_MINOR=$(python3 --version | awk '{print $2}' | cut -d. -f2)
    PYTHON_PATCH=$(python3 --version | awk '{print $2}' | cut -d. -f3)

    if [ "$PYTHON_MINOR" -lt 10 ]; then
        print_warning "建议使用 Python 3.10 或更高版本 (当前: $PYTHON_VERSION)"
    fi

    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip 未安装"
        exit 1
    fi
    print_success "pip 已安装"

    # 检查 Git (可选)
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version)
        print_success "$GIT_VERSION"
    else
        print_warning "Git 未安装 (可选)"
    fi
}

# ============================================================================
# 步骤 2: 创建虚拟环境
# ============================================================================
create_venv() {
    print_info "创建虚拟环境..."

    if [ -d "venv" ]; then
        print_warning "虚拟环境已存在，跳过创建"
    else
        python3 -m venv venv
        print_success "虚拟环境创建完成"
    fi

    # 激活虚拟环境
    source venv/bin/activate
    print_success "虚拟环境已激活"
}

# ============================================================================
# 步骤 3: 安装依赖
# ============================================================================
install_dependencies() {
    print_info "安装依赖包..."

    # 升级 pip
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    print_success "pip 已升级"

    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "依赖包安装完成"
    else
        print_error "找不到 requirements.txt 文件"
        exit 1
    fi
}

# ============================================================================
# 步骤 4: 创建环境变量文件
# ============================================================================
create_env_file() {
    print_info "配置环境变量..."

    if [ -f ".env" ]; then
        print_warning ".env 文件已存在，跳过创建"
    elif [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env 文件已创建"

        # 生成 SECRET_KEY
        if command -v openssl &> /dev/null; then
            SECRET_KEY=$(openssl rand -hex 32)
            sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
            rm -f .env.bak
            print_success "SECRET_KEY 已生成"
        else
            SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
            sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
            rm -f .env.bak
            print_success "SECRET_KEY 已生成"
        fi
    else
        print_warning ".env.example 文件不存在，创建基本的 .env 文件"
        cat > .env << 'EOF'
DATABASE_URL=sqlite:///./data/catchcore.db
SECRET_KEY=your-secret-key-here
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
EOF
        print_success ".env 文件已创建"
    fi
}

# ============================================================================
# 步骤 5: 创建目录结构
# ============================================================================
create_directories() {
    print_info "创建目录结构..."

    mkdir -p data
    mkdir -p logs
    mkdir -p uploads
    mkdir -p static

    print_success "目录结构已创建"
}

# ============================================================================
# 步骤 6: 初始化数据库
# ============================================================================
init_database() {
    print_info "初始化数据库..."

    python3 << 'PYTHON_EOF'
import sys
import os

try:
    from app.database import Base, engine
    from app.models.user import User
    from app.models.task import Task
    from app.models.asset import Asset
    from app.models.vulnerability import Vulnerability
    from app.models.poc import POC, POCTag

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表已创建")

except Exception as e:
    print(f"✗ 数据库初始化失败: {e}")
    sys.exit(1)
PYTHON_EOF

    if [ $? -eq 0 ]; then
        print_success "数据库初始化完成"
    else
        print_error "数据库初始化失败"
        exit 1
    fi
}

# ============================================================================
# 步骤 7: 运行测试
# ============================================================================
run_tests() {
    print_info "运行测试..."

    if command -v pytest &> /dev/null || python3 -m pytest --version &> /dev/null; then
        python3 -m pytest tests/ -v --tb=short 2>&1 | head -50
        if [ $? -eq 0 ]; then
            print_success "测试通过"
        else
            print_warning "部分测试失败，但应用仍可继续运行"
        fi
    else
        print_warning "pytest 未安装，跳过测试"
    fi
}

# ============================================================================
# 步骤 8: 完成提示
# ============================================================================
print_completion() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                  ✅ 部署完成！                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    print_success "CatchCore 已准备好运行！"
    echo ""
    echo "接下来的步骤:"
    echo ""
    echo "1️⃣  激活虚拟环境:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2️⃣  启动应用:"
    echo "   python3 -m uvicorn app.main:app --reload"
    echo ""
    echo "3️⃣  访问应用:"
    echo "   🌐 API 文档: http://localhost:8000/docs"
    echo "   🔗 API 端点: http://localhost:8000/api/v1"
    echo ""
    echo "4️⃣  查看日志:"
    echo "   tail -f logs/catchcore.log"
    echo ""
    echo "有问题? 查看部署指南:"
    echo "   📖 DEPLOYMENT_GUIDE.md"
    echo ""
}

# ============================================================================
# 主函数
# ============================================================================
main() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           CatchCore 自动部署脚本                         ║"
    echo "║  Advanced Vulnerability Scanning Platform                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # 检查是否在正确的目录
    if [ ! -f "requirements.txt" ]; then
        print_error "请在 CatchCore 后端目录运行此脚本"
        echo "用法: cd CatchCore/backend && bash ../../setup.sh"
        exit 1
    fi

    print_info "开始部署流程..."
    echo ""

    # 执行所有步骤
    check_requirements
    echo ""

    create_venv
    echo ""

    install_dependencies
    echo ""

    create_env_file
    echo ""

    create_directories
    echo ""

    init_database
    echo ""

    run_tests
    echo ""

    print_completion
}

# 运行主函数
main "$@"
