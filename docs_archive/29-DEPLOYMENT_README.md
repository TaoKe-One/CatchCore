# CatchCore 部署文档总览

欢迎！这个目录包含了 CatchCore 项目的所有部署和配置文档。

## 📚 文档导航

### 🆕 新手推荐

**从这里开始！**

- **[BEGINNER_GUIDE.md](./BEGINNER_GUIDE.md)** - 👶 完全新手指南
  - 简单易懂的步骤
  - 10 分钟快速部署
  - 常见新手问题解答
  - **推荐新手首先阅读**

### 📖 详细部署指南

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - 📘 完整部署手册
  - 系统要求检查
  - 逐步详细部署流程
  - 环境变量配置
  - 数据库设置
  - 生产环境部署
  - Nginx + Gunicorn 配置
  - SSL 证书配置
  - **推荐仔细阅读一遍**

### 🔧 故障排查

- **[TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)** - 🛠️ 完整故障排查指南
  - 20+ 常见问题及解决方案
  - 分类详细说明
  - 快速诊断工具
  - Windows/Linux 特定问题
  - **遇到问题时查阅这份文档**

### ⚡ 自动化脚本

#### Linux/macOS 用户
```bash
bash setup.sh
```

#### Windows 用户
```powershell
.\setup.ps1
```

这些脚本会自动完成：
- Python 版本检查
- 虚拟环境创建
- 依赖安装
- 数据库初始化
- 环境配置

## 🚀 快速开始 (3 种方式)

### 方式 1: 最简单 (推荐新手)

```bash
cd CatchCore/backend

# Linux/macOS
bash ../../setup.sh

# Windows
.\..\..\setup.ps1
```

等待脚本完成，然后：
```bash
python -m uvicorn app.main:app --reload
```

### 方式 2: 手动步骤

```bash
cd CatchCore/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python3 << 'PYTHON'
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
PYTHON

# 运行应用
python -m uvicorn app.main:app --reload
```

### 方式 3: 使用 Docker (最简洁)

```bash
# 需要先安装 Docker
docker build -t catchcore .
docker run -p 8000:8000 catchcore
```

## 📋 部署检查清单

### 部署前检查
- [ ] Python 3.10+ 已安装
- [ ] pip 已升级
- [ ] 虚拟环境已创建
- [ ] 依赖已安装
- [ ] .env 文件已创建
- [ ] 数据库已初始化

### 部署后检查
- [ ] 应用可以启动
- [ ] 健康检查端点响应正常
- [ ] API 文档可以访问
- [ ] 数据库连接正常
- [ ] 测试通过

### 生产部署检查
- [ ] DEBUG=False
- [ ] SECRET_KEY 已改为强密钥
- [ ] ENVIRONMENT=production
- [ ] SSL 证书已配置
- [ ] 防火墙规则已配置
- [ ] 日志和备份已设置

## 🌐 访问应用

部署完成后，访问：

| URL | 说明 |
|-----|------|
| http://localhost:8000 | 应用首页 |
| http://localhost:8000/docs | API 交互式文档 |
| http://localhost:8000/redoc | API 备选文档 |
| http://localhost:8000/api/v1 | API 基础路径 |
| http://localhost:8000/health | 健康检查 |

## 🔍 诊断工具

遇到问题？运行诊断工具：

```bash
python3 diagnose.py
```

这会检查：
- Python 版本
- 依赖安装情况
- 环境变量
- 数据库连接
- 目录结构

## 📊 文档快速参考

### 按用途查找

