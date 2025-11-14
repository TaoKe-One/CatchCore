# CatchCore 文档指南

欢迎使用 CatchCore！所有的文档已经组织在 `docs/` 文件夹中。

## 📚 快速导航

### 🆕 新手推荐

如果你是第一次使用，请按照以下顺序：

1. **[docs/BEGINNER_GUIDE.md](./docs/BEGINNER_GUIDE.md)** - 完全新手指南
   - 5-10 分钟快速开始
   - 详细的逐步说明
   - 终端基础知识
   - 常见新手问题

2. **[docs/DEPLOYMENT_README.md](./docs/DEPLOYMENT_README.md)** - 部署文档导航
   - 4 种场景选择
   - 快速查找表
   - 最佳实践

### 📖 详细文档

- **[docs/DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md)** - 完整部署手册
  - 系统要求检查
  - 详细部署步骤
  - 环境变量配置
  - 数据库配置（SQLite/PostgreSQL）
  - 生产环境部署
  - SSL/HTTPS 配置
  - 监控和维护

- **[docs/TROUBLESHOOTING_GUIDE.md](./docs/TROUBLESHOOTING_GUIDE.md)** - 故障排查指南
  - 20+ 常见问题及解决方案
  - 诊断工具
  - 按症状快速查找
  - Windows/Linux 特定问题

### 🧪 测试文档

- **[docs/TEST_SUITE_README.md](./docs/TEST_SUITE_README.md)** - 测试套件文档
  - 测试框架说明
  - 如何运行测试
  - 覆盖率报告
  - 最佳实践

- **[docs/PHASE6_DOCUMENTATION_INDEX.md](./docs/PHASE6_DOCUMENTATION_INDEX.md)** - Phase 6 文档索引
  - 测试项目完整总结
  - 490+ 测试的详细信息
  - 文档导航

## 🚀 快速开始（3 分钟）

### Linux/macOS 用户

```bash
# 1. 克隆项目
git clone https://github.com/TaoKe-One/CatchCore.git
cd CatchCore/backend

# 2. 运行自动化脚本
bash ../../setup.sh

# 3. 启动应用
python -m uvicorn app.main:app --reload

# 4. 访问 API 文档
# 打开浏览器访问: http://localhost:8000/docs
```

### Windows 用户

```powershell
# 1. 克隆项目
git clone https://github.com/TaoKe-One/CatchCore.git
cd CatchCore\backend

# 2. 运行自动化脚本
.\..\..\setup.ps1

# 3. 启动应用
python -m uvicorn app.main:app --reload

# 4. 访问 API 文档
# 打开浏览器访问: http://localhost:8000/docs
```

## 📋 按场景查找文档

| 你的情况 | 推荐文档 |
|---------|--------|
| 我是编程新手，从未部署过 | [BEGINNER_GUIDE.md](./docs/BEGINNER_GUIDE.md) |
| 我要在本机快速尝试 | [BEGINNER_GUIDE.md](./docs/BEGINNER_GUIDE.md) + [DEPLOYMENT_README.md](./docs/DEPLOYMENT_README.md) |
| 我要完整学习部署流程 | [DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md) |
| 我要部署到生产环境 | [DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md) 的生产环境部分 |
| 我遇到了问题 | [TROUBLESHOOTING_GUIDE.md](./docs/TROUBLESHOOTING_GUIDE.md) |
| 我想了解测试 | [TEST_SUITE_README.md](./docs/TEST_SUITE_README.md) |
| 我想查看 Phase 6 测试总结 | [PHASE6_DOCUMENTATION_INDEX.md](./docs/PHASE6_DOCUMENTATION_INDEX.md) |

## 🔧 自动化部署脚本

项目根目录中提供了两个自动化脚本：

- **setup.sh** - Linux/macOS 用户
  ```bash
  bash setup.sh
  ```

- **setup.ps1** - Windows 用户
  ```powershell
  .\setup.ps1
  ```

这些脚本会自动完成：
- Python 版本检查
- 虚拟环境创建
- 依赖安装
- 数据库初始化
- 环境变量配置

## 📞 获取帮助

### 自助查询

1. **查看错误日志**
   ```bash
   tail -f logs/catchcore.log
   ```

2. **运行诊断工具**
   ```bash
   python3 diagnose.py
   ```

