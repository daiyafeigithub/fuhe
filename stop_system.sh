#!/bin/bash

echo "停止系统..."

# 停止后端 (端口 8000)
if command -v lsof &> /dev/null; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
elif command -v netstat &> /dev/null; then
    for pid in $(netstat -ano 2>/dev/null | grep ':8000' | awk '{print $5}' | sort -u); do
        taskkill //F //PID $pid 2>/dev/null || true
    done
fi

# 停止前端 (端口 3000)
if command -v lsof &> /dev/null; then
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
elif command -v netstat &> /dev/null; then
    for pid in $(netstat -ano 2>/dev/null | grep ':3000' | awk '{print $5}' | sort -u); do
        taskkill //F //PID $pid 2>/dev/null || true
    done
fi

# 停止 uvicorn 和 node 进程
pkill -f uvicorn 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

echo "系统已停止"
