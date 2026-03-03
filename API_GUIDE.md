# 湖南省二附院精致饮片复核系统 - 接口文档

## 系统说明

本文档描述了湖南省二附院精致饮片复核系统的所有后端接口。系统基于 FastAPI 框架开发，遵循 RESTful API 设计规范。

**基础信息**：
- 接口前缀：`/zyfh/api/v1/`
- 认证方式：Bearer Token（在请求头携带）
- 数据格式：JSON
- 字符编码：UTF-8

**通用响应格式**：
```json
{
    "code": "0000",
    "msg": "操作成功",
    "data": {},
    "timestamp": 1772323317000,
    "requestId": "REQ20260228001001"
}
```

**业务返回码**：
- `0000`：操作成功
- `1000`：请求参数错误
- `2000`：身份认证失败
- `3000`：权限不足
- `4000`：数据同步失败
- `5000`：服务器内部错误
- `6000`：设备故障/离线
- `7000`：二维码相关错误
- `8000`：复核相关错误

---

## 一、系统认证接口

### 1. 获取访问Token

**接口地址**：`POST /zyfh/api/v1/system/token/get`

**是否需要认证**：否

**请求参数**：
| 参数名 | 必选 | 类型 | 示例 | 说明 |
|--------|------|------|------|------|
| user_account | 是 | String | admin | 用户账号 |
| user_pwd | 是 | String | admin123 | 用户密码 |

**返回示例**：
```json
{
    "code": "0000",
    "msg": "操作成功",
    "data": {
        "token": "Bearer eyJhbGciOiJIUzI1NiJ9...",
        "expireTime": 1772409717000,
        "userInfo": {
            "userAccount": "admin",
            "userName": "超级管理员",
            "deptName": "系统管理"
        }
    },
    "timestamp": 1772323317000,
    "requestId": "REQ20260228001001"
}
```

### 2. 健康检查

**接口地址**：`GET /zyfh/api/v1/health`

**是否需要认证**：否

**返回示例**：
```json
{
    "code": "0000",
    "msg": "系统运行正常",
    "data": {"status": "ok"},
    "timestamp": 1772323317000,
    "requestId": "REQ20260228001002"
}
```

---

## 二、二维码管理模块

### 1. 新增/维护企业标志

**接口地址**：`POST /zyfh/api/v1/qrcode/enterprise/save`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| enterpriseCode | 是 | Integer | 企业标志编码（唯一） |
| enterpriseName | 是 | String | 企业全称 |
| status | 否 | Integer | 状态：1-启用，0-禁用，默认1 |
| createBy | 是 | String | 创建人账号 |

### 2. 二维码单条生成

**接口地址**：`POST /zyfh/api/v1/qrcode/generate/single`

**数据校验规则**：
- 规格：必须为"数字+g"格式，数字1-30（含）
- 批号：纯数字，长度5-10位（含）
- 数量：默认7，支持手动修改（仅数字）
- 重量：数字型，可保留1-4位小数，无单位（后台按kg存储）
- 院内编码：与HIS系统CJID字段比对，不存在则提醒
- 企业标志：必须为系统内已维护的编码

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| enterprise_code | 是 | Integer | 企业标志编码 |
| cj_id | 是 | String | 院内编码（CJID） |
| spec | 是 | String | 规格，如5g |
| batch_no | 是 | String | 批号，如2503050001 |
| num | 是 | Integer | 数量，默认7 |
| weight | 是 | Float | 重量（kg） |

**返回示例**：
```json
{
    "code": "0000",
    "msg": "操作成功",
    "data": {
        "qrcode_id": "QR20260228001001",
        "qrcode_content": "1;13310;5g;2503050001;7;0.035",
        "base64_str": "MjsxMzMxMDs1ZzsyMjAzMDUwMDAxOzc7MC4wMzU=",
        "qrcode_url": "http://localhost:8000/zyfh/qrcodes/QR20260228001001.png"
    }
}
```

### 3. 二维码批量生成

**接口地址**：`POST /zyfh/api/v1/qrcode/generate/batch`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| createBy | 是 | String | 创建人账号 |
| qrcodeList | 是 | Array | 二维码参数列表 |

**返回示例**：
```json
{
    "code": "0000",
    "msg": "操作成功",
    "data": {
        "successNum": 98,
        "failNum": 2,
        "failList": [...],
        "downloadUrl": "http://localhost:8000/zyfh/qrcodes/batch/20260228.zip"
    }
}
```

