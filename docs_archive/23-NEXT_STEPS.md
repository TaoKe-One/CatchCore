# CatchCore 下一步开发计划

**阶段:** 第二阶段第 2-3 天
**当前状态:** 已完成 60%，继续推进到 95%+
**目标:** 完整的扫描流程实现

---

## 🎯 优先级排序

### 第1优先级 (今天完成) - 任务队列和异步执行

#### 1.1 Celery + Redis 配置
```
目标: 完成 (4小时)
文件: backend/app/celery_app.py

关键任务:
- 配置 Celery 和 Redis 连接
- 定义异步任务装饰器
- 配置任务路由和优先级
- 实现任务状态跟踪
```

#### 1.2 扫描任务异步执行
```
目标: 完成 (6小时)
文件: backend/app/services/scan_service.py

关键功能:
- 端口扫描异步任务
- 服务识别异步任务
- 指纹识别异步任务
- 任务状态同步到数据库
- 错误处理和重试机制
```

#### 1.3 WebSocket 实时推送
```
目标: 完成 (5小时)
文件: backend/app/api/v1_websocket.py

关键功能:
- 建立 WebSocket 连接
- 实时推送扫描进度
- 实时推送扫描结果
- 连接生命周期管理
```

---

### 第2优先级 (明天完成) - 扫描引擎集成

#### 2.1 端口扫描集成
```
目标: 完成 (6小时)
文件: backend/app/services/port_scan_service.py

支持工具:
- nmap (推荐)
- fscan (备选)

功能:
- 工具包装和调用
- 结果解析 (XML/JSON)
- 错误处理
- 超时管理
- 速率限制
```

#### 2.2 服务识别
```
目标: 完成 (4小时)
文件: backend/app/services/service_identify_service.py

功能:
- 获取服务版本信息
- 关联指纹库
- 记录到数据库
- 风险评估
```

#### 2.3 指纹识别优化
```
目标: 完成 (3小时)
文件: backend/app/services/fingerprint_service.py

功能:
- 批量指纹库加载
- 高效匹配算法
- 缓存优化
- 性能基准测试
```

---

### 第3优先级 (后天完成) - 前端交互优化

#### 3.1 实时进度显示
```
目标: 完成 (4小时)
文件: frontend/src/pages/tasks/TaskDetail.tsx

功能:
- WebSocket 连接管理
- 实时进度条更新
- 结果流式显示
- 错误提示
```

#### 3.2 POC 管理页面
```
目标: 完成 (4小时)
文件: frontend/src/pages/pocs/POCList.tsx

功能:
- POC 列表和搜索
- POC 上传功能
- POC 执行界面
- 结果展示
```

#### 3.3 扫描结果展示
```
目标: 完成 (3小时)
文件: frontend/src/pages/results/ScanResults.tsx

功能:
- 发现的资产列表
- 服务详情卡片
- 漏洞关联显示
- 数据导出功能
```

---

## 📋 详细开发流程

### 步骤 1: Celery 配置 (1小时)

**创建文件:** `backend/app/celery_app.py`

```python
# celery 配置
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "catchcore",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
)
```

**更新:** `backend/requirements.txt`
```
celery==5.3.4
flower==2.0.1  # Celery 监控
```

---

### 步骤 2: 扫描服务实现 (3小时)

**创建文件:** `backend/app/services/scan_service.py`

```python
# 异步扫描任务
from celery import shared_task
from app.celery_app import celery_app

@celery_app.task(bind=True)
def port_scan_task(self, task_id: int, target: str):
    """异步端口扫描任务"""
    try:
        # 1. 更新任务状态为运行中
        # 2. 执行 nmap 扫描
        # 3. 解析结果
        # 4. 保存到数据库
        # 5. 更新任务状态为完成
    except Exception as e:
        # 错误处理
        pass

@celery_app.task(bind=True)
def service_identify_task(self, task_id: int, asset_id: int, port: int):
    """异步服务识别任务"""
    # 识别服务类型和版本
    pass

@celery_app.task(bind=True)
def fingerprint_task(self, task_id: int, asset_id: int):
    """异步指纹识别任务"""
    # 进行指纹匹配
    pass
```

