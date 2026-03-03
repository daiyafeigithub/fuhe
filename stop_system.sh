#!/bin/bash

echo "⏹️  正在停止系统..."

# 停止后端
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
echo "✅ 后端服务已停止"

# 停止前端
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
echo "✅ 前端服务已停止"

echo "👋 系统已停止"
