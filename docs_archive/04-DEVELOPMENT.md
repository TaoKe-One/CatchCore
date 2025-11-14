# CatchCore 开发指南

## 项目结构详解

### 后端目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用工厂
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py               # 依赖注入（认证、数据库等）
│   │   ├── v1_auth.py            # 认证相关路由
│   │   ├── v1_assets.py          # 资产管理路由（待开发）
│   │   ├── v1_tasks.py           # 任务管理路由（待开发）
│   │   ├── v1_vulnerabilities.py # 漏洞管理路由（待开发）
│   │   └── v1_pocs.py            # POC 管理路由（待开发）
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # 应用配置
│   │   ├── database.py           # 数据库配置
│   │   └── security.py           # 安全相关功能
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py               # 用户、角色、权限模型
│   │   ├── asset.py              # 资产、服务模型
│   │   ├── task.py               # 任务模型
│   │   ├── vulnerability.py      # 漏洞模型
│   │   ├── poc.py                # POC 模型
│   │   ├── fingerprint.py        # 指纹模型
│   │   ├── credential.py         # 凭证模型
│   │   ├── project.py            # 项目模型
│   │   └── node.py               # 节点模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py               # 用户相关 schema
│   │   ├── asset.py              # 资产相关 schema
│   │   ├── task.py               # 任务相关 schema
│   │   └── vulnerability.py      # 漏洞相关 schema
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asset_service.py      # 资产服务（待开发）
│   │   ├── task_service.py       # 任务服务（待开发）
│   │   ├── scan_service.py       # 扫描服务（待开发）
│   │   └── report_service.py     # 报告服务（待开发）
│   └── utils/
│       ├── __init__.py
│       ├── validators.py         # 验证工具
│       ├── parsers.py            # 解析工具
│       └── helpers.py            # 辅助函数
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置
│   ├── test_auth.py             # 认证测试
│   ├── test_assets.py           # 资产测试（待开发）
│   └── test_tasks.py            # 任务测试（待开发）
├── main.py                       # 应用入口
├── requirements.txt              # Python 依赖
├── Dockerfile                    # Docker 配置
├── .env                          # 本地环境变量
├── .env.example                  # 环境变量示例
└── alembic/                      # 数据库迁移（待配置）
```

### 前端目录结构

```
frontend/
├── src/
│   ├── main.tsx                  # 应用入口
│   ├── App.tsx                   # 主应用组件
│   ├── components/               # 可复用组件
│   │   ├── Layout/              # 布局组件
│   │   ├── AssetTable/          # 资产表格（待开发）
│   │   ├── TaskList/            # 任务列表（待开发）
│   │   └── ...
│   ├── pages/
│   │   ├── auth/
│   │   │   └── LoginPage.tsx     # 登录页
│   │   ├── dashboard/
│   │   │   └── Dashboard.tsx     # 仪表盘
│   │   ├── assets/
│   │   │   ├── AssetList.tsx     # 资产列表
│   │   │   └── AssetDetail.tsx   # 资产详情（待开发）
│   │   ├── tasks/
│   │   │   ├── TaskList.tsx      # 任务列表
│   │   │   ├── TaskDetail.tsx    # 任务详情（待开发）
│   │   │   └── TaskCreate.tsx    # 任务创建（待开发）
│   │   └── vulnerabilities/
│   │       ├── VulnerabilityList.tsx    # 漏洞列表
│   │       └── VulnerabilityDetail.tsx  # 漏洞详情（待开发）
│   ├── services/
│   │   └── api.ts                # API 客户端
│   ├── store/
│   │   ├── index.ts              # Redux store 配置
│   │   └── slices/
│   │       ├── authSlice.ts      # 认证 slice
│   │       ├── assetSlice.ts     # 资产 slice
│   │       └── taskSlice.ts      # 任务 slice
│   ├── types/
│   │   └── index.ts              # TypeScript 类型定义
│   ├── styles/
│   │   ├── index.less            # 全局样式
│   │   └── App.less              # App 样式
│   └── utils/
│       ├── request.ts            # 请求工具（待开发）
│       └── format.ts             # 格式化工具（待开发）
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── Dockerfile
└── .gitignore
```

## 开发工作流

### 1. 添加新的 API 路由

**步骤：**

1. 在 `app/models/` 中定义数据库模型（如果需要）
2. 在 `app/schemas/` 中定义请求/响应 schema
3. 在 `app/services/` 中实现业务逻辑
4. 在 `app/api/` 中创建路由文件

**示例：添加资产管理路由**

```python
# backend/app/api/v1_assets.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import Asset
from app.schemas.asset import AssetCreate, AssetResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/assets", tags=["assets"])

