# 饮片复核系统

## 系统概述

本系统是医院级中药饮片复核管理系统，实现基于二维码的扫码复核、智能错误提醒、分筐复核、全流程溯源和工作量统计等核心功能。

### 核心功能

- **二维码管理**：标准化生成、印制校验、离线解析、历史查询
- **扫码复核**：HIS处方同步、实时扫码、中断续核、批量确认
- **智能错误提醒**：药品错误/数量错误自动识别、多维度实时提醒
- **分筐复核**：筐号管理、分筐关联、分筐确认、进度可视化
- **复核溯源**：扫码记录溯源、视频监控联动、溯源报告生成
- **工作量统计**：自动统计、多维度查询、报表生成、数据导出
- **系统管理**：用户权限、基础数据、设备管理、日志记录、数据备份

### 技术架构

- **后端框架**：FastAPI（轻量级，可快速迭代）
- **数据库**：MySQL 8.0（生产）/ SQLite（开发测试）
- **前端**：原生 HTML + JavaScript（支持 PWA 离线功能）
- **认证方式**：JWT Token
- **离线支持**：本地 SQLite 缓存 + 网络恢复自动同步

## 快速开始

### 开发环境

#### 1. 创建并激活 Python 虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

#### 2. 安装依赖

```bash
pip install -r backend/requirements.txt
```

#### 3. 配置数据库

**使用 MySQL（生产环境）**：
```bash
# 修改 backend/app/database.py 中的数据库连接信息
DATABASE_URL = "mysql+pymysql://用户名:密码@localhost:3306/zyyz_fuping"
```

**使用 SQLite（开发环境）**：
```bash
# 设置环境变量
export USE_SQLITE=true
```

#### 4. 启动后端服务

```bash
uvicorn backend.app.main:app --reload --port 8000
```

#### 5. 访问系统

- 前端界面：http://localhost:8000/frontend/
- 接口文档：http://localhost:8000/zyfh/api/v1/docs
- 健康检查：http://localhost:8000/zyfh/api/v1/health

### 运行测试

```bash
# 在激活的虚拟环境中
pytest backend/tests/ -v
```

## 默认账号

| 类型 | 账号 | 密码 | 说明 |
|------|------|------|------|
| 超级管理员 | admin | admin123 | 拥有所有权限 |

## 默认数据

### 企业列表

| 编码 | 企业名称 |
|------|----------|
| 1 | 亳州市沪谯药业有限公司 |
| 2 | 湖南三湘中药饮片有限公司 |
| 3 | 长沙新林制药有限公司 |
| 4 | 安徽亳药千草中药饮片有限公司 |
| 5 | 北京仟草中药饮片有限公司 |
| 6 | 天津尚药堂制药有限公司 |

### 角色列表

| 角色编码 | 角色名称 | 权限 |
|----------|----------|------|
| SUPER_ADMIN | 超级管理员 | ALL |
| SYS_ADMIN | 系统管理员 | SYS:* |
| QR_MANAGER | 二维码管理员 | QR:* |
| REVIEWER | 复核员 | CHECK:* |
| VIEWER | 查询员 | VIEW:* |
| TRACE_MANAGER | 溯源管理员 | TRACE:* |

## 接口文档

详细的接口文档请参考 `API_GUIDE.md`，包含：
- 所有接口的详细说明
- 请求参数和返回格式
- 业务返回码说明
- 离线模式说明
- 开发和测试指南

## 系统优化

根据 `guide.md` 要求，系统已完成以下优化：

### 1. 功能完整性
- ✅ 补充所有7大功能模块的核心功能
- ✅ 完善二维码生成的数据校验逻辑
- ✅ 优化扫码复核的参数校验和错误处理
- ✅ 补充缺失的接口（角色列表、用户删除等）

### 2. 数据规范性
- ✅ 补充数据库表字段和索引
- ✅ 完善默认数据初始化（企业列表）
- ✅ 优化数据结构和关系

### 3. 接口标准化
- ✅ 统一接口响应格式
- ✅ 统一业务返回码
- ✅ 完善接口文档

### 4. 用户体验
- ✅ 前端界面优化
- ✅ 添加加载状态指示器
- ✅ 增强错误提示和表单验证
- ✅ 统一 API 调用封装

### 5. 系统可靠性
- ✅ 完善参数校验
- ✅ 优化错误处理
- ✅ 完善离线数据同步逻辑

