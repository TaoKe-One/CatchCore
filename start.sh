#!/bin/bash

# CatchCore startup script

set -e

echo "================================"
echo "CatchCore - 漏洞猎手的核心捕鼠器"
echo "================================"
echo ""

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon 未运行，请启动 Docker"
    exit 1
fi

echo "✅ Docker 检查通过"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose 未找到，使用 'docker compose' 命令"
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "🚀 启动 CatchCore 服务..."
echo ""

# Start services
$DOCKER_COMPOSE up -d

echo ""
echo "✅ 所有服务启动完成！"
echo ""
echo "📍 服务地址："
echo "  - 前端: http://localhost:5173"
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - InfluxDB: http://localhost:8086"
echo ""
echo "🔐 默认登录信息："
echo "  - 数据库用户: catchcore"
echo "  - 数据库密码: catchcore"
echo ""
echo "📝 查看日志: $DOCKER_COMPOSE logs -f [service_name]"
echo "⏹️  停止服务: $DOCKER_COMPOSE down"
echo ""
