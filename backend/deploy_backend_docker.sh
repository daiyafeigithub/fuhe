#!/usr/bin/env bash

set -euo pipefail

show_help() {
    cat <<'EOF'
用法:
  1) 直接部署已解压目录（当前目录需包含 Dockerfile 和 backend/）
     sh deploy_backend_docker.sh

  2) 传入打包文件，自动解压并部署
     sh deploy_backend_docker.sh /path/to/fuhe-backend-xxxx.tar.gz [解压目录]

可选环境变量:
  IMAGE_NAME       Docker 镜像名（默认: fuhe-backend）
  CONTAINER_NAME   Docker 容器名（默认: fuhe-backend）
  HOST_PORT        主机端口（默认: 8000）
  CONTAINER_PORT   容器端口（默认: 8000）
  USE_SQLITE       是否启用 SQLite（默认: true）
  RESTART_POLICY   重启策略（默认: unless-stopped）
  DATA_DIR         持久化目录（默认: <部署目录>/data）
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "错误: 未检测到 docker，请先安装 Docker。"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "错误: Docker 服务未运行，请先启动 Docker。"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$SCRIPT_DIR"

if [[ -n "${1:-}" ]]; then
    PACKAGE_FILE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
    if [[ ! -f "$PACKAGE_FILE" ]]; then
        echo "错误: 找不到打包文件: $PACKAGE_FILE"
        exit 1
    fi

    EXTRACT_BASE="${2:-$SCRIPT_DIR/deployments}"
    mkdir -p "$EXTRACT_BASE"
    EXTRACT_BASE="$(cd "$EXTRACT_BASE" && pwd)"

    TOP_LEVEL_DIR="$(tar -tzf "$PACKAGE_FILE" | head -n 1 | cut -d '/' -f 1)"
    if [[ -z "$TOP_LEVEL_DIR" ]]; then
        echo "错误: 打包文件结构异常，无法识别根目录。"
        exit 1
    fi

    echo "解压发布包到: $EXTRACT_BASE"
    tar -xzf "$PACKAGE_FILE" -C "$EXTRACT_BASE"
    DEPLOY_DIR="$EXTRACT_BASE/$TOP_LEVEL_DIR"
fi

if [[ ! -f "$DEPLOY_DIR/Dockerfile" || ! -d "$DEPLOY_DIR/backend" ]]; then
    echo "错误: 部署目录缺少 Dockerfile 或 backend/ 目录: $DEPLOY_DIR"
    exit 1
fi

IMAGE_NAME="${IMAGE_NAME:-fuhe-backend}"
CONTAINER_NAME="${CONTAINER_NAME:-fuhe-backend}"
HOST_PORT="${HOST_PORT:-8000}"
CONTAINER_PORT="${CONTAINER_PORT:-8000}"
USE_SQLITE="${USE_SQLITE:-true}"
RESTART_POLICY="${RESTART_POLICY:-unless-stopped}"
DATA_DIR="${DATA_DIR:-$DEPLOY_DIR/data}"

mkdir -p "$DATA_DIR/qrcodes" "$DATA_DIR/reports"
touch "$DATA_DIR/zyyz_fuping.db" "$DATA_DIR/local_offline.db"
DATA_DIR="$(cd "$DATA_DIR" && pwd)"

echo "构建镜像: $IMAGE_NAME:latest"
docker build -t "$IMAGE_NAME:latest" "$DEPLOY_DIR"

if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
    echo "移除旧容器: $CONTAINER_NAME"
    docker rm -f "$CONTAINER_NAME" >/dev/null
fi

echo "启动新容器: $CONTAINER_NAME"
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart "$RESTART_POLICY" \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    -e "USE_SQLITE=$USE_SQLITE" \
    -v "$DATA_DIR/zyyz_fuping.db:/app/zyyz_fuping.db" \
    -v "$DATA_DIR/local_offline.db:/app/local_offline.db" \
    -v "$DATA_DIR/qrcodes:/app/qrcodes" \
    -v "$DATA_DIR/reports:/app/reports" \
    "$IMAGE_NAME:latest" >/dev/null

echo ""
echo "部署完成"
echo "部署目录: $DEPLOY_DIR"
echo "数据目录: $DATA_DIR"
echo "访问地址: http://localhost:${HOST_PORT}/zyfh/api/v1/docs"
echo "查看日志: docker logs -f $CONTAINER_NAME"
