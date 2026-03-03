#!/bin/bash

# 湖南省二附院精致饮片复核系统 - 启动脚本

echo "=========================================="
echo "  湖南省二附院精致饮片复核系统"
echo "  系统启动脚本"
echo "=========================================="
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python3，请先安装 Python3"
    exit 1
fi

echo "✅ Python3 已安装"

# 检查是否已存在虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv .venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 检查依赖是否已安装
if [ ! -f ".venv/installed" ]; then
    echo "📦 安装依赖包..."
    pip install -q -r backend/requirements.txt
    touch .venv/installed
    echo "✅ 依赖包安装成功"
else
    echo "✅ 依赖包已安装"
fi

# 检查数据库
echo "🗄️  检查数据库..."
if [ ! -f "zyyz_fuping.db" ]; then
    echo "✅ 将自动创建 SQLite 数据库"
fi

# 启动系统
echo ""
echo "🚀 启动系统服务..."
echo "=========================================="
echo "后端服务地址：http://localhost:8000"
echo "前端访问地址：http://localhost:8000/frontend/"
echo "接口文档地址：http://localhost:8000/zyfh/api/v1/docs"
echo "健康检查地址：http://localhost:8000/zyfh/api/v1/health"
echo "=========================================="
echo ""
echo "💡 提示："
echo "  - 默认管理员账号：admin / admin123"
echo "  - 按 Ctrl+C 停止服务"
echo ""

# 启动 FastAPI 服务
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