### 4. 二维码解析

**接口地址**：`POST /zyfh/api/v1/qrcode/parse`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| qrcode_string | 是 | String | Base64编码的二维码内容 |

### 5. 二维码校验

**接口地址**：`POST /zyfh/api/v1/qrcode/verify`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| qrcode_content | 是 | String | 二维码Base64字符串 |
| verifyBy | 是 | String | 校验人账号 |

**返回示例**：
```json
{
    "code": "0000",
    "data": {
        "decryptContent": "1;13310;5g;2503050001;7;0.035",
        "verifyResult": "SUCCESS",
        "verifyReason": null
    }
}
```

### 6. 二维码历史记录查询

**接口地址**：`GET /zyfh/api/v1/qrcode/record/query`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| enterprise_code | 否 | Integer | 企业标志编码 |
| cj_id | 否 | String | 院内编码 |
| batch_no | 否 | String | 批号 |
| verify_result | 否 | String | 校验结果 |
| start_time | 否 | String | 开始时间 |
| end_time | 否 | String | 结束时间 |
| page | 否 | Integer | 页码，默认1 |
| size | 否 | Integer | 每页条数，默认20 |

---

## 三、扫码复核模块

### 1. HIS处方信息同步

**接口地址**：`POST /zyfh/api/v1/check/his/sync`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 否 | String | 处方号（单条同步） |
| start_time | 否 | String | 开始时间（批量同步） |
| end_time | 否 | String | 结束时间（批量同步） |

### 2. 扫码复核初始化

**接口地址**：`POST /zyfh/api/v1/check/init`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 是 | String | 处方号 |
| check_by | 是 | String | 复核人员账号 |
| check_station | 是 | String | 复核台编号 |

### 3. 实时扫码复核

**接口地址**：`POST /zyfh/api/v1/check/scan`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 是 | String | 处方号 |
| basket_no | 是 | String | 筐号 |
| qrcode_content | 是 | String | 二维码Base64字符串 |
| check_by | 是 | String | 复核人员账号 |

**离线处理**：网络中断时返回 `OFFLINE_SAVED` 状态，数据保存至本地数据库，网络恢复后自动同步。

**返回示例**：
```json
{
    "code": "0000",
    "data": {
        "drug_name": "盐巴戟天",
        "scan_result": "SUCCESS",
        "cj_id": "13310",
        "spec": "5g",
        "batch_no": "2503050001",
        "num": 7,
        "weight": 0.035,
        "basket_no": "K20260228001",
        "scan_time": "2026-02-28T09:12:00"
    }
}
```

### 4. 复核进度保存

**接口地址**：`POST /zyfh/api/v1/check/progress/save`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 是 | String | 处方号 |
| check_by | 是 | String | 复核人员账号 |
| finished_drugs | 是 | Array | 已完成CJID列表 |
| unfinished_drugs | 是 | Array | 未完成CJID列表 |
| current_basket | 是 | String | 当前筐号 |

### 5. 复核完成提交

**接口地址**：`POST /zyfh/api/v1/check/submit`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 是 | String | 处方号 |
| check_by | 是 | String | 复核人员账号 |

---

## 四、错误提醒模块

### 1. 错误记录保存

**接口地址**：`POST /zyfh/api/v1/alert/error/save`

**说明**：内部联动接口，由扫码复核接口自动调用

### 2. 错误记录处理

**接口地址**：`PUT /zyfh/api/v1/alert/error/handle`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| error_id | 是 | String | 错误记录ID |
| handle_by | 是 | String | 处理人账号 |
| handle_result | 是 | String | 处理结果：REPLACE/ADD/CANCEL |
| handle_desc | 否 | String | 处理描述 |

### 3. 错误记录查询

**接口地址**：`GET /zyfh/api/v1/alert/error/list`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 否 | String | 处方号 |
| error_status | 否 | Integer | 错误状态：1-未处理，2-已处理 |

---

## 五、分筐管理模块

### 1. 筐号新增/维护

**接口地址**：`POST /zyfh/api/v1/basket/save`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| basket_no | 是 | String | 筐号 |
| basket_name | 否 | String | 筐名/备注 |
| status | 否 | Integer | 状态：1-启用，0-作废 |
| create_by | 是 | String | 创建人账号 |

### 2. 饮片分筐关联

**接口地址**：`POST /zyfh/api/v1/basket/relation/save`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 是 | String | 处方号 |
| basket_no | 是 | String | 筐号 |
| cj_id_list | 是 | Array | 院内编码列表 |
| create_by | 是 | String | 操作人账号 |