| 需求 | 文档 |
|------|------|
| 我是完全新手 | [BEGINNER_GUIDE.md](./BEGINNER_GUIDE.md) |
| 我要从头部署 | [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) |
| 我遇到了问题 | [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md) |
| 我要部署到生产 | [DEPLOYMENT_GUIDE.md#生产环境部署](./DEPLOYMENT_GUIDE.md#生产环境部署) |
| 我需要 SSL 证书 | [DEPLOYMENT_GUIDE.md#获取-ssl-证书](./DEPLOYMENT_GUIDE.md#获取-ssl-证书) |
| 我需要配置数据库 | [DEPLOYMENT_GUIDE.md#数据库配置](./DEPLOYMENT_GUIDE.md#数据库配置) |

### 按操作系统查找

| 系统 | 推荐方式 | 文档 |
|------|--------|------|
| Windows 新手 | 运行 setup.ps1 | [BEGINNER_GUIDE.md](./BEGINNER_GUIDE.md) |
| macOS 新手 | 运行 setup.sh | [BEGINNER_GUIDE.md](./BEGINNER_GUIDE.md) |
| Linux 新手 | 运行 setup.sh | [BEGINNER_GUIDE.md](./BEGINNER_GUIDE.md) |
| Windows 专业 | 手动部署 | [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) |
| Linux 专业 | Docker/Systemd | [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) |

## 🎯 典型场景

### 场景 1: 我是学生，想在本机学习

```bash
# 推荐文档: BEGINNER_GUIDE.md
# 步骤:
1. 运行 setup.sh (或 setup.ps1)
2. python -m uvicorn app.main:app --reload
3. 访问 http://localhost:8000/docs
```

### 场景 2: 我是开发者，想参与开发

```bash
# 推荐文档: DEPLOYMENT_GUIDE.md
# 步骤:
1. 手动部署 (按照详细步骤)
2. 运行测试
3. 开始开发
```

### 场景 3: 我需要部署到服务器

```bash
# 推荐文档: DEPLOYMENT_GUIDE.md#生产环境部署
# 步骤:
1. 配置服务器
2. 设置 PostgreSQL
3. 配置 Nginx
4. 配置 SSL
5. 使用 Systemd/Supervisor 管理
```

### 场景 4: 我遇到了部署问题

```bash
# 推荐文档: TROUBLESHOOTING_GUIDE.md
# 步骤:
1. 运行 diagnose.py
2. 查看错误消息
3. 在故障排查指南中找到对应问题
4. 按照解决方案修复
```

## 📞 获取帮助

### 自助查询

1. **检查错误信息** - 通常会直接告诉你问题
2. **查看日志:**
   ```bash
   tail -f logs/catchcore.log
   ```

3. **运行诊断:**
   ```bash
   python3 diagnose.py
   ```

4. **查看故障排查指南:**
   - [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)

### 联系支持

- **GitHub Issues:** [报告 Bug](https://github.com/yourusername/CatchCore/issues)
- **GitHub Discussions:** [讨论问题](https://github.com/yourusername/CatchCore/discussions)
- **邮件:** support@catchcore.local
- **Wiki:** [项目 Wiki](https://github.com/yourusername/CatchCore/wiki)

## 🔐 安全建议

### 部署前必读

- ⚠️ 不要在代码中硬编码密钥
- ⚠️ 在生产环境中使用强 SECRET_KEY
- ⚠️ 启用 HTTPS/SSL
- ⚠️ 定期备份数据库
- ⚠️ 配置防火墙规则
- ⚠️ 定期更新依赖包

## 📈 部署架构参考

### 开发环境
```
本机 -> SQLite -> 开发服务器
```

### 生产环境 (推荐)
```
CDN -> Nginx -> Gunicorn (多进程) -> FastAPI -> PostgreSQL
```

## 🎓 学习资源

- **Python 教程:** https://docs.python.org/3/tutorial/
- **FastAPI 官方文档:** https://fastapi.tiangolo.com/
- **SQLAlchemy 官方文档:** https://docs.sqlalchemy.org/
- **PostgreSQL 官方文档:** https://www.postgresql.org/docs/
- **Nginx 官方文档:** https://nginx.org/en/docs/

## ✅ 完成标志

当你看到以下日志时，说明部署成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

打开浏览器访问 http://localhost:8000/docs，你应该看到交互式 API 文档。

---

## 📝 文档版本

| 文档 | 版本 | 更新日期 |
|------|------|--------|
| BEGINNER_GUIDE.md | 1.0 | 2025-11-12 |
| DEPLOYMENT_GUIDE.md | 1.0 | 2025-11-12 |
| TROUBLESHOOTING_GUIDE.md | 1.0 | 2025-11-12 |

---

## 🎉 下一步

**快速部署完成后，你可以：**

1. 📖 阅读 [API 文档](http://localhost:8000/docs)
2. 🧪 运行测试:
   ```bash
   python -m pytest tests/ -v
   ```

3. 📊 查看测试覆盖率:
   ```bash
   python -m pytest tests/ --cov=app --cov-report=html
   ```

4. 🔍 探索代码:
   - `app/main.py` - 应用入口
   - `app/models/` - 数据模型
   - `app/services/` - 业务逻辑
   - `app/routers/` - API 端点

5. 🚀 开始开发！

---

**祝你部署顺利！有问题随时查阅文档。** ✨
