# CatchCore - 漏洞猎手的核心捕鼠器

让内网安全风险无处可逃

## 项目介绍

CatchCore 是一款综合性内网安全检测和运维工具，专门针对企业内部网络进行快速资产发现、识别、检测和漏洞评估。通过集成多个开源安全工具，实现自动化漏洞探测、修复验证和资产管理的完整闭环。

## 技术栈

### 前端
- React 18 + TypeScript
- Ant Design v5
- Redux Toolkit (状态管理)
- Vite (构建工具)
- Tailwind CSS + Less

### 后端
- Python 3.10+
- FastAPI
- SQLAlchemy ORM
- PostgreSQL
- Redis
- Celery (任务队列)

### 基础设施
- Docker + Docker Compose
- InfluxDB (时序数据)
- Elasticsearch (搜索引擎，可选)

## 快速开始

### 前置条件
- Docker 和 Docker Compose
- Node.js 18+ (本地开发)
- Python 3.10+ (本地开发)

### 使用 Docker Compose 启动

1. 克隆项目
```bash
git clone <repository-url>
cd CatchCore
```

2. 启动所有服务
```bash
docker-compose up -d
```

3. 初始化数据库
```bash
docker-compose exec backend python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

4. 访问应用
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 本地开发

#### 后端

1. 创建虚拟环境
```bash
cd backend
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库等信息
```

4. 运行应用
```bash
python main.py
```

#### 前端

1. 安装依赖
```bash
cd frontend
npm install
```

2. 启动开发服务器
```bash
npm run dev
```

3. 访问应用
http://localhost:5173

## 项目结构

```
CatchCore/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── core/          # 核心配置和工具
│   │   ├── models/        # 数据库模型
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── tests/             # 测试文件
│   ├── main.py            # 应用入口
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile         # 后端容器配置
├── frontend/
│   ├── src/
│   │   ├── components/    # React 组件
│   │   ├── pages/         # 页面
│   │   ├── services/      # API 服务
│   │   ├── store/         # Redux 状态管理
│   │   ├── types/         # TypeScript 类型
│   │   └── styles/        # 样式文件
│   ├── package.json       # Node 依赖
│   ├── vite.config.ts     # Vite 配置
│   └── Dockerfile         # 前端容器配置
├── docker-compose.yml     # Docker Compose 编排
└── README.md              # 项目文档
```

## 主要功能模块

### 已实现
- ✅ 用户管理和认证系统
- ✅ 数据库模型设计
- ✅ 基础 API 框架
- ✅ 前端框架和布局
- ✅ Docker 容器化

### 进行中
- 🔄 资产管理 CRUD
- 🔄 任务管理系统
- 🔄 漏洞管理

### 待实现
- ⏳ 端口扫描集成
- ⏳ 指纹识别引擎
- ⏳ POC 执行框架
- ⏳ 弱口令破解
- ⏳ 分布式部署
- ⏳ 报告生成

## API 文档

启动后端服务后，可访问 Swagger 文档：
http://localhost:8000/docs

## 开发指南

### 后端开发

1. 添加新的 API 路由：在 `app/api/` 目录下创建新的路由文件
2. 添加数据库模型：在 `app/models/` 目录下创建模型文件
3. 创建 Pydantic Schema：在 `app/schemas/` 目录下定义请求/响应格式

### 前端开发

1. 新建页面：在 `src/pages/` 目录下创建新的页面组件
2. 新建组件：在 `src/components/` 目录下创建可复用组件
3. 状态管理：使用 Redux Toolkit 在 `src/store/slices/` 中定义状态

## 测试

### 后端测试
```bash
cd backend
pytest
```

### 前端测试
```bash
cd frontend
npm run test
```

## 部署

### Docker Compose 部署
```bash
docker-compose -f docker-compose.yml up -d
```

### Kubernetes 部署
详见 `deploy/kubernetes/` 目录 (待实现)

## 故障排查

### 数据库连接失败
1. 检查 PostgreSQL 容器是否正常运行：`docker-compose ps`
2. 检查数据库凭证是否正确
3. 查看后端日志：`docker-compose logs backend`

### 前后端通信失败
1. 检查 CORS 配置是否正确
2. 验证 API 端点是否正确
3. 检查浏览器控制台的错误信息

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系项目维护者。

---

**最后更新：** 2025-11-11
**版本：** 0.1.0