### 3. 分筐复核确认

**接口地址**：`POST /zyfh/api/v1/basket/check/confirm`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 是 | String | 处方号 |
| basket_no | 是 | String | 筐号 |
| confirm_by | 是 | String | 确认人账号 |

### 4. 筐号列表查询

**接口地址**：`GET /zyfh/api/v1/basket/list`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| status | 否 | Integer | 状态筛选 |

---

## 六、溯源管理模块

### 1. 复核溯源记录查询

**接口地址**：`GET /zyfh/api/v1/trace/record/query`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 否 | String | 处方号 |
| cj_id | 否 | String | 院内编码 |
| check_by | 否 | String | 复核人员账号 |
| start_time | 否 | String | 开始时间 |
| end_time | 否 | String | 结束时间 |
| page | 否 | Integer | 页码，默认1 |
| size | 否 | Integer | 每页条数，默认20 |

### 2. 视频监控联动查询

**接口地址**：`GET /zyfh/api/v1/trace/video/query`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no | 是 | String | 处方号 |
| scan_time | 是 | String | 扫码时间 |
| check_station | 是 | String | 复核台编号 |

### 3. 溯源报告生成

**接口地址**：`POST /zyfh/api/v1/trace/report/generate`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| pres_no_list | 是 | Array | 处方号列表 |
| report_type | 是 | String | 报告格式：PDF/EXCEL |
| generate_by | 是 | String | 生成人账号 |

---

## 七、工作量统计模块

### 1. 复核工作量统计

**接口地址**：`GET /zyfh/api/v1/stat/workload/query`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| stat_type | 是 | String | 统计维度：USER/TIME/PRES |
| check_by | 否 | String | 复核人员账号 |
| time_type | 否 | String | 时间类型：DAY/WEEK/MONTH |
| stat_time | 否 | String | 统计时间 |
| page | 否 | Integer | 页码，默认1 |
| size | 否 | Integer | 每页条数，默认20 |

### 2. 统计报告生成

**接口地址**：`POST /zyfh/api/v1/stat/report/generate`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| start_date | 是 | String | 开始日期 |
| end_date | 是 | String | 结束日期 |
| report_type | 是 | String | 报告类型 |
| generate_by | 是 | String | 生成人账号 |

---

## 八、系统管理模块

### 1. 系统用户新增/编辑

**接口地址**：`POST /zyfh/api/v1/sys/user/save`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| user_account | 是 | String | 用户账号 |
| user_pwd | 是 | String | 用户密码 |
| user_name | 是 | String | 用户姓名 |
| dept_name | 是 | String | 所属科室 |
| post | 是 | String | 岗位 |
| phone | 否 | String | 联系电话 |
| status | 否 | Integer | 状态：1-启用，0-禁用 |

### 2. 系统用户查询

**接口地址**：`GET /zyfh/api/v1/sys/user/list`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| user_account | 否 | String | 用户账号（模糊查询） |
| user_name | 否 | String | 用户姓名（模糊查询） |
| dept_name | 否 | String | 所属科室 |
| status | 否 | Integer | 状态 |
| page | 否 | Integer | 页码，默认1 |
| size | 否 | Integer | 每页条数，默认20 |

### 3. 系统用户删除

**接口地址**：`DELETE /zyfh/api/v1/sys/user/delete`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| id | 是 | Integer | 用户ID |
| operate_by | 是 | String | 操作人账号 |

### 4. 角色新增/编辑

**接口地址**：`POST /zyfh/api/v1/sys/role/save`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| role_code | 是 | String | 角色编码 |
| role_name | 是 | String | 角色名称 |
| role_permission | 是 | String | 权限标识 |
| role_desc | 否 | String | 角色描述 |
| status | 否 | Integer | 状态：1-启用，0-禁用 |

### 5. 角色列表查询

**接口地址**：`GET /zyfh/api/v1/sys/role/list`

### 6. 用户-角色关联绑定

**接口地址**：`POST /zyfh/api/v1/sys/user_role/bind`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| user_id | 是 | Integer | 用户ID |
| role_id_list | 是 | Array | 角色ID列表 |
| operate_by | 是 | String | 操作人账号 |

### 7. 设备注册/更新

