# CatchCore 快速参考指南

## 📚 文档索引

| 文档 | 用途 | 读者 |
|------|------|------|
| **README.md** | 项目介绍、快速开始 | 所有人 |
| **FIRST_STEPS.md** | 首次使用指南 | 新用户 |
| **DEVELOPMENT.md** | 开发指南、编码规范 | 开发者 |
| **PROJECT_STATUS.md** | 项目进度、统计数据 | 项目经理 |
| **PHASE2_PROGRESS.md** | 第二阶段完成情况 | 开发者 |
| **NEXT_STEPS.md** | 下一步详细计划 | 开发者 |
| **QUICK_REFERENCE.md** | 本文件 - 快速参考 | 所有人 |

---

## 🚀 快速启动

### 使用 Docker Compose (推荐)

```bash
# 1. 进入项目目录
cd /Users/taowilliam/project/CatchCore

# 2. 启动所有服务
./start.sh
# 或
docker-compose up -d

# 3. 访问应用
# 前端: http://localhost:5173
# 后端: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# 前端 (新终端)
cd frontend
npm install
npm run dev
```

---

## 📝 常用命令

### Docker 操作

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# 进入容器
docker-compose exec backend bash
docker-compose exec postgres psql -U catchcore

# 停止服务
docker-compose down

# 重新启动
docker-compose restart backend
```

### 后端开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py

# 代码格式化
black app/

# 代码检查
flake8 app/
mypy app/

# 运行测试
pytest
pytest -v
pytest --cov
```

### 前端开发

```bash
# 安装依赖
npm install

# 开发服务器
npm run dev

# 生产构建
npm run build

# 代码检查
npm run lint

# 运行测试
npm test
```

---

## 🔑 默认凭证

| 服务 | 用户名 | 密码 | URL |
|------|--------|------|-----|
| PostgreSQL | catchcore | catchcore | localhost:5432 |
| Redis | - | - | localhost:6379 |
| InfluxDB | admin | admin | http://localhost:8086 |

---

## 🌐 API 端点速查

### 认证
```
POST   /api/v1/auth/register      注册
POST   /api/v1/auth/login         登录
POST   /api/v1/auth/refresh       刷新 token
```

### 资产管理
```
GET    /api/v1/assets             列表 (支持筛选/分页)
POST   /api/v1/assets             创建
GET    /api/v1/assets/{id}        详情
PUT    /api/v1/assets/{id}        更新
DELETE /api/v1/assets/{id}        删除
POST   /api/v1/assets/batch-import 批量导入
```

### 任务管理
```
GET    /api/v1/tasks              列表
POST   /api/v1/tasks              创建
GET    /api/v1/tasks/{id}         详情
DELETE /api/v1/tasks/{id}         删除
POST   /api/v1/tasks/{id}/start   启动
POST   /api/v1/tasks/{id}/pause   暂停
POST   /api/v1/tasks/{id}/resume  恢复
POST   /api/v1/tasks/{id}/cancel  取消
GET    /api/v1/tasks/{id}/logs    日志
```

### 漏洞管理
```
GET    /api/v1/vulnerabilities    列表
GET    /api/v1/vulnerabilities/{id} 详情
PUT    /api/v1/vulnerabilities/{id} 更新
DELETE /api/v1/vulnerabilities/{id} 删除
GET    /api/v1/vulnerabilities/stats/summary 统计
```

---

## 🧪 测试 API

### 使用 curl

