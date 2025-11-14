# CatchCore 故障排查指南

## 📋 目录
1. [快速诊断](#快速诊断)
2. [Python 和环境问题](#python-和环境问题)
3. [依赖和包问题](#依赖和包问题)
4. [数据库问题](#数据库问题)
5. [运行时问题](#运行时问题)
6. [网络和连接问题](#网络和连接问题)
7. [性能问题](#性能问题)
8. [Windows 特定问题](#windows-特定问题)
9. [Linux 特定问题](#linux-特定问题)
10. [获取更多帮助](#获取更多帮助)

---

## 快速诊断

### 使用诊断脚本

创建 `diagnose.py`:

```python
#!/usr/bin/env python3
"""
CatchCore 诊断工具 - 快速诊断部署环境
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python():
    """检查 Python 版本"""
    print("📌 Python 检查")
    print(f"  • 版本: {sys.version}")
    print(f"  • 路径: {sys.executable}")

    # 检查版本
    if sys.version_info < (3, 10):
        print("  ⚠️  建议使用 Python 3.10 或更高版本")
    else:
        print("  ✅ Python 版本正确")
    print()

def check_dependencies():
    """检查关键依赖"""
    print("📌 依赖检查")

    dependencies = [
        'fastapi',
        'sqlalchemy',
        'uvicorn',
        'pydantic',
        'pytest',
    ]

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - 未安装")
    print()

def check_database():
    """检查数据库连接"""
    print("📌 数据库检查")

    try:
        from app.database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("  ✅ 数据库连接成功")
    except Exception as e:
        print(f"  ❌ 数据库连接失败: {e}")
    print()

def check_environment():
    """检查环境变量"""
    print("📌 环境变量检查")

    required_vars = ['DATABASE_URL', 'SECRET_KEY']

    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var} - 已设置")
        else:
            print(f"  ❌ {var} - 未设置")
    print()

def check_directories():
    """检查目录结构"""
    print("📌 目录检查")

    required_dirs = ['app', 'data', 'logs', 'tests']

    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ - 不存在")
    print()

def main():
    print("\n" + "="*50)
    print("CatchCore 诊断工具")
    print("="*50 + "\n")

    check_python()
    check_environment()
    check_dependencies()
    check_directories()
    check_database()

    print("诊断完成!")

if __name__ == '__main__':
    main()
```

运行诊断:

```bash
python3 diagnose.py
```

---

## Python 和环境问题

### 问题 1: "python3: command not found"

**症状:**
```
$ python3
python3: command not found
```

**原因:** Python 未安装或不在 PATH 中

**解决方案:**

```bash
# 检查 Python 是否已安装
which python
python --version

# 如果都不行，安装 Python
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip

# Windows
# 从 https://www.python.org/downloads/ 下载并安装
# 安装时必须勾选 "Add Python to PATH"
```

**验证:**
```bash
python3 --version
# 应该输出: Python 3.10.x 或更高
```

---

### 问题 2: "ModuleNotFoundError" 或 "ImportError"

**症状:**
```
ModuleNotFoundError: No module named 'fastapi'
ImportError: cannot import name 'xxx' from 'yyy'
```

**原因:**
1. 虚拟环境未激活
2. 依赖未安装
3. 虚拟环境损坏

**解决方案:**

```bash
# 1. 检查虚拟环境是否已激活
which python
# 应该输出虚拟环境路径，例如:
# /path/to/project/venv/bin/python

# 2. 激活虚拟环境
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows

# 3. 验证激活成功 (应该看到 (venv) 前缀)
echo $VIRTUAL_ENV

# 4. 重新安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 5. 如果仍然失败，重建虚拟环境
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**快速修复:**
```bash
# 清理所有缓存并重新安装
pip cache purge
pip install -r requirements.txt --force-reinstall
```

---

### 问题 3: "No module named 'app'"

**症状:**
```
ModuleNotFoundError: No module named 'app'
```

**原因:** 没有在正确的目录中运行

**解决方案:**

```bash
# 检查当前目录
pwd

# 应该输出: /path/to/CatchCore/backend

# 如果不对，进入正确目录
cd /path/to/CatchCore/backend

# 检查目录结构
ls -la
# 应该看到:
# app/
# tests/
# venv/
# requirements.txt
# .env
```

---

## 依赖和包问题

### 问题 4: pip 安装缓慢或超时

**症状:**
```
Downloading package...  (这会花很长时间)
ERROR: Failed building wheel for package
```

**原因:** 网络问题或依赖包过大

**解决方案:**

```bash
# 方法 1: 使用国内镜像 (推荐中国用户)

# 阿里云镜像
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 清华大学镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 腾讯云镜像
pip install -i https://mirrors.cloud.tencent.com/pypi/simple -r requirements.txt

# 方法 2: 增加超时时间
pip install --default-timeout=1000 -r requirements.txt

# 方法 3: 分开安装不同的包
pip install fastapi
pip install sqlalchemy
pip install uvicorn
# ... 逐个安装
```

**永久配置 (推荐):**

创建或编辑 `~/.pip/pip.conf`:

```ini
[global]
# 中国用户推荐使用阿里云镜像
index-url = https://mirrors.aliyun.com/pypi/simple/

# 其他配置
timeout = 120
```

**验证:**
```bash
pip config list
```

---

### 问题 5: "ERROR: Could not find a version that satisfies the requirement"

**症状:**
```
ERROR: Could not find a version that satisfies the requirement xxx
No matching distribution found for xxx
```

**原因:**
1. 包名错误
2. 版本不兼容
3. Python 版本不支持

**解决方案:**

```bash
# 1. 检查包名
pip search fastapi  # 搜索包

# 2. 更新 requirements.txt 中的版本
# 从:
fastapi==0.95.0

# 改为:
fastapi==0.104.0

# 3. 使用灵活版本号
fastapi>=0.95.0,<1.0.0

# 4. 升级 pip
pip install --upgrade pip setuptools wheel
```

---

### 问题 6: "distutils.errors.DistutilsError"

**症状:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**原因:** Windows 缺少 C++ 编译工具

**解决方案:**

```powershell
# Windows 用户

# 方法 1: 安装 Visual Studio Build Tools
# 下载: https://visualstudio.microsoft.com/downloads/
# 选择 "Desktop development with C++"

# 方法 2: 使用预编译的 wheel
pip install --only-binary :all: -r requirements.txt

# 方法 3: 使用 Conda
conda install fastapi sqlalchemy uvicorn
```

---

## 数据库问题

### 问题 7: "sqlite3.OperationalError: database is locked"

**症状:**
```
sqlite3.OperationalError: database is locked
```

**原因:** 另一个进程正在使用数据库

**解决方案:**

```bash
# 1. 找到并关闭占用数据库的进程
# Linux/macOS
lsof data/catchcore.db
kill -9 <PID>

# Windows
tasklist | findstr python
taskkill /PID <PID> /F

# 2. 删除锁文件 (如果存在)
rm data/catchcore.db-journal
rm data/catchcore.db-wal

# 3. 使用 WAL 模式来改进并发
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('data/catchcore.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.close()
EOF
```

---

### 问题 8: "postgresql: FATAL: Ident authentication failed"

**症状:**
```
postgresql: FATAL: Ident authentication failed for user 'postgres'
```

**原因:** PostgreSQL 认证配置问题

**解决方案:**

```bash
# 1. 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 2. 启动 PostgreSQL
sudo systemctl start postgresql

# 3. 修改 pg_hba.conf 文件
# 通常位置: /etc/postgresql/*/main/pg_hba.conf

# 找到这一行:
# local   all             postgres                                ident

# 改为:
# local   all             postgres                                trust

# 4. 重启 PostgreSQL
sudo systemctl restart postgresql

# 5. 重置密码
sudo -u postgres psql
ALTER USER postgres PASSWORD 'new_password';
\q
```

**验证:**
```bash
psql -U postgres -d postgres
# 应该成功连接
```

---

### 问题 9: "could not connect to server: Connection refused"

**症状:**
```
could not connect to server: Connection refused
Is the server running on host "localhost" (127.0.0.1) and accepting TCP connections on port 5432?
```

**原因:** PostgreSQL 未运行

**解决方案:**

```bash
# 检查服务状态
sudo systemctl status postgresql

# 启动服务
sudo systemctl start postgresql

# 启用开机自启
sudo systemctl enable postgresql

# 验证连接
psql -h localhost -U postgres
```

---

### 问题 10: 数据库表不存在

**症状:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable)
relation "user" does not exist
```

**原因:** 数据库表未创建

**解决方案:**

```bash
# 重新初始化数据库
python3 << 'EOF'
from app.database import Base, engine
from app.models import user, task, asset, vulnerability, poc

# 创建所有表
Base.metadata.create_all(bind=engine)
print("✅ 数据库表已创建")
EOF

# 或使用 Alembic 迁移
python3 -m alembic upgrade head
```

---

## 运行时问题

### 问题 11: "address already in use"

**症状:**
```
OSError: [Errno 98] Address already in use
```

**原因:** 端口已被占用

**解决方案:**

```bash
# 方法 1: 使用不同的端口
python3 -m uvicorn app.main:app --port 8001

# 方法 2: 找出占用端口的进程并关闭

# Linux/macOS
lsof -i :8000  # 列出使用 8000 端口的进程
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**快速修复:**
```bash
# 在当前终端中，按 Ctrl+C 停止应用
# 然后重新启动
```

---

### 问题 12: 应用启动缓慢

**症状:**
```
应用需要 30+ 秒才能启动
```

**原因:**
1. 磁盘 I/O 缓慢
2. 数据库连接池初始化
3. 导入大型模块

**解决方案:**

```bash
# 1. 检查磁盘速度
# Linux
sudo hdparm -t /dev/sda

# 2. 使用 SSD 而不是 HDD

# 3. 禁用未使用的功能
# 在 app/main.py 中注释掉不需要的中间件

# 4. 使用 --reload-delay 延迟重载
python3 -m uvicorn app.main:app --reload --reload-delay 2

# 5. 预加载依赖
python3 << 'EOF'
# 这会导入所有模块到内存中
import app.main
print("✅ 模块已预加载")
EOF
```

---

### 问题 13: 内存持续增长 (内存泄漏)

**症状:**
```
应用运行一段时间后，内存使用不断增加
```

**原因:**
1. 数据库连接未关闭
2. 缓存未清理
3. 循环引用

**解决方案:**

```python
# 在 app/main.py 中添加内存监控
from fastapi import FastAPI
import psutil
import os

app = FastAPI()

@app.get("/memory")
async def get_memory_usage():
    """获取内存使用情况"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return {
        "rss": memory_info.rss / 1024 / 1024,  # MB
        "vms": memory_info.vms / 1024 / 1024,  # MB
        "percent": process.memory_percent()
    }

# 检查内存泄漏
# curl http://localhost:8000/memory
```

**修复:**

```python
# 确保正确关闭数据库连接
from app.database import SessionLocal

@app.on_event("shutdown")
async def shutdown_event():
    # 清理资源
    pass

# 使用依赖注入确保连接正确关闭
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### 问题 14: API 返回 500 错误

**症状:**
```
Internal Server Error
```

**原因:** 应用代码异常

**解决方案:**

```bash
# 1. 查看错误日志
tail -f logs/catchcore.log

# 2. 启用详细错误输出
# 在 .env 中设置
DEBUG=True
LOG_LEVEL=DEBUG

# 3. 使用 Postman/Insomnia 测试 API
# 查看详细的错误响应

# 4. 检查关键日志
grep "ERROR" logs/catchcore.log
grep "Traceback" logs/catchcore.log
```

**常见原因和修复:**

```python
# 原因 1: 数据库查询错误
try:
    user = db.query(User).filter(User.id == user_id).first()
except Exception as e:
    logger.error(f"数据库查询错误: {e}")
    return {"error": "数据库查询失败"}

# 原因 2: 输入验证失败
from pydantic import BaseModel, ValidationError

class UserCreate(BaseModel):
    username: str
    email: str

try:
    user_data = UserCreate(**request_data)
except ValidationError as e:
    logger.error(f"验证错误: {e}")
    return {"error": "输入数据不正确"}
```

---

## 网络和连接问题

### 问题 15: "No module named 'app.main'"

**症状:**
```
ModuleNotFoundError: No module named 'app.main'
```

**原因:** 项目结构不正确

**解决方案:**

```bash
# 验证目录结构
tree -L 2 CatchCore/backend/

# 应该如下:
# CatchCore/backend/
# ├── app/
# │   ├── __init__.py
# │   ├── main.py
# │   ├── models/
# │   ├── services/
# │   └── ...
# ├── tests/
# ├── requirements.txt
# └── .env

# 如果 __init__.py 缺失，创建它们
touch app/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
```

---

### 问题 16: CORS 错误

**症状:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**原因:** CORS 配置不正确

**解决方案:**

```python
# 在 app/main.py 中配置 CORS
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**或在 .env 中配置:**

```ini
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

---

### 问题 17: SSL/TLS 证书错误

**症状:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**原因:** SSL 证书问题

**解决方案:**

```bash
# 方法 1: 禁用 SSL 验证 (仅用于开发)
export REQUESTS_CA_BUNDLE=""
export SSL_NO_VERIFY=1

# 方法 2: 使用系统证书
# macOS
/Applications/Python\ 3.x/Install\ Certificates.command

# 方法 3: 指定 CA 证书
export REQUESTS_CA_BUNDLE=/path/to/cacert.pem

# 方法 4: 更新证书
pip install -U certifi
```

---

## 性能问题

### 问题 18: 数据库查询缓慢

**症状:**
```
查询需要 5+ 秒
```

**原因:**
1. 缺少数据库索引
2. N+1 查询问题
3. 查询语句不优化

**解决方案:**

```python
# 1. 添加索引
from sqlalchemy import Index

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, index=True)  # 添加索引
    email = Column(String, unique=True, index=True)

# 2. 使用 eager loading
# 错误方式 (N+1 查询)
users = db.query(User).all()
for user in users:
    print(user.tasks)  # 每个用户都会查询一次 tasks

# 正确方式
from sqlalchemy.orm import joinedload
users = db.query(User).options(joinedload(User.tasks)).all()

# 3. 使用查询分析
import time

start = time.time()
result = db.query(User).filter(...).all()
elapsed = time.time() - start

print(f"查询耗时: {elapsed:.2f}s")
```

**添加性能监控:**

```python
from fastapi import FastAPI
import time
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_performance(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(f"{request.url.path} - 耗时: {process_time:.2f}s")

    if process_time > 1.0:  # 超过 1 秒
        logger.warning(f"⚠️ 慢查询: {request.url.path}")

    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

## Windows 特定问题

### 问题 19: PowerShell 执行策略错误

**症状:**
```
script is not digitally signed
```

**原因:** PowerShell 执行策略限制

**解决方案:**

```powershell
# 查看当前执行策略
Get-ExecutionPolicy

# 修改为允许本地脚本运行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 验证
Get-ExecutionPolicy
```

---

### 问题 20: venv 激活脚本不工作

**症状:**
```
'.\venv\Scripts\Activate.ps1' cannot be loaded
```

**原因:** 执行策略问题

**解决方案:**

```powershell
# 方法 1: 修改执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 方法 2: 使用 cmd.exe 激活
.\venv\Scripts\activate.bat

# 方法 3: 使用完整路径
& '.\venv\Scripts\Activate.ps1'
```

---

## Linux 特定问题

### 问题 21: "Permission denied" 权限错误

**症状:**
```
Permission denied: './venv/bin/python'
```

**原因:** 文件权限问题

**解决方案:**

```bash
# 修复权限
chmod +x venv/bin/python
chmod +x venv/bin/pip

# 或修复整个目录
chmod -R +x venv/bin/

# 修复项目目录权限
sudo chown -R $USER:$USER ~/projects/CatchCore
chmod -R 755 ~/projects/CatchCore
```

---

### 问题 22: "command not found: python3"

**症状:**
```
python3: command not found
```

**原因:** Python 未正确安装

**解决方案:**

```bash
# 检查 Python 是否已安装
which python3
ls -la /usr/bin/python*

# 安装 Python
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip

# 创建符号链接 (如果需要)
sudo ln -s /usr/bin/python3.11 /usr/bin/python3

# 验证
python3 --version
```

---

## 获取更多帮助

### 如何提交有效的问题报告

当向开发者报告问题时，请包括以下信息:

```markdown
## 问题描述
[清晰描述你遇到的问题]

## 操作系统
- OS: Ubuntu 20.04 / macOS 12 / Windows 11
- Architecture: x86_64

## Python 版本
[输出: python3 --version]

## 虚拟环境
[输出: which python 或 where python]

## 错误消息
[完整的错误堆栈跟踪]

## 重现步骤
1. ...
2. ...
3. ...

## 期望行为
[你期望会发生什么]

## 实际行为
[实际发生了什么]

## 诊断输出
[运行 python3 diagnose.py 的输出]
```

### 获取支持的渠道

1. **GitHub Issues:** [https://github.com/yourusername/CatchCore/issues](https://github.com/yourusername/CatchCore/issues)
2. **GitHub Discussions:** [https://github.com/yourusername/CatchCore/discussions](https://github.com/yourusername/CatchCore/discussions)
3. **邮件:** support@catchcore.local
4. **Wiki:** [https://github.com/yourusername/CatchCore/wiki](https://github.com/yourusername/CatchCore/wiki)

---

## 快速查找

| 症状 | 常见原因 | 快速修复 |
|------|--------|--------|
| ModuleNotFoundError | 虚拟环境未激活 | `source venv/bin/activate` |
| Address already in use | 端口被占用 | 使用 `-port 8001` 或 `kill` 进程 |
| No such file or directory | 目录错误 | `cd CatchCore/backend` |
| OperationalError | 数据库问题 | 重建虚拟环境和数据库 |
| 500 错误 | 应用异常 | 检查日志 `tail -f logs/catchcore.log` |
| 缓慢运行 | 资源不足 | 检查 CPU/内存，使用性能监控 |
| 导入错误 | 缺少依赖 | `pip install -r requirements.txt` |

---

**最后更新:** 2025 年 11 月 12 日
**版本:** 1.0.0
