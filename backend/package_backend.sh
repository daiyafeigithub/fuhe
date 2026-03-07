#!/usr/bin/env bash

set -euo pipefail

show_help() {
    cat <<'EOF'
用法:
  sh package_backend.sh [版本号]

说明:
  - 在 backend 目录生成后端发布包（tar.gz）
  - 发布包内包含:
      backend/                后端代码与依赖文件
      Dockerfile              Docker 构建文件
      deploy_backend_docker.sh 解压+Docker部署脚本
      README_DEPLOY.md        部署说明

示例:
  sh package_backend.sh
  sh package_backend.sh v1.2.0
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

if ! command -v tar >/dev/null 2>&1; then
    echo "错误: 未检测到 tar 命令。"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VERSION="${1:-$(date +%Y%m%d_%H%M%S)}"
PACKAGE_NAME="fuhe-backend-${VERSION}"
DIST_DIR="$SCRIPT_DIR/dist"
WORK_DIR="$SCRIPT_DIR/.build/$PACKAGE_NAME"
PACKAGE_ROOT="$WORK_DIR/$PACKAGE_NAME"

rm -rf "$WORK_DIR"
mkdir -p "$DIST_DIR" "$PACKAGE_ROOT/backend"

echo "准备后端文件..."
cp -R "$SCRIPT_DIR/app" "$PACKAGE_ROOT/backend/"

if [[ -d "$SCRIPT_DIR/db" ]]; then
    cp -R "$SCRIPT_DIR/db" "$PACKAGE_ROOT/backend/"
fi

for file in requirements.txt openapi.yaml; do
    if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
        echo "错误: 缺少必需文件 backend/$file"
        exit 1
    fi
    cp "$SCRIPT_DIR/$file" "$PACKAGE_ROOT/backend/"
done

for data_file in zyyz_fuping.db local_offline.db; do
    if [[ -f "$SCRIPT_DIR/$data_file" ]]; then
        cp "$SCRIPT_DIR/$data_file" "$PACKAGE_ROOT/backend/"
    fi
done

find "$PACKAGE_ROOT/backend" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$PACKAGE_ROOT/backend" -type f -name "*.pyc" -delete

if [[ -f "$PROJECT_ROOT/Dockerfile" ]]; then
    cp "$PROJECT_ROOT/Dockerfile" "$PACKAGE_ROOT/Dockerfile"
else
    cat > "$PACKAGE_ROOT/Dockerfile" <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
fi

cp "$SCRIPT_DIR/deploy_backend_docker.sh" "$PACKAGE_ROOT/deploy_backend_docker.sh"
chmod +x "$PACKAGE_ROOT/deploy_backend_docker.sh"

cat > "$PACKAGE_ROOT/README_DEPLOY.md" <<'EOF'
# 后端 Docker 部署说明

## 1. 解压发布包

```bash
tar -xzf fuhe-backend-<版本号>.tar.gz
cd fuhe-backend-<版本号>
```

## 2. 执行部署脚本

```bash
sh deploy_backend_docker.sh
```

或直接传入压缩包自动解压并部署：

```bash
sh deploy_backend_docker.sh /path/to/fuhe-backend-<版本号>.tar.gz
```

## 3. 常用环境变量

- `IMAGE_NAME`：镜像名（默认 `fuhe-backend`）
- `CONTAINER_NAME`：容器名（默认 `fuhe-backend`）
- `HOST_PORT`：主机端口（默认 `8000`）
- `USE_SQLITE`：是否使用 SQLite（默认 `true`）
- `DATA_DIR`：数据持久化目录（默认 `<部署目录>/data`）

示例：

```bash
HOST_PORT=18000 CONTAINER_NAME=fuhe-prod sh deploy_backend_docker.sh
```
EOF

ARCHIVE_PATH="$DIST_DIR/${PACKAGE_NAME}.tar.gz"
echo "生成压缩包: $ARCHIVE_PATH"
(
    cd "$WORK_DIR"
    tar -czf "$ARCHIVE_PATH" "$PACKAGE_NAME"
)

rm -rf "$WORK_DIR"

echo ""
echo "打包完成"
echo "发布包: $ARCHIVE_PATH"
echo "可使用如下命令部署:"
echo "  sh $SCRIPT_DIR/deploy_backend_docker.sh $ARCHIVE_PATH"