@router.post("", response_model=AssetResponse)
async def create_asset(
    asset_in: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """创建新资产"""
    db_asset = Asset(**asset_in.dict())
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return db_asset

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取资产详情"""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset
```

4. 在 `app/main.py` 中注册路由：

```python
from app.api.v1_assets import router as assets_router

app.include_router(assets_router, prefix=settings.API_V1_PREFIX)
```

### 2. 添加新的前端页面

**步骤：**

1. 在 `src/pages/` 中创建新的页面组件
2. 在 `src/services/api.ts` 中添加 API 方法
3. 如果需要状态管理，在 `src/store/slices/` 中创建 slice
4. 在 `src/App.tsx` 中注册路由

**示例：添加资产详情页**

```typescript
// src/pages/assets/AssetDetail.tsx
import React, { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Tabs, Table } from 'antd'
import apiService from '../../services/api'

const AssetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [asset, setAsset] = React.useState(null)
  const [loading, setLoading] = React.useState(false)

  useEffect(() => {
    if (id) {
      fetchAsset(parseInt(id))
    }
  }, [id])

  const fetchAsset = async (assetId: number) => {
    setLoading(true)
    try {
      const response = await apiService.getAsset(assetId)
      setAsset(response.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card loading={loading} title={`资产: ${asset?.ip}`}>
      <Tabs>
        <Tabs.TabPane tab="基本信息" key="1">
          {/* 基本信息内容 */}
        </Tabs.TabPane>
        <Tabs.TabPane tab="服务" key="2">
          {/* 服务列表 */}
        </Tabs.TabPane>
        <Tabs.TabPane tab="漏洞" key="3">
          {/* 漏洞列表 */}
        </Tabs.TabPane>
      </Tabs>
    </Card>
  )
}

export default AssetDetail
```

## 编码规范

### 后端

- 使用 `black` 进行代码格式化：`black .`
- 使用 `flake8` 进行代码检查：`flake8 app`
- 使用 `mypy` 进行类型检查：`mypy app`
- 遵循 PEP 8 编码规范
- 为所有函数添加文档字符串

### 前端

- 使用 ESLint 检查代码：`npm run lint`
- 使用 TypeScript 进行类型检查
- 使用 Prettier 进行代码格式化（如需要）
- 组件命名使用 PascalCase
- 文件命名使用 PascalCase（组件）或 camelCase（工具/服务）

## 测试

### 后端测试

```bash
cd backend
pytest              # 运行所有测试
pytest -v           # 详细输出
pytest tests/test_auth.py  # 运行特定测试文件
pytest --cov        # 生成覆盖率报告
```

### 前端测试

```bash
cd frontend
npm test            # 运行测试
npm run test:ui     # UI 模式测试
```

## 调试

### 后端调试

1. 在 `main.py` 中设置 `DEBUG=True`
2. 访问 FastAPI 自动生成的文档：
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### 前端调试

1. 使用浏览器开发者工具（F12）
2. 使用 Redux DevTools 浏览器扩展
3. 在 Vite 中，修改代码会自动热更新

## 常见问题

### Q: 如何添加新的数据库模型？

A:
1. 在 `app/models/` 中创建模型类
2. 在模型的 `__init__.py` 中导出
3. 在 `app/core/database.py` 中的 `init_db()` 会自动创建表

### Q: 如何运行数据库迁移？

A: 目前使用自动创建表，如需版本控制，可配置 Alembic。

### Q: 如何处理错误响应？

A: 统一使用 HTTP 异常：
```python
from fastapi import HTTPException

raise HTTPException(
    status_code=400,
    detail="Error message"
)
```

## 性能优化

### 后端
- 使用数据库索引
- 实现分页查询
- 使用 Redis 缓存
- 异步数据库操作

### 前端
- 代码分割
- 路由级代码分割
- 图片优化
- Redux 状态选择器优化

## 部署前检查清单

- [ ] 所有测试通过
- [ ] 代码没有 linting 错误
- [ ] 环境变量正确配置
- [ ] 数据库已初始化
- [ ] Docker 镜像能正常构建

---

**更新时间：** 2025-11-11