3. **查看相应文档**
   - 遇到问题 → [TROUBLESHOOTING_GUIDE.md](./docs/TROUBLESHOOTING_GUIDE.md)
   - 部署问题 → [DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md)
   - 测试问题 → [TEST_SUITE_README.md](./docs/TEST_SUITE_README.md)

### 联系我们

- **GitHub Issues:** [报告问题](https://github.com/TaoKe-One/CatchCore/issues)
- **GitHub Discussions:** [讨论问题](https://github.com/TaoKe-One/CatchCore/discussions)
- **项目主页:** [https://github.com/TaoKe-One/CatchCore](https://github.com/TaoKe-One/CatchCore)

## 🌐 访问应用

部署成功后，可以通过以下地址访问：

| URL | 说明 |
|-----|------|
| http://localhost:8000 | 应用首页 |
| http://localhost:8000/docs | Swagger API 文档 |
| http://localhost:8000/redoc | ReDoc API 文档 |
| http://localhost:8000/api/v1 | API 基础路径 |
| http://localhost:8000/health | 健康检查 |

## 📊 项目信息

- **项目名称:** CatchCore
- **描述:** Advanced Vulnerability Scanning Platform（高级漏洞扫描平台）
- **仓库:** [https://github.com/TaoKe-One/CatchCore](https://github.com/TaoKe-One/CatchCore)
- **文档目录:** [docs/](./docs/)

## 🎓 学习路径

### 初级（新手）
1. 阅读 [BEGINNER_GUIDE.md](./docs/BEGINNER_GUIDE.md)
2. 运行 setup.sh 或 setup.ps1
3. 启动应用并访问 API 文档

### 中级（开发者）
1. 阅读 [DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md)
2. 理解各个配置项
3. 运行测试：`python -m pytest tests/ -v`

### 高级（运维/架构）
1. 阅读 [DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md) 生产环境部分
2. 配置 PostgreSQL 和 Nginx
3. 设置 SSL 和监控

## 🆘 常见问题速查

| 问题 | 解决文档 |
|------|--------|
| Python 未安装 | [BEGINNER_GUIDE.md](./docs/BEGINNER_GUIDE.md#第一步-准备工作) |
| pip 安装太慢 | [TROUBLESHOOTING_GUIDE.md](./docs/TROUBLESHOOTING_GUIDE.md#问题-4-pip-安装缓慢或超时) |
| 虚拟环境问题 | [TROUBLESHOOTING_GUIDE.md](./docs/TROUBLESHOOTING_GUIDE.md#问题-2-modulenotfounderror-或-importerror) |
| 端口被占用 | [TROUBLESHOOTING_GUIDE.md](./docs/TROUBLESHOOTING_GUIDE.md#问题-11-address-already-in-use) |
| 数据库错误 | [TROUBLESHOOTING_GUIDE.md](./docs/TROUBLESHOOTING_GUIDE.md#数据库问题) |

## ✨ 特色功能

### 完整的测试套件
- 490+ 单元测试和集成测试
- 详见 [TEST_SUITE_README.md](./docs/TEST_SUITE_README.md)
- 详见 [PHASE6_DOCUMENTATION_INDEX.md](./docs/PHASE6_DOCUMENTATION_INDEX.md)

### 自动化部署
- 一键部署脚本
- 自动环境检查
- 彩色输出和进度提示

### 详细文档
- 完全新手友好
- 多层次覆盖（快速开始到生产部署）
- 包含 20+ 常见问题解决方案

### 生产就绪
- Gunicorn + Nginx 配置
- SSL/HTTPS 支持
- 日志、备份和监控

## 📈 项目统计

- **测试用例:** 490+
- **测试代码行数:** 7,739+
- **文档数量:** 7
- **API 端点:** 55+
- **支持工具:** 5 种安全扫描工具

## 🎉 开始使用

**新手用户：** 立即开始 [docs/BEGINNER_GUIDE.md](./docs/BEGINNER_GUIDE.md)

**经验用户：** 查看 [docs/DEPLOYMENT_README.md](./docs/DEPLOYMENT_README.md)

**遇到问题：** 参考 [docs/TROUBLESHOOTING_GUIDE.md](./docs/TROUBLESHOOTING_GUIDE.md)

---

祝你使用愉快！如有任何问题，欢迎提交 Issue 或 Discussion。

**Happy hacking!** 🚀