---

### 步骤 3: WebSocket 实现 (2小时)

**创建文件:** `backend/app/api/v1_websocket.py`

```python
# WebSocket 端点
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/api/v1/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: int):
    """WebSocket 端点用于实时推送扫描进度"""
    await websocket.accept()

    try:
        while True:
            # 1. 从 Redis 获取任务进度
            # 2. 从数据库获取新结果
            # 3. 推送到前端
            await websocket.send_json({
                "type": "progress",
                "progress": progress,
                "message": message,
            })
    except WebSocketDisconnect:
        pass
```

---

### 步骤 4: 端口扫描集成 (3小时)

**创建文件:** `backend/app/services/port_scan_service.py`

```python
# 端口扫描实现
import subprocess
import xml.etree.ElementTree as ET

class PortScanService:
    @staticmethod
    async def scan_with_nmap(target: str, options: dict = None):
        """使用 nmap 扫描端口"""
        cmd = [
            "nmap",
            "-oX", "-",  # XML 输出
            "-Pn",  # 跳过 ping
            "-p", options.get("ports", "1-65535"),
            "-T", options.get("timing", "4"),
            target
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # 解析 XML 结果
        root = ET.fromstring(result.stdout)
        ports = []

        for host in root.findall("host"):
            for port in host.findall("ports/port"):
                ports.append({
                    "port": int(port.get("portid")),
                    "protocol": port.get("protocol"),
                    "state": port.find("state").get("state"),
                    "service": port.find("service").get("name") if port.find("service") else None,
                })

        return ports
```

---

### 步骤 5: 前端 WebSocket 连接 (2小时)

**创建文件:** `frontend/src/hooks/useTaskProgress.ts`

```typescript
// WebSocket 进度钩子
import { useEffect, useState } from 'react'

export const useTaskProgress = (taskId: number) => {
  const [progress, setProgress] = useState(0)
  const [logs, setLogs] = useState<string[]>([])
  const [results, setResults] = useState<any[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    const websocket = new WebSocket(
      `ws://localhost:8000/api/v1/ws/task/${taskId}`
    )

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'progress') {
        setProgress(data.progress)
      } else if (data.type === 'log') {
        setLogs(prev => [...prev, data.message])
      } else if (data.type === 'result') {
        setResults(prev => [...prev, data.result])
      }
    }

    setWs(websocket)

    return () => websocket.close()
  }, [taskId])

  return { progress, logs, results, ws }
}
```

---

## 🔄 工作流程图

```
用户创建任务
    ↓
前端发送请求 (POST /api/v1/tasks/start)
    ↓
后端接收并创建 Celery 任务
    ↓
Celery Worker 异步执行扫描
    ├─ 1. 端口扫描 (nmap)
    ├─ 2. 服务识别
    ├─ 3. 指纹匹配
    ├─ 4. 漏洞检查
    └─ 5. 结果保存到数据库
    ↓
推送进度到 Redis
    ↓
WebSocket 实时推送到前端
    ↓
前端显示进度和结果
    ↓
任务完成，用户查看报告
```

---

## 📊 预期结果

完成这些步骤后，系统将支持：

### 后端功能
- ✅ 异步扫描任务执行
- ✅ 扫描进度实时追踪
- ✅ 多项扫描并行执行
- ✅ 错误自动重试
- ✅ 结果自动入库

### 前端功能
- ✅ 实时进度条显示
- ✅ 实时日志输出
- ✅ 结果流式显示
- ✅ 扫描中止功能
- ✅ 结果导出

### 用户体验
- ✅ 一键启动完整扫描
- ✅ 实时查看扫描进度
- ✅ 自动发现资产和漏洞
- ✅ 完整的扫描历史记录

---

## ⚠️ 重要注意事项

### 1. nmap 安装
```bash
# macOS
brew install nmap