**接口地址**：`POST /zyfh/api/v1/sys/device/save`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| device_no | 是 | String | 设备编号 |
| device_type | 是 | String | 设备类型：SCAN/PAD/PRINT/CAM |
| device_name | 是 | String | 设备名称 |
| bind_station | 否 | String | 绑定复核台 |
| bind_user | 否 | String | 绑定人员 |

### 8. 设备列表查询

**接口地址**：`GET /zyfh/api/v1/sys/device/list`

### 9. 院内药品基础数据同步

**接口地址**：`POST /zyfh/api/v1/sys/base/drug/sync/his`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| sync_type | 是 | String | 同步类型：ALL/UPDATE |
| operate_by | 是 | String | 操作人账号 |

### 10. 系统日志查询

**接口地址**：`GET /zyfh/api/v1/sys/log/query`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| log_type | 否 | String | 日志类型 |
| user_account | 否 | String | 用户账号 |

### 11. 系统参数配置

**接口地址**：`POST /zyfh/api/v1/sys/param/config/save`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| param_key | 是 | String | 参数键 |
| param_value | 是 | String | 参数值 |
| param_desc | 是 | String | 参数描述 |
| operate_by | 是 | String | 操作人账号 |

### 12. 系统参数查询

**接口地址**：`GET /zyfh/api/v1/sys/param/config/query`

### 13. 数据备份手动触发

**接口地址**：`POST /zyfh/api/v1/sys/data/backup/trigger`

**请求参数**：
| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| backup_type | 是 | String | 备份类型：FULL/INCREMENT |
| backup_desc | 否 | String | 备份描述 |
| operate_by | 是 | String | 操作人账号 |

### 14. 数据备份记录查询

**接口地址**：`GET /zyfh/api/v1/sys/data/backup/record/query`

---

## 九、离线数据同步

### 1. 离线数据同步

**接口地址**：`POST /zyfh/api/v1/system/offline/sync`

**说明**：将本地离线数据同步至服务器

**返回示例**：
```json
{
    "code": "0000",
    "data": {
        "synced_count": 15,
        "failed_count": 0,
        "total_processed": 15,
        "results": [...],
        "message": "离线数据同步完成，成功: 15，失败: 0"
    }
}
```

---

## 系统默认数据

### 默认管理员账号
- 账号：`admin`
- 密码：`admin123`
- 角色：超级管理员

### 默认企业列表
| 编码 | 企业名称 |
|------|----------|
| 1 | 亳州市沪谯药业有限公司 |
| 2 | 湖南三湘中药饮片有限公司 |
| 3 | 长沙新林制药有限公司 |
| 4 | 安徽亳药千草中药饮片有限公司 |
| 5 | 北京仟草中药饮片有限公司 |
| 6 | 天津尚药堂制药有限公司 |

### 默认角色列表
| 角色编码 | 角色名称 | 权限标识 |
|----------|----------|----------|
| SUPER_ADMIN | 超级管理员 | ALL |
| SYS_ADMIN | 系统管理员 | SYS:* |
| QR_MANAGER | 二维码管理员 | QR:* |
| REVIEWER | 复核员 | CHECK:* |
| VIEWER | 查询员 | VIEW:* |
| TRACE_MANAGER | 溯源管理员 | TRACE:* |

---

## 离线模式说明

系统支持离线操作，网络中断时：
1. 扫码复核、进度保存、提交等操作数据保存至本地SQLite数据库
2. 网络恢复后自动触发同步任务
3. 同步顺序：先扫码记录、进度保存，后提交记录
4. 失败记录会自动重试（最多10次）

---

## 开发和测试

### 启动系统

```bash
# 1. 安装依赖
pip install -r backend/requirements.txt

# 2. 启动后端服务
uvicorn backend.app.main:app --reload --port 8000

# 3. 访问前端
# http://localhost:8000/frontend/
```

### 运行测试

```bash
pytest backend/tests/
```

### 健康检查

```bash
curl http://localhost:8000/zyfh/api/v1/health
```

---

## 注意事项

1. **密码安全**：密码使用MD5加密存储，传输时建议使用HTTPS
2. **Token管理**：Token有效期为24小时，过期需重新获取
3. **参数校验**：所有接口都会进行严格的参数校验
4. **错误处理**：所有错误都会返回明确的错误码和错误信息
5. **数据一致性**：核心操作使用数据库事务保证数据一致性
6. **离线支持**：核心业务接口支持离线操作
7. **日志记录**：所有操作都会记录到系统日志中

---

**文档版本**：V1.0  
**最后更新**：2026年2月  
**维护团队**：湖南省二附院信息系统开发组
