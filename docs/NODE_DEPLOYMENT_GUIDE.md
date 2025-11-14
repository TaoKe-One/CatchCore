# CatchCore 节点部署指南

## 📚 目录
1. [架构概述](#架构概述)
2. [节点系统要求](#节点系统要求)
3. [节点类型说明](#节点类型说明)
4. [核心节点部署](#核心节点部署)
5. [扫描节点部署](#扫描节点部署)
6. [节点注册和管理](#节点注册和管理)
7. [节点健康检查](#节点健康检查)
8. [任务分配](#任务分配)
9. [监控和维护](#监控和维护)
10. [故障排查](#故障排查)

---

## 架构概述

CatchCore 采用分布式架构，支持多节点部署。整个系统由以下组件组成：

```
┌─────────────────────────────────────────────────────┐
│           Master 服务器 (核心节点)                    │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │  FastAPI     │  PostgreSQL  │    Redis     │    │
│  │  后端服务    │   数据库     │   缓存队列    │    │
│  └──────────────┴──────────────┴──────────────┘    │
│  ┌──────────────────────────────────┐              │
│  │  任务调度器 & 节点管理器          │              │
│  └──────────────────────────────────┘              │
└─────────────────────────────────────────────────────┘
           │           │           │
           ▼           ▼           ▼
    ┌───────────┐ ┌───────────┐ ┌───────────┐
    │  扫描节点   │ │  扫描节点   │ │  扫描节点   │
    │   Node 1   │ │   Node 2   │ │   Node 3   │
    └───────────┘ └───────────┘ └───────────┘
```

### 核心组件
- **Master 服务器**: 中央控制器，管理所有节点和任务
- **扫描节点**: 执行实际扫描任务的工作节点
- **数据库**: PostgreSQL 存储所有数据
- **缓存/队列**: Redis 进行任务队列和实时通信
- **任务调度**: 负责将任务分配给合适的节点

---

## 节点系统要求

### Master 节点（核心服务器）
```
操作系统:     Linux (Ubuntu 20.04+) / macOS / Windows (WSL2)
Python:       3.10 或更高版本
CPU:          4 核或以上
内存:         8GB 或以上（生产环境 16GB+）
磁盘:         50GB 可用空间
网络:         稳定的互联网连接
数据库:       PostgreSQL 13+
缓存:         Redis 6.0+
```

### 扫描节点
```
操作系统:     Linux / macOS / Windows (WSL2)
Python:       3.10 或更高版本
CPU:          2 核或以上
内存:         4GB 或以上
磁盘:         20GB 可用空间
网络:         与 Master 节点的稳定连接
扫描工具:     FScan, Nuclei, Afrog, DDDD, DirSearch（自动安装）
```

### 网络要求
```
Master 节点暴露端口:
  - 8000 (FastAPI 应用)
  - 5432 (PostgreSQL)
  - 6379 (Redis)
  - 8086 (InfluxDB)

扫描节点需要访问:
  - Master:8000 (API 通信)
  - Master:6379 (Redis 队列)
  - 互联网 (下载工具和目标扫描)
```

---

## 节点类型说明

CatchCore 支持多种节点类型：

### 1. Scanner 节点（默认）
- **功能**: 执行扫描任务（端口扫描、服务识别、指纹识别等）
- **资源消耗**: 中等
- **并发任务**: 5-10 个
- **用途**: 分布式扫描执行

### 2. Worker 节点
- **功能**: 执行通用计算任务（POC 检测、密码破解等）
- **资源消耗**: 高
- **并发任务**: 2-5 个
- **用途**: 计算密集型任务

### 3. Coordinator 节点
- **功能**: 辅助协调任务分配（未来扩展）
- **资源消耗**: 低
- **并发任务**: 无限制
- **用途**: 分布式协调

---

## 核心节点部署

### 步骤 1: 准备 Master 服务器

#### 1.1 系统更新（Ubuntu/Debian）
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget \
  postgresql postgresql-contrib redis-server docker.io docker-compose
```

#### 1.2 启动基础服务
```bash
# 启动 PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 启动 Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 或使用 Docker Compose
cd /path/to/CatchCore
docker-compose up -d postgres redis influxdb
```

### 步骤 2: 克隆项目并配置

```bash
# 克隆仓库
git clone https://github.com/TaoKe-One/CatchCore.git
cd CatchCore

# 创建环境文件
cp backend/.env.example backend/.env

# 编辑环境文件
nano backend/.env
```

### 步骤 3: 配置 Master .env 文件
```env
# 应用配置
APP_NAME=CatchCore
APP_VERSION=0.1.0
DEBUG=False
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql://catchcore:catchcore@localhost:5432/catchcore_db

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# JWT 安全密钥（生成新的！）
SECRET_KEY=your-very-secret-key-change-this-in-production-use-something-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS 配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# API 配置
API_V1_PREFIX=/api/v1

# 节点配置
NODE_HEARTBEAT_INTERVAL=30
NODE_HEARTBEAT_TIMEOUT=120
MAX_NODE_OFFLINE_TIME=300

# InfluxDB 配置（可选）
INFLUXDB_URL=http://localhost:8086
INFLUXDB_ORG=catchcore
INFLUXDB_BUCKET=scandata
INFLUXDB_TOKEN=your-token-here
```

### 步骤 4: 初始化数据库

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python3 -m alembic upgrade head

# 创建初始用户
python3 -c "from app.models.user import User; print('Database initialized')"
```

### 步骤 5: 启动 Master 服务器

```bash
# 方式 1: 直接运行（开发）
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 方式 2: 使用 Gunicorn（生产）
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app

# 方式 3: 使用 Docker
docker-compose up -d backend
```

### 步骤 6: 验证 Master 部署

```bash
# 检查应用健康状态
curl http://localhost:8000/health

# 预期响应
# {"status":"ok","version":"0.1.0"}

# 检查数据库连接
curl http://localhost:8000/api/v1/assets

# 如果返回 401，说明需要认证（正常）
```

---

## 扫描节点部署

### 步骤 1: 准备扫描节点

#### 1.1 系统依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl wget

# macOS
brew install python3 git

# 安装扫描工具（可选，系统会自动下载）
sudo apt install -y nmap hydra hashcat
```

#### 1.2 克隆项目
```bash
git clone https://github.com/TaoKe-One/CatchCore.git
cd CatchCore
```

### 步骤 2: 创建节点配置

在每个扫描节点创建 `node_config.yml`：

```yaml
# node_config.yml
node:
  name: "scanner-node-01"          # 唯一节点名称
  type: "scanner"                   # 节点类型: scanner, worker
  host: "192.168.1.100"            # 本地 IP 地址
  port: 8001                        # 本地端口

master:
  host: "192.168.1.50"             # Master 服务器 IP
  port: 8000                        # Master API 端口
  api_url: "http://192.168.1.50:8000/api/v1"

redis:
  host: "192.168.1.50"             # Redis 服务器地址
  port: 6379
  db: 0
  password: null                    # 如果 Redis 设置了密码

performance:
  max_concurrent_tasks: 5          # 最大并发任务数
  worker_threads: 4                # 工作线程数
  heartbeat_interval: 30           # 心跳间隔（秒）
  check_task_interval: 5           # 检查任务间隔（秒）

tools:
  fscan_enabled: true
  nuclei_enabled: true
  afrog_enabled: true
  dddd_enabled: true
  dirsearch_enabled: true
  auto_install: true               # 自动安装缺失的工具
```

### 步骤 3: 部署节点服务

#### 方式 1: 直接运行（开发）

```bash
# 进入项目目录
cd CatchCore/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行节点代理（需要创建 node_agent.py）
python3 node_agent.py --config ../node_config.yml
```

#### 方式 2: 使用 Systemd 服务（推荐）

创建 `/etc/systemd/system/catchcore-node.service`：

```ini
[Unit]
Description=CatchCore Scanning Node
After=network.target

[Service]
Type=simple
User=catchcore
WorkingDirectory=/opt/catchcore
Environment="PATH=/opt/catchcore/backend/venv/bin"
ExecStart=/opt/catchcore/backend/venv/bin/python3 node_agent.py --config /opt/catchcore/node_config.yml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable catchcore-node
sudo systemctl start catchcore-node

# 查看日志
sudo journalctl -u catchcore-node -f
```

#### 方式 3: 使用 Docker

创建 `Dockerfile.node`：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    curl \
    wget \
    nmap \
    && rm -rf /var/lib/apt/lists/*

# 复制项目
COPY backend/ /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制节点配置
COPY node_config.yml /app/node_config.yml

# 运行节点代理
CMD ["python3", "node_agent.py", "--config", "/app/node_config.yml"]
```

运行容器：
```bash
docker build -f Dockerfile.node -t catchcore-node:latest .

docker run -d \
  --name catchcore-node-01 \
  --network host \
  -v /opt/catchcore/node_config.yml:/app/node_config.yml \
  -e MASTER_URL=http://192.168.1.50:8000/api/v1 \
  -e NODE_NAME=scanner-node-01 \
  catchcore-node:latest
```

#### 方式 4: 使用 Docker Compose

在 `docker-compose.yml` 中添加节点服务：

```yaml
  # 扫描节点 1
  scanner-node-1:
    build:
      context: ./backend
      dockerfile: Dockerfile.node
    container_name: catchcore-scanner-1
    environment:
      - MASTER_HOST=backend
      - MASTER_PORT=8000
      - NODE_NAME=scanner-node-01
      - NODE_TYPE=scanner
      - MAX_CONCURRENT_TASKS=5
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - backend
      - redis
    volumes:
      - ./data/node-1:/app/data
    networks:
      - catchcore-network

  # 扫描节点 2
  scanner-node-2:
    build:
      context: ./backend
      dockerfile: Dockerfile.node
    container_name: catchcore-scanner-2
    environment:
      - MASTER_HOST=backend
      - MASTER_PORT=8000
      - NODE_NAME=scanner-node-02
      - NODE_TYPE=scanner
      - MAX_CONCURRENT_TASKS=5
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - backend
      - redis
    volumes:
      - ./data/node-2:/app/data
    networks:
      - catchcore-network
```

启动节点：
```bash
docker-compose up -d scanner-node-1 scanner-node-2
```

---

## 节点注册和管理

### 自动节点注册

节点启动时会自动向 Master 注册：

```
节点启动流程：
1. 读取本地配置文件
2. 连接到 Master 的 Redis
3. 向 Master API 发送注册请求
4. 获取节点 ID 和认证令牌
5. 启动心跳线程
6. 开始监听任务队列
```

### 手动节点注册 API

如果需要手动注册节点：

```bash
curl -X POST http://localhost:8000/api/v1/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "scanner-node-01",
    "host": "192.168.1.100",
    "port": 8001,
    "node_type": "scanner",
    "max_concurrent_tasks": 5,
    "api_version": "0.1.0"
  }'
```

响应：
```json
{
  "id": 1,
  "name": "scanner-node-01",
  "host": "192.168.1.100",
  "port": 8001,
  "status": "online",
  "node_type": "scanner",
  "created_at": "2025-11-14T10:30:00Z"
}
```

### 查看所有节点

```bash
curl -X GET http://localhost:8000/api/v1/nodes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 更新节点配置

```bash
curl -X PUT http://localhost:8000/api/v1/nodes/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "max_concurrent_tasks": 8,
    "status": "maintenance"
  }'
```

### 删除节点

```bash
curl -X DELETE http://localhost:8000/api/v1/nodes/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 节点健康检查

### 心跳机制

每个扫描节点定期向 Master 发送心跳：

```
心跳包内容：
{
  "node_id": 1,
  "timestamp": "2025-11-14T10:30:00Z",
  "status": "online",
  "cpu_usage": 45.5,
  "memory_usage": 62.3,
  "disk_usage": 38.9,
  "current_tasks": 3,
  "api_version": "0.1.0"
}
```

### 健康检查 API

```bash
# 检查单个节点状态
curl -X GET http://localhost:8000/api/v1/nodes/1/health \
  -H "Authorization: Bearer YOUR_TOKEN"

# 响应
{
  "id": 1,
  "name": "scanner-node-01",
  "status": "online",
  "last_heartbeat": "2025-11-14T10:30:00Z",
  "cpu_usage": 45.5,
  "memory_usage": 62.3,
  "disk_usage": 38.9,
  "current_tasks": 3,
  "is_healthy": true
}
```

### 离线检测

- 节点离线超时: 120 秒
- 自动将离线节点标记为 "offline"
- 离线节点上的任务会重新分配

---

## 任务分配

### 任务分配流程

```
任务创建 → 入队 → 调度器检查 → 选择合适节点 → 发送到节点 → 执行 → 回报结果
```

### 节点选择策略

调度器使用以下策略选择最优节点：

1. **健康性检查**: 只选择在线且健康的节点
2. **容量检查**: 节点当前任务数 < 最大并发任务数
3. **负载均衡**: 优先选择任务数最少的节点
4. **亲和性**: 优先选择同一地域/网络的节点（如果配置）
5. **优先级**: 根据任务优先级选择适合的节点类型

### 示例: 创建扫描任务

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Port Scan - 192.168.1.0/24",
    "task_type": "port_scan",
    "target_range": "192.168.1.0/24",
    "priority": 8,
    "description": "Scan local network for open ports"
  }'
```

任务会自动分配给可用的 Scanner 节点。

---

## 监控和维护

### 监控仪表板

使用 Web UI 查看：
- 所有节点的实时状态
- 每个节点的资源使用情况
- 运行中的任务分布
- 历史统计信息

访问: `http://localhost:3000/nodes`

### 性能指标

通过 InfluxDB + Grafana 监控：

```bash
# 节点 CPU 使用率
SELECT mean("cpu_usage") FROM "node_metrics"
WHERE time > now() - 1h
GROUP BY time(5m), "node_name"

# 节点内存使用率
SELECT mean("memory_usage") FROM "node_metrics"
WHERE time > now() - 1h
GROUP BY time(5m), "node_name"

# 任务完成率
SELECT mean("completed_tasks") FROM "node_metrics"
WHERE time > now() - 1d
GROUP BY time(1h), "node_name"
```

### 日志收集

节点日志位置：
- **直接运行**: `./logs/node_agent.log`
- **Systemd**: `journalctl -u catchcore-node`
- **Docker**: `docker logs catchcore-node-01`

### 定期维护任务

```bash
# 每周检查节点状态
curl -X GET http://localhost:8000/api/v1/nodes \
  -H "Authorization: Bearer YOUR_TOKEN" | jq '.[] | select(.status != "online")'

# 清理旧日志（30 天以前）
find ./logs -name "*.log" -mtime +30 -delete

# 检查磁盘空间
df -h

# 检查数据库大小
psql -U catchcore -d catchcore_db -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS size FROM pg_database;"
```

---

## 故障排查

### 问题 1: 节点无法连接到 Master

**症状**: 节点启动后显示"无法连接到 Master"

**排查步骤**:
```bash
# 1. 检查网络连接
ping master_ip

# 2. 检查 Master 端口是否开放
telnet master_ip 8000

# 3. 检查防火墙规则
sudo ufw status
sudo ufw allow 8000/tcp

# 4. 检查 Master 是否运行
curl http://master_ip:8000/health

# 5. 查看节点日志
tail -f logs/node_agent.log
```

### 问题 2: 节点任务分配失败

**症状**: 任务一直处于 PENDING 状态

**排查步骤**:
```bash
# 1. 检查节点是否在线
curl -X GET http://localhost:8000/api/v1/nodes \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 检查节点容量
# 确保 current_tasks < max_concurrent_tasks

# 3. 检查任务配置
curl -X GET http://localhost:8000/api/v1/tasks/1 \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. 重启节点
systemctl restart catchcore-node
```

### 问题 3: 节点内存持续增长

**症状**: 节点内存使用率逐步上升

**解决方案**:
```bash
# 1. 增加 Python 垃圾回收频率
export PYTHONGC_THRESHOLD=700,5,5

# 2. 限制内存使用（通过 cgroup）
sudo cgcreate -g memory:/catchcore-node
sudo cgset -r memory.limit_in_bytes=4G /catchcore-node

# 3. 定期重启节点
# 在 systemd 中添加:
ExecStartPost=/bin/bash -c 'systemctl restart --time=86400 %n'

# 4. 查看内存使用详情
ps aux | grep node_agent
ps -eo pid,user,vsize,rss | grep python
```

### 问题 4: 任务执行超时

**症状**: 任务经常超时且无法完成

**解决方案**:
```bash
# 1. 增加任务超时时间
# 在 .env 中添加:
TASK_TIMEOUT_SECONDS=3600

# 2. 提高节点资源分配
# 增加 max_concurrent_tasks 的值（2-3）

# 3. 检查目标网络连接
ping target_ip
traceroute target_ip

# 4. 查看任务日志
curl -X GET http://localhost:8000/api/v1/tasks/1/logs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 问题 5: Redis 连接错误

**症状**: "redis.exceptions.ConnectionError"

**解决方案**:
```bash
# 1. 检查 Redis 状态
redis-cli ping

# 2. 检查 Redis 配置
redis-cli CONFIG GET maxmemory
redis-cli CONFIG GET maxmemory-policy

# 3. 增加 Redis 内存限制
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 4. 重启 Redis
sudo systemctl restart redis-server

# 5. 检查连接字符串
# 确保 REDIS_URL 格式正确: redis://[password@]host:port/db
```

### 问题 6: 数据库连接池耗尽

**症状**: "psycopg2.pool.PoolError: connection pool is exhausted"

**解决方案**:
```bash
# 1. 增加连接池大小（backend/.env）
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# 2. 检查活跃连接
psql -U catchcore -d catchcore_db -c "SELECT count(*) FROM pg_stat_activity;"

# 3. 杀死长时间连接
psql -U catchcore -d catchcore_db -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE now() - query_start > interval '1 hour';"

# 4. 重启后端服务
docker restart catchcore-backend
```

---

## 扩展和优化

### 水平扩展

添加更多扫描节点：

1. 为每个节点创建唯一的 `node_config.yml`
2. 使用不同的 `name` 字段
3. 部署节点（按照上述方式）
4. 节点自动注册并加入集群

### 性能优化建议

```yaml
优化配置:
  worker_threads: 8              # 增加线程数（CPU 核心数 × 2）
  max_concurrent_tasks: 10       # 根据资源调整
  heartbeat_interval: 60         # 减少心跳频率节省网络
  check_task_interval: 1         # 增加检查频率但要注意 CPU
  connection_pool_size: 50       # 增加连接池
```

### 资源隔离

使用 cgroup/容器限制资源：

```bash
# CPU 限制 (Docker)
docker run --cpus="2" catchcore-node

# 内存限制 (Docker)
docker run --memory="4g" catchcore-node

# 组合
docker run \
  --cpus="2" \
  --memory="4g" \
  --memory-swap="5g" \
  catchcore-node
```

---

## 最佳实践

✅ **推荐做法**
- 为每个节点配置不同的 hostname
- 定期备份 PostgreSQL 数据库
- 使用 HTTPS 在生产环境
- 监控节点资源使用情况
- 定期清理旧日志和数据
- 在不同网络区域部署节点
- 使用负载均衡器（可选）

❌ **应避免**
- 在同一服务器上运行多个 Master 实例
- 直接暴露 Redis 到互联网
- 使用默认数据库密码
- 禁用日志记录
- 过度超配节点任务
- 忽视安全更新

---

## 常用命令速查表

```bash
# 节点管理
curl -X POST http://master:8000/api/v1/nodes/register      # 注册节点
curl -X GET http://master:8000/api/v1/nodes                # 列出节点
curl -X GET http://master:8000/api/v1/nodes/1/health       # 检查健康状态
curl -X PUT http://master:8000/api/v1/nodes/1              # 更新节点
curl -X DELETE http://master:8000/api/v1/nodes/1           # 删除节点

# 任务管理
curl -X POST http://master:8000/api/v1/tasks               # 创建任务
curl -X GET http://master:8000/api/v1/tasks/1              # 查看任务
curl -X GET http://master:8000/api/v1/tasks/1/progress     # 查看进度
curl -X GET http://master:8000/api/v1/tasks/1/logs         # 查看日志

# 系统监控
curl -X GET http://master:8000/health                      # 健康检查
curl -X GET http://master:8000/api/v1/nodes/stats          # 节点统计
curl -X GET http://master:8000/api/v1/tasks/stats          # 任务统计

# Systemd 服务
sudo systemctl start catchcore-node                         # 启动服务
sudo systemctl stop catchcore-node                          # 停止服务
sudo systemctl restart catchcore-node                       # 重启服务
sudo systemctl status catchcore-node                        # 查看状态
sudo journalctl -u catchcore-node -f                        # 实时日志

# Docker 操作
docker-compose up -d                                       # 启动所有服务
docker-compose up -d scanner-node-1                        # 启动特定节点
docker-compose ps                                          # 查看容器状态
docker logs catchcore-scanner-1                            # 查看日志
docker inspect catchcore-scanner-1                         # 检查配置
```

---

## 支持和反馈

如有问题或建议，请：
1. 查看此文档的常见问题部分
2. 查看项目 GitHub Issues
3. 提交新 Issue 或 Pull Request

**项目地址**: https://github.com/TaoKe-One/CatchCore
**文档更新**: 2025-11-14

---

