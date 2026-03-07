#!/bin/bash

# 饮片复核系统 - 启动脚本

# 获取脚本所在目录并切换
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  饮片复核系统"
echo "=========================================="
echo ""

# 检测 Python
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
    VENV_PATH=".venv"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    VENV_PATH=".venv"
else
    echo "创建 Python 虚拟环境..."
    python3 -m venv .venv
    if [ -f ".venv/Scripts/python.exe" ]; then
        PYTHON=".venv/Scripts/python.exe"
        VENV_PATH=".venv"
    else
        PYTHON=".venv/bin/python"
        VENV_PATH=".venv"
    fi
fi

# 检测 npm
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到 npm，请先安装 Node.js"
    exit 1
fi

# 杀掉可能占用端口的进程
echo "清理端口占用..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

echo "安装后端依赖..."
"$PYTHON" -m pip install -q -r backend/requirements.txt 2>/dev/null

echo "安装前端依赖..."
cd frontend && npm install --silent 2>/dev/null && cd ..

echo ""
echo "启动服务..."
echo "=========================================="
echo "后端 API:  http://localhost:8000"
echo "前端界面:  http://localhost:3000"
echo "API 文档:  http://localhost:8000/zyfh/api/v1/docs"
echo "=========================================="
echo "默认账号: admin / admin123"
echo "按 Ctrl+C 停止所有服务"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "停止服务..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    # 额外清理可能的进程
    pkill -f uvicorn 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

# 启动后端
"$PYTHON" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

# 等待子进程
wait
