# 饮片复核系统 - 快速启动指南

## 系统概述

本系统是医院级中药饮片复核系统，采用前后端分离架构：
- **前端**: Vue.js 3 + Vite + Element Plus + Pinia
- **后端**: FastAPI + SQLAlchemy + SQLite/MySQL

## 快速启动

### 方式一：使用启动脚本（推荐）

```bash
# 启动系统
./start_frontend_backend.sh

# 停止系统
./stop_system.sh
```

### 方式二：手动启动

#### 1. 启动后端

```bash
cd backend

# 如果是第一次运行，需要创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动后端服务（使用 SQLite）
USE_SQLITE=true python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 启动前端

```bash
cd frontend

# 如果是第一次运行，需要安装依赖
npm install

# 启动前端开发服务器
npm run dev
```

## 访问地址

- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 默认登录账号

```
账号: admin
密码: 123456a@
```

## 主要功能模块

1. **工作台** - 系统概览和快捷操作
2. **二维码管理** - 二维码生成、校验和历史查询
3. **扫码复核** - 处方复核、扫码、进度管理
4. **错误提醒** - 错误记录查询和处理
5. **分筐管理** - 筐号管理和处方分筐关联
6. **溯源管理** - 复核记录溯源和视频查看
7. **工作量统计** - 多维度工作量统计
8. **系统管理** - 用户和角色管理

## 数据库配置

系统支持两种数据库：

### SQLite（默认，开发/测试）
无需额外配置，自动创建 `zyyz_fuping.db` 文件

### MySQL（生产环境）
修改 `backend/app/database.py` 中的连接配置：
```python
DATABASE_URL = "mysql+pymysql://用户名:密码@主机:端口/数据库名"
```

## 离线模式

系统支持离线操作：
1. 本地缓存扫码记录和复核进度
2. 网络恢复后自动同步数据
3. 使用 SQLite 作为离线数据库

## 日志查看

```bash
# 查看后端日志
tail -f /tmp/backend.log

# 查看前端日志
tail -f /tmp/frontend.log
```

## 常见问题

### Q: 启动后端时提示端口被占用
```bash
# 查看占用端口的进程
lsof -i:8000

# 杀掉进程
kill -9 <PID>
```

### Q: 前端无法连接后端
1. 检查后端是否正常运行
2. 检查 `frontend/src/api/index.js` 中的 `baseURL` 配置
3. 确保防火墙没有阻止 8000 端口

### Q: 登录失败
1. 检查数据库是否已初始化
2. 检查用户名密码是否正确
3. 查看后端日志获取详细错误信息

## 技术支持

如有问题，请查看：
- API 文档: http://localhost:8000/docs
- 后端日志: /tmp/backend.log
- 前端日志: /tmp/frontend.log