# Ubuntu/Debian
apt-get install nmap

# CentOS
yum install nmap
```

### 2. Redis 要求
- Redis 必须运行在 Docker 容器中
- 确保消息队列可用

### 3. 并发限制
- 默认最多 5 个并发扫描任务
- 可通过配置调整

### 4. 超时设置
- 单个扫描任务最多 30 分钟
- nmap 扫描最多 15 分钟

---

## 📝 文件清单

### 需要创建的文件
```
backend/
├── app/
│   ├── celery_app.py                      (Celery 配置)
│   ├── services/
│   │   ├── scan_service.py                (扫描服务)
│   │   ├── port_scan_service.py           (端口扫描)
│   │   ├── service_identify_service.py    (服务识别)
│   │   └── fingerprint_service.py         (指纹识别)
│   └── api/
│       └── v1_websocket.py                (WebSocket)
│
frontend/
├── src/
│   ├── hooks/
│   │   └── useTaskProgress.ts             (进度钩子)
│   ├── pages/
│   │   ├── tasks/TaskDetail.tsx           (任务详情)
│   │   ├── results/ScanResults.tsx        (扫描结果)
│   │   └── pocs/POCList.tsx               (POC 管理)
│   └── services/
│       └── websocket.ts                   (WebSocket 客户端)
```

### 需要修改的文件
```
backend/requirements.txt                    (添加 celery, flower)
backend/docker-compose.yml                  (Redis 配置)
backend/app/main.py                         (注册 WebSocket)
frontend/package.json                       (如需额外依赖)
```

---

## 🚀 预计时间表

| 任务 | 预计时间 | 优先级 |
|------|--------|--------|
| Celery 配置 | 1小时 | 🔴 必须 |
| 扫描服务 | 3小时 | 🔴 必须 |
| WebSocket | 2小时 | 🟡 重要 |
| 端口扫描 | 3小时 | 🔴 必须 |
| 服务识别 | 2小时 | 🟡 重要 |
| 前端集成 | 3小时 | 🟡 重要 |
| 测试和优化 | 2小时 | 🟢 可选 |
| **总计** | **16小时** | |

---

## ✅ 完成检查清单

在完成每个部分时：

- [ ] Celery 配置完成
  - [ ] Redis 连接成功
  - [ ] 任务可以入队
  - [ ] Worker 可以执行

- [ ] 扫描服务完成
  - [ ] nmap 集成成功
  - [ ] 结果解析正确
  - [ ] 数据库存储成功

- [ ] WebSocket 完成
  - [ ] 连接建立
  - [ ] 消息推送
  - [ ] 前端接收

- [ ] 前端集成完成
  - [ ] 进度条显示
  - [ ] 日志输出
  - [ ] 结果展示

---

## 🎯 成功标准

系统完成以下标准即为成功：

1. **能够创建和执行扫描任务**
   - 任务状态正确转移
   - 无报错和异常

2. **实时进度推送**
   - 前端实时显示进度
   - 延迟 < 1 秒

3. **扫描结果准确**
   - 发现的端口完整
   - 服务识别正确
   - 漏洞匹配准确

4. **用户体验流畅**
   - 界面响应快速
   - 信息清晰易读
   - 操作直观易用

---

## 💡 优化建议

完成基础功能后可考虑的优化：

1. **性能优化**
   - 批量处理扫描结果
   - 查询结果缓存
   - 前端虚拟滚动

2. **功能扩展**
   - 暂停和恢复扫描
   - 扫描任务队列管理
   - 扫描结果对比

3. **可靠性改进**
   - 任务失败重试
   - 断线自动重连
   - 数据备份

---

**下一步:** 立即开始实现 Celery + Redis 配置!

**时间:** 预计 16 小时完成所有功能
**目标:** 达到系统 95% 完成度
