# ============================================================================
# CatchCore Windows 自动部署脚本 (PowerShell)
# 用法: .\setup.ps1
#
# 首次使用可能需要运行:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# ============================================================================

# 颜色定义
$Colors = @{
    Info    = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
}

# 打印信息函数
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Info
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✓] $Message" -ForegroundColor $Colors.Success
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[⚠] $Message" -ForegroundColor $Colors.Warning
}

function Write-Error {
    param([string]$Message)
    Write-Host "[✗] $Message" -ForegroundColor $Colors.Error
}

function Exit-Script {
    param([string]$Message = "按任意键退出...")
    Write-Host $Message
    $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit
}

# ============================================================================
# 步骤 1: 检查系统要求
# ============================================================================
function Check-Requirements {
    Write-Info "检查系统要求..."

    # 检查 Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "Python 已安装: $pythonVersion"
    } catch {
        Write-Error "Python 未安装"
        Write-Host ""
        Write-Host "请按以下步骤安装 Python:"
        Write-Host "1. 访问 https://www.python.org/downloads/"
        Write-Host "2. 下载 Python 3.10+ 版本"
        Write-Host "3. 安装时请勾选 'Add Python to PATH'"
        Write-Host ""
        Exit-Script
    }

    # 检查 pip
    try {
        $pipVersion = pip --version 2>&1
        Write-Success "pip 已安装"
    } catch {
        Write-Error "pip 未安装"
        Exit-Script
    }

    # 检查 Git (可选)
    try {
        $gitVersion = git --version 2>&1
        Write-Success "Git 已安装: $gitVersion"
    } catch {
        Write-Warning "Git 未安装 (可选)"
    }
}

# ============================================================================
# 步骤 2: 创建虚拟环境
# ============================================================================
function Create-VirtualEnv {
    Write-Info "创建虚拟环境..."

    if (Test-Path "venv") {
        Write-Warning "虚拟环境已存在，跳过创建"
    } else {
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Error "虚拟环境创建失败"
            Exit-Script
        }
        Write-Success "虚拟环境创建完成"
    }

    # 激活虚拟环境
    & ".\venv\Scripts\Activate.ps1"
    Write-Success "虚拟环境已激活"
}

# ============================================================================
# 步骤 3: 安装依赖
# ============================================================================
function Install-Dependencies {
    Write-Info "安装依赖包..."

    # 升级 pip
    python -m pip install --upgrade pip setuptools wheel | Out-Null
    Write-Success "pip 已升级"

    # 安装依赖
    if (Test-Path "requirements.txt") {
        Write-Info "这可能需要几分钟，请耐心等待..."
        pip install -r requirements.txt

        if ($LASTEXITCODE -ne 0) {
            Write-Error "依赖包安装失败"
            Exit-Script
        }
        Write-Success "依赖包安装完成"
    } else {
        Write-Error "找不到 requirements.txt 文件"
        Exit-Script
    }
}

# ============================================================================
# 步骤 4: 创建环境变量文件
# ============================================================================
function Create-EnvFile {
    Write-Info "配置环境变量..."

    if (Test-Path ".env") {
        Write-Warning ".env 文件已存在，跳过创建"
    } elseif (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Success ".env 文件已创建"

        # 生成 SECRET_KEY
        $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object { [char]$_ })

        # 更新 .env 文件中的 SECRET_KEY
        (Get-Content ".env") -replace '^SECRET_KEY=.*', "SECRET_KEY=$secretKey" | Set-Content ".env"
        Write-Success "SECRET_KEY 已生成"
    } else {
        Write-Warning ".env.example 文件不存在，创建基本的 .env 文件"

        $envContent = @"
DATABASE_URL=sqlite:///./data/catchcore.db
SECRET_KEY=your-secret-key-here
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
"@

        Set-Content ".env" $envContent
        Write-Success ".env 文件已创建"
    }
}

# ============================================================================
# 步骤 5: 创建目录结构
# ============================================================================
function Create-Directories {
    Write-Info "创建目录结构..."

    @("data", "logs", "uploads", "static") | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ | Out-Null
        }
    }

    Write-Success "目录结构已创建"
}

# ============================================================================
# 步骤 6: 初始化数据库
# ============================================================================
function Initialize-Database {
    Write-Info "初始化数据库..."

    $pythonScript = @"
import sys

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
"@

    $pythonScript | python

    if ($LASTEXITCODE -eq 0) {
        Write-Success "数据库初始化完成"
    } else {
        Write-Error "数据库初始化失败"
        Exit-Script
    }
}

# ============================================================================
# 步骤 7: 运行测试
# ============================================================================
function Run-Tests {
    Write-Info "运行测试..."

    $pytestExists = python -m pytest --version 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Info "运行测试用例..."
        python -m pytest tests/ -v --tb=short 2>&1 | Select-Object -First 50

        if ($LASTEXITCODE -eq 0) {
            Write-Success "测试通过"
        } else {
            Write-Warning "部分测试失败，但应用仍可继续运行"
        }
    } else {
        Write-Warning "pytest 未安装，跳过测试"
    }
}

# ============================================================================
# 步骤 8: 完成提示
# ============================================================================
function Print-Completion {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor $Colors.Success
    Write-Host "║                  ✅ 部署完成！                            ║" -ForegroundColor $Colors.Success
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor $Colors.Success
    Write-Host ""
    Write-Success "CatchCore 已准备好运行！"
    Write-Host ""
    Write-Host "接下来的步骤:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1️⃣  虚拟环境已激活，继续在此 PowerShell 窗口中运行应用"
    Write-Host ""
    Write-Host "2️⃣  启动应用:"
    Write-Host "   python -m uvicorn app.main:app --reload"
    Write-Host ""
    Write-Host "3️⃣  访问应用 (在浏览器中打开):"
    Write-Host "   🌐 API 文档: http://localhost:8000/docs"
    Write-Host "   🔗 API 端点: http://localhost:8000/api/v1"
    Write-Host ""
    Write-Host "4️⃣  查看日志:"
    Write-Host "   Get-Content logs/catchcore.log -Tail 50 -Wait"
    Write-Host ""
    Write-Host "有问题? 查看部署指南:" -ForegroundColor Yellow
    Write-Host "   📖 DEPLOYMENT_GUIDE.md"
    Write-Host ""
    Write-Host "按任意键关闭此窗口..." -ForegroundColor Green
    $null = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# ============================================================================
# 主函数
# ============================================================================
function Main {
    Clear-Host

    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor $Colors.Success
    Write-Host "║           CatchCore Windows 自动部署脚本                ║" -ForegroundColor $Colors.Success
    Write-Host "║  Advanced Vulnerability Scanning Platform                 ║" -ForegroundColor $Colors.Success
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor $Colors.Success
    Write-Host ""

    # 检查是否在正确的目录
    if (-not (Test-Path "requirements.txt")) {
        Write-Error "请在 CatchCore 后端目录运行此脚本"
        Write-Host "用法: cd CatchCore\backend; ..\...\setup.ps1"
        Exit-Script
    }

    Write-Info "开始部署流程..."
    Write-Host ""

    # 执行所有步骤
    Check-Requirements
    Write-Host ""

    Create-VirtualEnv
    Write-Host ""

    Install-Dependencies
    Write-Host ""

    Create-EnvFile
    Write-Host ""

    Create-Directories
    Write-Host ""

    Initialize-Database
    Write-Host ""

    Run-Tests
    Write-Host ""

    Print-Completion
}

# 运行主函数
Main