```bash
# 获取 token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.data.access_token')

# 创建资产
curl -X POST http://localhost:8000/api/v1/assets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.100",
    "hostname": "server1",
    "department": "IT"
  }'

# 获取资产列表
curl -X GET "http://localhost:8000/api/v1/assets?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

### 使用 Postman

1. 导入 API 集合 (http://localhost:8000/docs)
2. 在环境变量中设置 `token`
3. 测试各个端点

---

## 📊 项目结构

```
CatchCore/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # 业务逻辑
│   │   ├── core/              # 核心配置
│   │   ├── utils/             # 工具函数
│   │   └── main.py            # 应用入口
│   ├── requirements.txt        # 依赖
│   └── Dockerfile             # 容器配置
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── pages/             # 页面
│   │   ├── components/        # 组件
│   │   ├── services/          # API 服务
│   │   ├── store/             # Redux 状态
│   │   ├── types/             # 类型定义
│   │   ├── hooks/             # 自定义 hooks
│   │   └── styles/            # 样式
│   ├── package.json           # 依赖
│   └── Dockerfile             # 容器配置
│
├── docker-compose.yml         # 容器编排
├── README.md                  # 项目文档
└── DEVELOPMENT.md             # 开发指南
```

---

## 🔧 常见问题解决

### 问题：数据库连接失败

```bash
# 检查 PostgreSQL 容器
docker-compose ps postgres

# 查看日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres

# 检查连接字符串
# DATABASE_URL=postgresql://catchcore:catchcore@postgres:5432/catchcore_db
```

### 问题：前端无法连接后端

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查 CORS 配置
# 在 backend/.env 中更新 CORS_ORIGINS

# 清除浏览器缓存
# Ctrl+Shift+Delete (Chrome)
```

### 问题：Redis 连接失败

```bash
# 检查 Redis 容器
docker-compose ps redis

# 测试 Redis 连接
docker-compose exec redis redis-cli ping

# 查看 Redis 日志
docker-compose logs redis
```

---

## 📈 性能优化建议

### 数据库
- 添加索引到常用查询字段
- 使用连接池优化并发
- 定期清理过期日志

### 缓存
- Redis 缓存 API 响应
- 前端使用 LocalStorage 缓存用户偏好
- 指纹库缓存到内存

### 扫描
- 使用异步任务队列 (Celery)
- 扫描结果分页返回
- 大结果集使用 WebSocket 流式传输

---

## 📚 学习资源

### 后端
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Celery 文档](https://docs.celeryproject.io/)

### 前端
- [React 文档](https://react.dev/)
- [Ant Design 文档](https://ant.design/)
- [Redux Toolkit 文档](https://redux-toolkit.js.org/)

### 安全
- [OWASP 安全指南](https://owasp.org/)
- [nmap 官方文档](https://nmap.org/book/)

---

## 🎯 下一步推荐

1. **立即做:**
   - 启动应用并测试登录
   - 创建几个测试资产
   - 创建扫描任务

2. **本周做:**
   - 实现 Celery 任务队列
   - 集成 nmap 扫描
   - 添加 WebSocket 实时推送

3. **本月做:**
   - 完成所有扫描功能
   - 添加单元测试
   - 优化性能

---

## 📞 获取帮助

### 文档
- 查看 DEVELOPMENT.md 了解开发指南
- 查看 FIRST_STEPS.md 了解使用说明
- 查看 API 文档: http://localhost:8000/docs

### 调试
- 查看日志: `docker-compose logs -f [service]`
- 使用 Postman 测试 API
- 使用浏览器开发工具检查前端

### 社区
- GitHub Issues (如果使用 GitHub)
- 开发者论坛
- Slack/Discord 社区

---

## ✅ 代码质量检查清单

在提交代码前：

- [ ] 代码通过 linter (black, flake8)
- [ ] 类型检查通过 (mypy)
- [ ] 单元测试通过
- [ ] 文档已更新
- [ ] 没有硬编码的凭证
- [ ] 错误处理完整
- [ ] 性能满足预期

---

## 🔐 安全检查清单

部署前：

- [ ] 更改所有默认密码
- [ ] 配置 HTTPS/SSL
- [ ] 设置防火墙规则
- [ ] 启用日志审计
- [ ] 配置备份策略
- [ ] 运行安全扫描
- [ ] 更新所有依赖

---

**最后更新:** 2025-11-11
**适用版本:** v0.1.0+