## 目录结构

```
fuhe/
├── backend/              # 后端代码
│   ├── app/            # 应用主目录
│   │   ├── main.py     # FastAPI 主应用
│   │   ├── models.py   # 数据库模型
│   │   ├── schemas.py  # Pydantic 模型
│   │   └── database.py # 数据库配置
│   ├── tests/          # 测试代码
│   ├── requirements.txt # Python 依赖
│   └── openapi.yaml    # OpenAPI 规范
├── frontend/           # 前端代码
│   ├── index.html      # 主页面
│   └── sw.js          # Service Worker（PWA）
├── logs/              # 日志目录
├── zyyz_fuping.db    # SQLite 数据库（开发环境）
├── local_offline.db   # 离线数据缓存
├── guide.md           # 功能详细设计文档
├── API_GUIDE.md       # 接口文档
├── OPTIMIZATION_REPORT.md  # 优化报告
├── README.md          # 本文件
└── start_system.sh    # 系统启动脚本
```

## 核心业务流程

### 1. 二维码生成流程

```
选择企业 → 输入药品信息 → 数据校验 → 生成二维码 → 保存记录
```

### 2. 扫码复核流程

```
同步处方 → 初始化复核 → 扫码复核（可中断续核） → 提交复核结果
```

### 3. 分筐复核流程

```
创建筐号 → 关联饮片 → 分筐扫码 → 筐确认 → 处方提交
```

### 4. 错误处理流程

```
扫码检测错误 → 实时提醒 → 标注处理结果 → 提交复核
```

## 离线支持

系统支持完整的离线操作：

1. **离线缓存**：扫码记录、进度保存等数据本地缓存
2. **自动同步**：网络恢复后自动同步离线数据
3. **无缝切换**：在线/离线模式自动切换，用户无感知

## 系统集成

### HIS 系统集成

- 处方信息同步（已实现 Mock，待对接真实接口）
- 药品基础数据同步
- 复核结果回传

### 视频监控系统集成

- 扫码时间与视频录像精准匹配
- 视频地址自动获取和续期
- 视频联动查询（已实现 Mock，待对接真实接口）

## 部署说明

### 开发环境部署

```bash
# 1. 启动数据库（如果使用 MySQL）
mysql -u root -p
CREATE DATABASE zyyz_fuping DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

# 2. 启动后端
uvicorn backend.app.main:app --reload --port 8000

# 3. 访问系统
# http://localhost:8000/frontend/
```

### 生产环境部署

```bash
# 1. 使用 Gunicorn + Uvicorn
pip install gunicorn
gunicorn backend.app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000

# 2. 使用 Nginx 反向代理
# 配置 Nginx 指向 FastAPI 服务

# 3. 使用 Docker 部署
docker build -t fuhe-system .
docker run -p 8000:8000 fuhe-system
```

## 常见问题

### Q1: 数据库连接失败怎么办？

A: 检查数据库连接信息是否正确，或者设置 `USE_SQLITE=true` 使用 SQLite 模式。

### Q2: 如何切换到生产数据库？

A: 修改 `backend/app/database.py` 中的 `DATABASE_URL`，使用 MySQL 连接字符串。

### Q3: 离线数据如何同步？

A: 调用 `/zyfh/api/v1/system/offline/sync` 接口，或等待系统自动同步。

### Q4: 如何查看系统日志？

A: 日志文件存储在 `logs/` 目录下，或通过系统管理模块的日志查询功能查看。

## 后续计划

- [ ] 集成真实的 HIS 系统接口
- [ ] 集成真实的视频监控系统
- [ ] 实现二维码图片生成功能
- [ ] 实现溯源报告 PDF 生成
- [ ] 优化前端界面（使用现代前端框架）
- [ ] 添加单元测试和集成测试
- [ ] 性能优化（缓存、数据库优化）
- [ ] 安全加固（接口限流、数据加密）

## 文档

- **功能详细设计**：`guide.md`
- **接口文档**：`API_GUIDE.md`
- **优化报告**：`OPTIMIZATION_REPORT.md`
- **完成总结**：`COMPLETION_SUMMARY.md`
- **最终报告**：`FINAL_REPORT.md`

## 联系方式

如有问题或建议，请联系系统开发团队。

---

**系统版本**：V1.0  
**最后更新**：2026年3月2日  
**维护团队**：湖南省二附院信息系统开发组
