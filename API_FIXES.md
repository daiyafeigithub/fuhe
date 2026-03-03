# API 字段名映射修复说明

## 问题
后端使用下划线命名（snake_case），前端使用驼峰命名（camelCase），导致 API 调用失败。

## 已修复的接口

### 1. 登录接口
**前端发送:** `userAccount`, `userPwd`
**后端接收:** `user_account`, `user_pwd`

**修复位置:** `frontend/src/api/index.js`
```javascript
export const login = (data) => api.post('/system/token/get', {
  user_account: data.userAccount,
  user_pwd: data.userPwd
})
```

### 2. 二维码生成接口
**前端发送:** `enterpriseCode`, `cjId`, `batchNo`, `num`, `weight`
**后端接收:** `enterprise_code`, `cj_id`, `batch_no`, `num`, `weight`

**修复位置:** `frontend/src/api/index.js`
```javascript
export const generateQRCode = (data) => api.post('/qrcode/generate/single', {
  enterprise_code: data.enterpriseCode,
  cj_id: data.cjId,
  spec: data.spec,
  batch_no: data.batchNo,
  num: data.num,
  weight: data.weight
})
```

**响应字段映射:**
- `qrcodeUrl` ← `qrcode_url`
- `qrcodeContent` ← `qrcode_content`
- `base64Str` ← `base64_str`
- `qrcodeId` ← `qrcode_id`

### 3. CORS 跨域配置
**修复位置:** `backend/app/main.py`

添加了以下允许的源:
- http://localhost:3000
- http://localhost:3001
- http://localhost:3002
- http://localhost:5173
- http://127.0.0.1:3000
- http://127.0.0.1:3001
- http://127.0.0.1:3002
- http://127.0.0.1:5173

### 4. 默认管理员密码
**修复:** 更新管理员密码为 `123456a@`

## 待修复的接口

以下接口仍需要字段名映射:

### 扫码复核模块
- `initCheck` - 处方初始化
- `scanCheck` - 扫码复核
- `saveProgress` - 保存进度
- `submitCheck` - 提交复核

### 错误提醒模块
- `handleError` - 错误处理
- `getErrorList` - 错误列表

### 分筐管理模块
- `saveBasket` - 保存筐号
- `saveBasketRelation` - 保存关联
- `confirmBasket` - 确认分筐

### 溯源管理模块
- `getTraceRecords` - 溯源记录
- `generateReport` - 生成报告

### 工作量统计模块
- `getWorkloadStat` - 工作量统计

### 系统管理模块
- `saveUser` - 保存用户
- `deleteUser` - 删除用户
- `saveRole` - 保存角色

## 测试方法

### 测试登录
```bash
curl -X POST http://localhost:8000/zyfh/api/v1/system/token/get \
  -H "Content-Type: application/json" \
  -d '{"user_account":"admin","user_pwd":"123456a@"}'
```

### 测试二维码生成
```bash
curl -X POST http://localhost:8000/zyfh/api/v1/qrcode/generate/single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "enterprise_code": 1,
    "cj_id": "13310",
    "spec": "5g",
    "batch_no": "2503050001",
    "num": 7,
    "weight": 0.035
  }'
```

## 注意事项

1. **认证**: 大部分接口需要在请求头中携带 Token
2. **数据类型**: 确保字段类型正确（整数、浮点数、字符串等）
3. **必填字段**: 检查必填字段是否都已提供
4. **格式验证**:
   - 规格: 必须为 "数字+g" 格式，如 "5g"
   - 批号: 5-10 位纯数字
   - 重量: 0-100kg 的浮点数
