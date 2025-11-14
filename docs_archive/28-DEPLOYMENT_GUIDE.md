# CatchCore 部署指南

## 📚 目录
1. [系统要求](#系统要求)
2. [快速开始](#快速开始)
3. [详细部署步骤](#详细部署步骤)
4. [数据库配置](#数据库配置)
5. [环境变量配置](#环境变量配置)
6. [运行应用](#运行应用)
7. [测试验证](#测试验证)
8. [常见问题排查](#常见问题排查)
9. [生产环境部署](#生产环境部署)
10. [监控和维护](#监控和维护)

---

## 系统要求

### 操作系统
- **Linux** (推荐 Ubuntu 20.04 或更高版本)
- **macOS** (10.14 或更高版本)
- **Windows** (建议使用 WSL 2)

### 软件要求
```
Python:          3.10 或更高版本
pip:             最新版本
Git:             2.0 或更高版本
PostgreSQL:      13 或更高版本 (生产环境)
SQLite:          3.0 或更高版本 (开发环境)
```

### 硬件要求
```
CPU:             2 核或以上
内存:            4GB 或以上 (建议 8GB)
磁盘:            10GB 可用空间
```

### 网络要求
```
互联网连接:      用于下载依赖
开放端口:        8000 (应用), 5432 (PostgreSQL)
```

---

## 快速开始

如果你很着急，可以按照这个最简单的步骤快速部署：

### 1 分钟快速部署 (开发环境)

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/CatchCore.git
cd CatchCore/backend

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python3 -m alembic upgrade head

# 5. 运行应用
python3 -m uvicorn app.main:app --reload

# 打开浏览器访问: http://localhost:8000
```

> **如果任何步骤出错，请查看下面的"常见问题排查"部分**

---

## 详细部署步骤

### 第 1 步: 系统准备

#### 1.1 更新系统包

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget
```

**macOS:**
```bash
# 确保已安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install python3 git postgresql
```

**Windows (使用 PowerShell):**
```powershell
# 使用 Chocolatey (需要先安装)
choco install python git postgresql
# 或手动下载安装:
# Python: https://www.python.org/downloads/
# Git: https://git-scm.com/download/win
# PostgreSQL: https://www.postgresql.org/download/windows/
```

#### 1.2 验证安装

```bash
# 检查 Python 版本
python3 --version
# 应该输出: Python 3.10.x 或更高

# 检查 pip 版本
pip --version
# 应该输出: pip xx.x from ...

# 检查 Git 版本
git --version
# 应该输出: git version 2.x.x
```

### 第 2 步: 克隆项目

```bash
# 创建工作目录
mkdir -p ~/projects
cd ~/projects

# 克隆项目 (使用 HTTPS)
git clone https://github.com/yourusername/CatchCore.git

# 或使用 SSH (如果已配置)
git clone git@github.com:yourusername/CatchCore.git

# 进入项目目录
cd CatchCore
```

**如果克隆失败:**
```bash
# 检查网络连接
ping github.com

# 如果无法连接到 GitHub，可以尝试使用代理
git config --global https.proxy http://proxyserver:port

# 或下载 ZIP 文件，然后解压
```

### 第 3 步: 创建虚拟环境

**Linux/macOS:**
```bash
# 进入后端目录
cd CatchCore/backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 你应该看到 (venv) 前缀出现在命令行
```

**Windows (PowerShell):**
```powershell
cd CatchCore\backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 如果出错，可能需要执行权限
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**验证虚拟环境:**
```bash
which python  # Linux/macOS
# 应该输出: /path/to/CatchCore/backend/venv/bin/python

where python  # Windows
# 应该输出包含 venv 的路径
```

### 第 4 步: 安装依赖

```bash
# 确保虚拟环境已激活 (看到 (venv) 前缀)

# 升级 pip (重要！)
pip install --upgrade pip

# 安装所有依赖
pip install -r requirements.txt

# 这会耗时 2-5 分钟，取决于网络速度
```

**如果安装缓慢:**
```bash
# 使用阿里云镜像 (中国用户)
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 或使用清华大学镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

**验证安装:**
```bash
# 检查关键依赖
pip list | grep -E "fastapi|sqlalchemy|pytest|uvicorn"

# 或
pip show fastapi
```

### 第 5 步: 数据库初始化

#### 使用 SQLite (开发环境 - 推荐新手)

```bash
# SQLite 已包含在 Python 中，无需额外安装

# 创建数据库文件夹
mkdir -p data

# 数据库文件将在 data/catchcore.db 中自动创建
```

#### 使用 PostgreSQL (生产环境)

```bash
# 1. 创建数据库和用户
sudo -u postgres psql

# 在 PostgreSQL 提示符中执行:
CREATE DATABASE catchcore;
CREATE USER catchcore_user WITH PASSWORD 'your_secure_password';
ALTER ROLE catchcore_user SET client_encoding TO 'utf8';
ALTER ROLE catchcore_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE catchcore_user SET default_transaction_deferrable TO on;
ALTER ROLE catchcore_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE catchcore TO catchcore_user;
\q

# 2. 验证连接
psql -U catchcore_user -d catchcore -h localhost
# 输入密码后，应该看到 catchcore=# 提示符
```

### 第 6 步: 配置环境变量

创建 `.env` 文件 (复制自 `.env.example`):

```bash
cd /path/to/CatchCore/backend

# 复制示例文件
cp .env.example .env

# 编辑 .env 文件 (使用你喜欢的编辑器)
nano .env
# 或
vim .env
```

**.env 文件内容 (开发环境):**

```ini
# ============================================================
# 应用配置
# ============================================================
APP_NAME=CatchCore
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# ============================================================
# 数据库配置
# ============================================================
# 使用 SQLite (开发)
DATABASE_URL=sqlite:///./data/catchcore.db

# 或使用 PostgreSQL (生产)
# DATABASE_URL=postgresql://catchcore_user:your_secure_password@localhost:5432/catchcore

# ============================================================
# API 配置
# ============================================================
API_TITLE=CatchCore API
API_DESCRIPTION=Advanced Vulnerability Scanning Platform
API_VERSION=1.0.0

# ============================================================
# 安全配置
# ============================================================
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================================
# CORS 配置
# ============================================================
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# ============================================================
# 扫描工具配置
# ============================================================
TOOLS_ENABLED=true
FSCAN_PATH=/usr/local/bin/fscan
NUCLEI_PATH=/usr/local/bin/nuclei
DIRSEARCH_PATH=/usr/local/bin/dirsearch
AFROG_PATH=/usr/local/bin/afrog
DDDD_PATH=/usr/local/bin/dddd

# ============================================================
# 日志配置
# ============================================================
LOG_LEVEL=INFO
LOG_FILE=logs/catchcore.log
```

**生成安全的 SECRET_KEY:**

```bash
# 方法 1: 使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法 2: 使用 OpenSSL
openssl rand -hex 32

# 复制输出的字符串，粘贴到 .env 文件的 SECRET_KEY
```

---

## 数据库配置

### 初始化数据库表

```bash
# 确保虚拟环境已激活

# 创建所有数据库表
python3 -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 验证表是否创建成功
sqlite3 data/catchcore.db ".tables"  # SQLite
# 或
psql -U catchcore_user -d catchcore -c "\dt"  # PostgreSQL
```

### 创建初始用户 (可选)

```bash
# 创建管理员用户
python3 << EOF
import sys
sys.path.insert(0, '.')

from app.models.user import User
from app.database import SessionLocal
from app.services.security_service import get_password_hash

db = SessionLocal()

# 检查用户是否已存在
existing_user = db.query(User).filter(User.username == "admin").first()
if not existing_user:
    admin = User(
        username="admin",
        email="admin@catchcore.local",
        hashed_password=get_password_hash("admin@123"),
        is_admin=True,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print("✅ 管理员用户创建成功!")
    print("用户名: admin")
    print("密码: admin@123")
    print("⚠️ 请立即修改密码！")
else:
    print("⚠️ 管理员用户已存在")

db.close()
EOF
```

---

## 环境变量配置

### 完整的环境变量列表

| 变量 | 说明 | 示例 | 是否必需 |
|-----|------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/catchcore.db` | ✅ |
| `SECRET_KEY` | JWT 密钥 | `your-secret-key-32-chars` | ✅ |
| `DEBUG` | 调试模式 | `True` 或 `False` | ❌ |
| `ENVIRONMENT` | 环境类型 | `development` 或 `production` | ❌ |
| `LOG_LEVEL` | 日志级别 | `DEBUG`, `INFO`, `WARNING`, `ERROR` | ❌ |
| `CORS_ORIGINS` | 允许的源 | `["http://localhost:3000"]` | ❌ |

### 验证环境变量

```bash
# 创建测试脚本
cat > test_env.py << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    'DATABASE_URL',
    'SECRET_KEY',
]

print("检查必需的环境变量...")
for var in required_vars:
    value = os.getenv(var)
    if value:
        # 隐藏敏感信息
        if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
            print(f"✅ {var}: {'*' * 20}")
        else:
            print(f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: 未设置")
EOF

python3 test_env.py
```

---

## 运行应用

### 开发环境 (推荐新手使用)

```bash
# 确保在虚拟环境中
source venv/bin/activate  # Linux/macOS

# 使用 uvicorn 运行应用 (带自动重载)
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 输出应该如下所示:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

### 访问应用

```
API 文档:      http://localhost:8000/docs
备选文档:      http://localhost:8000/redoc
API 端点:      http://localhost:8000/api/v1
健康检查:      http://localhost:8000/health
```

### 常见的运行模式

```bash
# 模式 1: 基本运行 (自动重载，适合开发)
python3 -m uvicorn app.main:app --reload

# 模式 2: 指定主机和端口
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 模式 3: 生产模式 (多进程)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 模式 4: 后台运行 (使用 nohup)
nohup python3 -m uvicorn app.main:app > logs/app.log 2>&1 &

# 模式 5: 使用 Gunicorn (推荐生产)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### 停止应用

```bash
# 如果在前台运行，按 Ctrl+C

# 如果在后台运行
# 方法 1: 使用 pkill
pkill -f "uvicorn app.main"

# 方法 2: 查找进程并杀死
ps aux | grep uvicorn
kill -9 <PID>
```

---

## 测试验证

### 运行单元测试

```bash
# 确保虚拟环境已激活

# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试
python3 -m pytest tests/unit/test_security.py -v

# 运行测试并生成覆盖率报告
python3 -m pytest tests/ --cov=app --cov-report=html

# 查看覆盖率报告 (在浏览器中)
open htmlcov/index.html  # macOS
# 或
xdg-open htmlcov/index.html  # Linux
```

### API 端点测试

```bash
# 打开另一个终端，确保应用正在运行

# 测试健康检查
curl http://localhost:8000/health

# 测试 API 版本
curl http://localhost:8000/api/v1/version

# 查看 API 文档
curl http://localhost:8000/docs
```

### 使用 Postman 或 Insomnia

1. 下载 [Postman](https://www.postman.com/) 或 [Insomnia](https://insomnia.rest/)
2. 导入 API 集合: `docs/postman_collection.json`
3. 设置环境变量
4. 运行测试

---

## 常见问题排查

### 问题 1: "python3: command not found"

**原因:** Python 未安装或未添加到 PATH

**解决方案:**

```bash
# 检查 Python 是否安装
which python3
python3 --version

# 如果未安装
# Linux/Ubuntu:
sudo apt install python3 python3-pip

# macOS:
brew install python3

# Windows:
# 从 https://www.python.org/downloads/ 下载并安装
```

### 问题 2: "ModuleNotFoundError: No module named 'fastapi'"

**原因:** 依赖未安装

**解决方案:**

```bash
# 确保虚拟环境已激活 (看到 (venv) 前缀)
source venv/bin/activate

# 重新安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 验证安装
pip list | grep fastapi
```

### 问题 3: "FileNotFoundError: [Errno 2] No such file or directory: '.env'"

**原因:** 缺少 .env 文件

**解决方案:**

```bash
# 创建 .env 文件
cp .env.example .env

# 或手动创建
cat > .env << 'EOF'
DATABASE_URL=sqlite:///./data/catchcore.db
SECRET_KEY=your-secret-key-32-chars
DEBUG=True
ENVIRONMENT=development
EOF
```

### 问题 4: "address already in use"

**原因:** 端口 8000 已被占用

**解决方案:**

```bash
# 方法 1: 使用不同的端口
python3 -m uvicorn app.main:app --port 8001

# 方法 2: 找到占用端口的进程并关闭
# Linux/macOS:
lsof -i :8000
kill -9 <PID>

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### 问题 5: "FATAL: Ident authentication failed for user 'postgres'"

**原因:** PostgreSQL 认证失败

**解决方案:**

```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 启动 PostgreSQL
sudo systemctl start postgresql

# 重置密码
sudo -u postgres psql
ALTER USER postgres PASSWORD 'new_password';
\q
```

### 问题 6: 数据库迁移错误

**原因:** 数据库版本不匹配或迁移脚本缺失

**解决方案:**

```bash
# 查看迁移状态
python3 -m alembic current

# 应用所有迁移
python3 -m alembic upgrade head

# 创建新的迁移 (如果有数据库变更)
python3 -m alembic revision --autogenerate -m "描述你的变更"

# 查看迁移历史
python3 -m alembic history
```

### 问题 7: 内存不足或速度缓慢

**原因:** 虚拟环境配置不当或系统资源不足

**解决方案:**

```bash
# 检查虚拟环境
which python
python -c "import sys; print(sys.prefix)"

# 清理 pip 缓存
pip cache purge

# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 8: 导入错误 "cannot import name 'xxx' from 'yyy'"

**原因:** 项目结构变更或缓存问题

**解决方案:**

```bash
# 清理 Python 缓存
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# 重启虚拟环境
deactivate
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 问题 9: SSL 证书错误

**原因:** 网络或 HTTPS 配置问题

**解决方案:**

```bash
# 临时禁用 SSL 验证 (仅用于开发)
pip install --trusted-host pypi.python.org -r requirements.txt

# 或设置环境变量
export PYTHONHTTPSVERIFY=0
pip install -r requirements.txt

# 推荐方案: 更新 CA 证书
curl https://cacert.omniroot.com/bc2025.crt -o ~/cacert.pem
export REQUESTS_CA_BUNDLE=~/cacert.pem
```

### 问题 10: 权限被拒绝错误

**原因:** 目录或文件权限问题

**解决方案:**

```bash
# 检查权限
ls -la

# 修复权限
chmod 755 CatchCore
chmod 755 CatchCore/backend
chmod 644 CatchCore/backend/requirements.txt

# 如果是系统目录，使用 sudo
sudo chown -R $USER:$USER ~/projects/CatchCore
```

---

## 生产环境部署

### 预部署检查清单

- [ ] 所有环境变量正确配置
- [ ] 数据库已备份
- [ ] 密钥文件已安全存储
- [ ] SSL 证书已获取
- [ ] 防火墙规则已配置
- [ ] 监控和日志已设置
- [ ] 备份和恢复计划已制定
- [ ] 负载均衡器已配置 (如需要)

### 使用 Gunicorn + Nginx 部署

#### 1. 安装 Gunicorn

```bash
pip install gunicorn
```

#### 2. 创建 Gunicorn 配置文件

创建 `gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
max_requests = 10000
max_requests_jitter = 1000
```

#### 3. 创建 Systemd 服务文件

创建 `/etc/systemd/system/catchcore.service`:

```ini
[Unit]
Description=CatchCore API Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/CatchCore/backend
Environment="PATH=/path/to/CatchCore/backend/venv/bin"
ExecStart=/path/to/CatchCore/backend/venv/bin/gunicorn --config gunicorn_config.py app.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 4. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable catchcore
sudo systemctl start catchcore
sudo systemctl status catchcore
```

#### 5. 配置 Nginx

创建 `/etc/nginx/sites-available/catchcore`:

```nginx
upstream catchcore {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/catchcore_access.log;
    error_log /var/log/nginx/catchcore_error.log;

    # 主反向代理
    location / {
        proxy_pass http://catchcore;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://catchcore;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;
    }

    # 静态文件
    location /static {
        alias /path/to/CatchCore/static;
        expires 30d;
    }
}
```

#### 6. 启用站点

```bash
sudo ln -s /etc/nginx/sites-available/catchcore /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 获取 SSL 证书 (Let's Encrypt)

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot certonly --nginx -d your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

### 日志配置

创建 `logging_config.py`:

```python
import logging
import logging.handlers
from pathlib import Path

# 创建日志目录
Path("logs").mkdir(exist_ok=True)

# 文件处理器
file_handler = logging.handlers.RotatingFileHandler(
    "logs/catchcore.log",
    maxBytes=10485760,  # 10MB
    backupCount=10
)

# 控制台处理器
console_handler = logging.StreamHandler()

# 日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 配置日志
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
```

---

## 监控和维护

### 系统监控

```bash
# 监控 CPU 和内存使用
top

# 监控进程
ps aux | grep gunicorn

# 监控日志
tail -f logs/catchcore.log

# 监控数据库连接
psql -U catchcore_user -d catchcore -c "SELECT * FROM pg_stat_activity;"
```

### 定期备份

创建 `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/path/to/backups"
DB_NAME="catchcore"
DB_USER="catchcore_user"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_backup_$TIMESTAMP.tar.gz /path/to/uploads/

# 删除 30 天前的备份
find $BACKUP_DIR -type f -mtime +30 -delete

echo "✅ 备份完成: $TIMESTAMP"
```

### 定时任务

```bash
# 编辑 crontab
crontab -e

# 添加备份任务 (每天 2:00 AM)
0 2 * * * /path/to/backup.sh

# 添加日志清理任务 (每周清理一次)
0 3 * * 0 find /path/to/logs -type f -mtime +30 -delete
```

### 性能优化

```python
# 在 app/main.py 中添加性能监控
from fastapi import FastAPI
from fastapi.middleware import gzip

app = FastAPI()

# 启用 GZIP 压缩
app.add_middleware(gzip.GZIPMiddleware, minimum_size=1000)

# 添加缓存
from fastapi_cache2 import FastAPICache2
FastAPICache2.init(InMemoryBackend())
```

### 监听告警

```python
# 创建健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database": await check_database(),
        "memory": get_memory_usage(),
        "cpu": get_cpu_usage()
    }
```

---

## 总结

### 快速参考

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行应用
python3 -m uvicorn app.main:app --reload

# 运行测试
python3 -m pytest tests/ -v

# 生成覆盖率报告
python3 -m pytest tests/ --cov=app --cov-report=html
```

### 获取帮助

- **官方文档:** [CatchCore Wiki](https://github.com/yourusername/CatchCore/wiki)
- **问题报告:** [GitHub Issues](https://github.com/yourusername/CatchCore/issues)
- **讨论区:** [GitHub Discussions](https://github.com/yourusername/CatchCore/discussions)
- **邮件:** support@catchcore.local

---

## 附录

### 附录 A: 所有依赖包

详见 `requirements.txt`

### 附录 B: API 端点列表

详见 `docs/api_endpoints.md`

### 附录 C: 数据库模式

详见 `docs/database_schema.md`

### 附录 D: 环境变量完整列表

详见 `.env.example`

---

**最后更新:** 2025 年 11 月 12 日
**维护者:** CatchCore 团队
**版本:** 1.0.0
