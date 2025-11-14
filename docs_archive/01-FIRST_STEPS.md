# CatchCore 快速开始指南

欢迎使用 CatchCore！本文档将帮助您快速启动并开始使用该系统。

## 📋 前置要求

在开始之前，请确保已安装：

- Docker (推荐 20.10+)
- Docker Compose (推荐 2.0+)
- 或
- Node.js 18+ (本地开发)
- Python 3.10+ (本地开发)

检查安装：
```bash
docker --version
docker-compose --version
```

## 🚀 最快启动方式（推荐）

### 使用 Docker Compose 一键启动

```bash
# 1. 进入项目目录
cd /Users/taowilliam/project/CatchCore

# 2. 运行启动脚本
./start.sh

# 或使用 docker-compose 直接启动
docker-compose up -d
```

### 验证服务是否正常运行

```bash
# 查看运行中的容器
docker-compose ps

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
```

### 访问应用

启动成功后，您可以访问：

- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **Swagger 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc

### 默认登录信息

创建第一个用户前，您需要初始化数据库并创建测试用户：

```bash
# 进入后端容器
docker-compose exec backend bash

# 创建测试数据（Python 命令）
python -c "
from app.core.database import init_db
from app.core.security import get_password_hash
from app.models import User
import asyncio

async def setup():
    await init_db()
    print('Database initialized successfully!')

asyncio.run(setup())
"

# 或者通过 Python REPL
python
```

然后在登录页面输入测试凭证登录。

## 💻 本地开发

如果您想在本地开发而不使用 Docker：

### 后端本地开发

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，确保数据库配置正确

# 5. 启动开发服务器
python main.py
```

后端将在 http://localhost:8000 运行

### 前端本地开发

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 运行

## 📁 项目文件结构快览

```
CatchCore/
├── backend/              # 后端 FastAPI 应用
├── frontend/             # 前端 React 应用
├── docker-compose.yml    # Docker 编排配置
├── README.md             # 项目文档
├── DEVELOPMENT.md        # 开发指南
├── PROJECT_STATUS.md     # 项目进度
└── start.sh              # 启动脚本
```

## 🔧 常见操作

### 停止服务

```bash
docker-compose down
```

### 清除数据并重新启动

```bash
# 删除所有数据（包括数据库和缓存）
docker-compose down -v

# 重新启动
docker-compose up -d
```

### 查看特定服务的日志

```bash
# 查看后端日志
docker-compose logs -f backend

# 查看数据库日志
docker-compose logs -f postgres

# 查看所有日志
docker-compose logs -f
```

### 进入后端容器执行命令

```bash
docker-compose exec backend bash

# 或者直接执行 Python 命令
docker-compose exec backend python -c "print('Hello')"
```

## 📊 系统架构概览

```
┌─────────────────────────────────────────┐
│        前端 (React + TypeScript)         │
│      http://localhost:5173               │
└──────────────────┬──────────────────────┘
                   │
                   │ HTTP/REST
                   │
┌──────────────────▼──────────────────────┐
│        后端 (FastAPI + Python)          │
│      http://localhost:8000               │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┬────────────┐
        │          │          │            │
        ▼          ▼          ▼            ▼
    PostgreSQL   Redis    InfluxDB    其他服务
    (主数据库)  (缓存)   (时序数据)   (可选)
```

## 🔐 安全提示

### 本地开发

当前配置适合本地开发。生产环境必须：

1. **更改 SECRET_KEY**
   ```bash
   # 在 backend/.env 中更改
   SECRET_KEY=your-new-secret-key-here
   ```

2. **使用强密码**
   ```bash
   # 为数据库使用强密码
   # 修改 docker-compose.yml 中的 POSTGRES_PASSWORD
   ```

3. **启用 HTTPS**
   ```bash
   # 在生产环境中使用 SSL/TLS 证书
   # 配置 Nginx 反向代理
   ```

4. **更新 CORS 设置**
   ```bash
   # 在 backend/.env 中设置允许的源
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

## 📝 后续步骤

1. **创建您的第一个资产**
   - 访问 http://localhost:5173
   - 登录系统
   - 导航到"资产管理"页面
   - 添加您的第一个资产（IP 或域名）

2. **创建扫描任务**
   - 在"任务管理"页面创建新任务
   - 选择扫描类型
   - 配置扫描参数
   - 执行扫描

3. **查看漏洞报告**
   - 在"漏洞管理"页面查看发现的漏洞
   - 评估风险等级
   - 制定修复计划

## 🆘 故障排除

### 问题：容器无法启动

**解决方案**：
```bash
# 查看详细错误日志
docker-compose logs backend

# 确保端口未被占用
lsof -i :8000  # 检查 8000 端口
lsof -i :5173  # 检查 5173 端口
lsof -i :5432  # 检查 5432 端口

# 清除旧容器并重新启动
docker-compose down
docker-compose up -d --build
```

### 问题：数据库连接失败

**解决方案**：
```bash
# 检查 PostgreSQL 容器状态
docker-compose ps postgres

# 查看 PostgreSQL 日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### 问题：前端无法连接后端

**解决方案**：
```bash
# 检查网络连接
docker-compose exec frontend curl http://backend:8000/health

# 查看浏览器控制台错误
# F12 打开开发者工具，查看 Network 和 Console 标签页

# 检查 CORS 配置
# 后端日志中查看 CORS 相关错误
```

## 📚 更多资源

- [完整项目文档](README.md)
- [开发指南](DEVELOPMENT.md)
- [项目进度](PROJECT_STATUS.md)
- [API 文档](http://localhost:8000/docs)

## 💬 获取帮助

遇到问题？

1. 查看项目文档和开发指南
2. 检查容器日志
3. 提交 Issue 或 PR
4. 联系项目维护者

---

**祝您使用愉快！** 🎉

**最后更新**: 2025-11-11
