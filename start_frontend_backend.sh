#!/bin/bash

# 湖南省二附院精致饮片复核系统 - 启动脚本

echo "================================"
echo "  湖南省二附院精致饮片复核系统"
echo "================================"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查后端虚拟环境
if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
    echo "⚠️  后端虚拟环境不存在，正在创建..."
    cd "$SCRIPT_DIR/backend"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
    echo "✅ 后端虚拟环境创建完成"
fi

# 检查前端依赖
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "⚠️  前端依赖未安装，正在安装..."
    cd "$SCRIPT_DIR/frontend"
    npm install
    echo "✅ 前端依赖安装完成"
fi

# 杀掉可能占用端口的进程
echo "🔄 清理端口占用..."
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# 启动后端
echo "🚀 启动后端服务..."
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
USE_SQLITE=true python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端启动
sleep 3

# 启动前端
echo "🚀 启动前端服务..."
cd "$SCRIPT_DIR/frontend"
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"

echo ""
echo "================================"
echo "  系统启动完成！"
echo "================================"
echo "📍 前端地址: http://localhost:5173"
echo "📍 后端地址: http://localhost:8000"
echo "📍 API文档: http://localhost:8000/docs"
echo ""
echo "📝 默认登录账号: admin"
echo "📝 默认登录密码: 123456a@"
echo ""
echo "💡 查看日志: tail -f /tmp/backend.log /tmp/frontend.log"
echo "💡 停止服务: ./stop_system.sh"
echo ""
