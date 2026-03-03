from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import base64
import hashlib
import jwt
import json
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional
import os

from app.database import get_db, Base, engine
from app import models, schemas

# 创建所有数据库表
Base.metadata.create_all(bind=engine)

# ========== CORS 跨域配置 ==========
app = FastAPI(title="湖南省二附院精致饮片复核系统 API", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 离线处理功能 ==========
# 为了支持离线模式，我们需要一个本地SQLite数据库来存储离线数据
import sqlite3
import threading
from contextlib import contextmanager

# 线程锁，确保数据库操作的线程安全
local_db_lock = threading.Lock()

def init_local_db():
    """初始化本地SQLite数据库，用于离线数据存储"""
    conn = sqlite3.connect('local_offline.db')
    cursor = conn.cursor()
    
    # 创建离线数据表，结构与主数据库表保持一致
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS local_scan_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pres_no TEXT NOT NULL,
            basket_no TEXT NOT NULL,
            qrcode_content TEXT NOT NULL,
            check_by TEXT NOT NULL,
            scan_time TEXT NOT NULL,
            is_sync INTEGER DEFAULT 0,
            sync_time TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS local_progress_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pres_no TEXT NOT NULL,
            check_by TEXT NOT NULL,
            progress_info TEXT NOT NULL,
            save_time TEXT NOT NULL,
            is_sync INTEGER DEFAULT 0,
            sync_time TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS local_submit_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pres_no TEXT NOT NULL,
            check_by TEXT NOT NULL,
            submit_time TEXT NOT NULL,
            is_sync INTEGER DEFAULT 0,
            sync_time TEXT
        )
    """)
    
    conn.commit()
    conn.close()

# 初始化本地数据库
init_local_db()

def save_offline_scan_record(pres_no, basket_no, qrcode_content, check_by):
    """保存离线扫码记录"""
    with local_db_lock:
        conn = sqlite3.connect('local_offline.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO local_scan_records 
            (pres_no, basket_no, qrcode_content, check_by, scan_time)
            VALUES (?, ?, ?, ?, ?)
        """, (pres_no, basket_no, qrcode_content, check_by, datetime.now().isoformat()))
        conn.commit()
        conn.close()

def save_offline_progress_record(pres_no, check_by, progress_info):
    """保存离线进度记录"""
    with local_db_lock:
        conn = sqlite3.connect('local_offline.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO local_progress_records 
            (pres_no, check_by, progress_info, save_time)
            VALUES (?, ?, ?, ?)
        """, (pres_no, check_by, str(progress_info), datetime.now().isoformat()))
        conn.commit()
        conn.close()

def save_offline_submit_record(pres_no, check_by):
    """保存离线提交记录"""
    with local_db_lock:
        conn = sqlite3.connect('local_offline.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO local_submit_records 
            (pres_no, check_by, submit_time)
            VALUES (?, ?, ?)
        """, (pres_no, check_by, datetime.now().isoformat()))
        conn.commit()
        conn.close()

def get_offline_records(table_name):
    """获取未同步的离线记录"""
    with local_db_lock:
        conn = sqlite3.connect('local_offline.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE is_sync = 0")
        records = cursor.fetchall()
        conn.close()
        return records

def mark_synced_record(table_name, record_id):
    """标记记录为已同步"""
    with local_db_lock:
        conn = sqlite3.connect('local_offline.db')
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE {table_name} 
            SET is_sync = 1, sync_time = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), record_id))
        conn.commit()
        conn.close()

def check_network_connection():
    """检查网络连接状态"""
    import urllib.request
    try:
        # 尝试连接外部网站来检查网络状态
        urllib.request.urlopen('http://www.baidu.com', timeout=3)
        return True
    except:
        return False

# 初始化默认数据
def init_default_data():
    """创建默认的管理员用户和企业数据"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        # 检查是否已初始化
        admin_user = db.query(models.SysUser).filter(models.SysUser.user_account == "admin").first()
        if admin_user:
            return
        
        # 创建管理员用户
        admin = models.SysUser(
            user_account="admin",
            user_name="超级管理员",
            user_pwd=hashlib.md5("admin123".encode()).hexdigest(),
            dept_name="系统管理",
            post="系统管理员",
            create_by="system"
        )
        db.add(admin)
        db.flush()
        
        # 创建默认企业（按照 guide.md 中的6家企业）
        enterprises = [
            (1, '亳州市沪谯药业有限公司'),
            (2, '湖南三湘中药饮片有限公司'),
            (3, '长沙新林制药有限公司'),
            (4, '安徽亳药千草中药饮片有限公司'),
            (5, '北京仟草中药饮片有限公司'),
            (6, '天津尚药堂制药有限公司')
        ]
        for code, name in enterprises:
            enterprise = models.Enterprise(
                enterprise_code=code,
                enterprise_name=name,
                create_by="system",
                status=1
            )
            db.add(enterprise)
        
        # 创建默认角色
        roles = [
            ("SUPER_ADMIN", "超级管理员", "ALL"),
            ("SYS_ADMIN", "系统管理员", "SYS:*"),
            ("QR_MANAGER", "二维码管理员", "QR:*"),
            ("REVIEWER", "复核员", "CHECK:*"),
            ("VIEWER", "查询员", "VIEW:*"),
            ("TRACE_MANAGER", "溯源管理员", "TRACE:*")
        ]
        for role_code, role_name, permissions in roles:
            role = models.SysRole(
                role_code=role_code,
                role_name=role_name,
                role_permission=permissions,
                role_desc=f"{role_name}角色",
                create_time=datetime.utcnow()
            )
            db.add(role)
        
        db.commit()
        print("✅ 默认数据初始化成功")
        print("   默认管理员账号: admin / admin123")
    except Exception as e:
        db.rollback()
        import traceback
        print(f"⚠️ 初始化数据失败: {str(e)[:200]}")
        # traceback.print_exc()
    finally:
        db.close()

# 配置静态文件服务（前端应用）
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

    # 为sw.js提供单独的路由
    @app.get("/sw.js")
    async def get_service_worker():
        sw_path = os.path.join(frontend_path, "sw.js")
        if os.path.exists(sw_path):
            from fastapi.responses import FileResponse
            return FileResponse(sw_path, media_type="application/javascript")
        else:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse("", status_code=404)

# 应用启动时初始化数据
init_default_data()

# ========== 通用工具函数 ==========

def get_request_id():
    """生成请求唯一标识"""
    return f"REQ{int(time.time()*1000)}"

def success_response(data=None, msg="操作成功"):
    """成功响应"""
    return {
        "code": "0000",
        "msg": msg,
        "data": data,
        "timestamp": int(time.time() * 1000),
        "requestId": get_request_id()
    }

def error_response(code="5000", msg="服务器错误"):
    """错误响应"""
    return {
        "code": code,
        "msg": msg,
        "data": None,
        "timestamp": int(time.time() * 1000),
        "requestId": get_request_id()
    }

def generate_token(user_id: int) -> str:
    """生成 JWT Token"""
    payload = {"user_id": user_id, "exp": int(time.time()) + 86400}
    token = jwt.encode(payload, "secret_key", algorithm="HS256")
    return token

def verify_token(token: str) -> int:
    """验证 JWT Token，返回用户ID"""
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Token invalid")

def hash_password(pwd: str) -> str:
    """密码 MD5 加密"""
    return hashlib.md5(pwd.encode()).hexdigest()

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取当前登录用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.replace("Bearer ", "").strip()
    user_id = verify_token(token)
    user = db.query(models.SysUser).filter(models.SysUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ========== 通用接口：系统认证 ==========

@app.post("/zyfh/api/v1/system/token/get")
def get_token(req: schemas.TokenRequest, db: Session = Depends(get_db)):
    """获取访问Token"""
    user = db.query(models.SysUser).filter(models.SysUser.user_account == req.user_account).first()
    if not user or user.user_pwd != hash_password(req.user_pwd):
        return error_response("2000", "用户账号或密码错误")
    
    token = generate_token(user.id)
    expire_time = int(time.time()) + 86400
    return success_response({
        "token": f"Bearer {token}",
        "expireTime": expire_time,
        "userInfo": {
            "userAccount": user.user_account,
            "userName": user.user_name,
            "deptName": user.dept_name
        }
    })

@app.get("/zyfh/api/v1/health")
def health_check():
    """健康检查"""
    return success_response({"status": "ok"}, "系统运行正常")

# ========== 二维码管理模块 ==========

@app.post("/zyfh/api/v1/qrcode/enterprise/save")
def save_enterprise(code: int, name: str, status: int = 1, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """新增/维护企业标志"""
    existing = db.query(models.Enterprise).filter(models.Enterprise.enterprise_code == code).first()
    if existing:
        existing.enterprise_name = name
        existing.status = status
        existing.update_by = current_user.user_account
        existing.update_time = datetime.utcnow()
    else:
        enterprise = models.Enterprise(
            enterprise_code=code,
            enterprise_name=name,
            status=status,
            create_by=current_user.user_account
        )
        db.add(enterprise)
    db.commit()
    return success_response({"enterprise_code": code})

@app.post("/zyfh/api/v1/qrcode/generate/single")
def generate_single_qrcode(req: schemas.QRGenerateRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """二维码单条生成"""
    # 1. 验证企业编码
    enterprise = db.query(models.Enterprise).filter(
        models.Enterprise.enterprise_code == req.enterprise_code,
        models.Enterprise.status == 1
    ).first()
    if not enterprise:
        return error_response("7000", "企业标志未维护或已禁用")
    
    # 2. 验证院内编码
    drug = db.query(models.DrugInfo).filter(
        models.DrugInfo.cj_id == req.cj_id,
        models.DrugInfo.status == 1
    ).first()
    if not drug:
        return error_response("1000", "院内编码无效，请核对")
    
    # 3. 数据校验（根据 guide.md 要求）
    # 规格：必须为"数字+g"格式，数字1-30（含）
    if not req.spec.endswith('g'):
        return error_response("1000", "规格格式错误，应为数字+g（如5g）")
    try:
        spec_num = float(req.spec.rstrip('g'))
        if not (1 <= spec_num <= 30):
            return error_response("1000", "规格数字范围错误，应为1-30（含）")
    except:
        return error_response("1000", "规格格式错误，应为数字+g（如5g）")
    
    # 批号：纯数字，长度5-10位（含）
    if not (5 <= len(req.batch_no) <= 10) or not req.batch_no.isdigit():
        return error_response("1000", "批号格式错误，应为5-10位纯数字")
    
    # 数量：默认7，支持手动修改（仅数字）
    if req.num <= 0:
        return error_response("1000", "数量必须大于0")
    
    # 重量：数字型，可保留1-4位小数，无单位（后台按kg存储）
    if req.weight <= 0 or req.weight > 100:
        return error_response("1000", "重量范围错误，应为0-100kg")
    
    # 4. 生成二维码内容
    qrcode_origin = f"{req.enterprise_code};{req.cj_id};{req.spec};{req.batch_no};{req.num};{req.weight}"
    
    # 5. 转换为 GB2312 再 Base64
    try:
        qrcode_bytes = qrcode_origin.encode("gb2312")
    except:
        qrcode_bytes = qrcode_origin.encode("utf-8")
    
    base64_str = base64.b64encode(qrcode_bytes).decode()
    qrcode_id = f"QR{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{int(time.time() % 1000)}"
    qrcode_url = f"http://localhost:8000/zyfh/qrcodes/{qrcode_id}.png"
    
    # 6. 保存到数据库
    qrcode = models.QRCodeGenerate(
        qrcode_id=qrcode_id,
        enterprise_code=req.enterprise_code,
        cj_id=req.cj_id,
        spec=req.spec,
        batch_no=req.batch_no,
        num=req.num,
        weight=req.weight,
        qrcode_origin=qrcode_origin,
        base64_str=base64_str,
        qrcode_url=qrcode_url,
        generate_by=current_user.user_account
    )
    db.add(qrcode)
    db.commit()
    
    return success_response({
        "qrcode_id": qrcode_id,
        "qrcode_content": qrcode_origin,
        "base64_str": base64_str,
        "qrcode_url": qrcode_url
    })

@app.post("/zyfh/api/v1/qrcode/generate/batch")
def generate_batch_qrcode(create_by: str, qrcode_list: List[schemas.QRGenerateRequest], db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """二维码批量生成"""
    success_count = 0
    fail_count = 0
    fail_list = []
    
    for idx, qr_req in enumerate(qrcode_list):
        try:
            # 验证企业编码
            enterprise = db.query(models.Enterprise).filter(models.Enterprise.enterprise_code == qr_req.enterprise_code).first()
            if not enterprise:
                fail_list.append({
                    "index": idx,
                    "params": qr_req.dict(),
                    "reason": "企业标志未维护"
                })
                fail_count += 1
                continue
            
            # 验证院内编码
            drug = db.query(models.DrugInfo).filter(models.DrugInfo.cj_id == qr_req.cj_id).first()
            if not drug:
                fail_list.append({
                    "index": idx,
                    "params": qr_req.dict(),
                    "reason": "院内编码无效，请核对"
                })
                fail_count += 1
                continue
            
            # 数据校验
            if not (1 <= float(qr_req.spec.rstrip('g')) <= 30):
                fail_list.append({
                    "index": idx,
                    "params": qr_req.dict(),
                    "reason": "规格格式错误，应为数字+g，数字范围1-30"
                })
                fail_count += 1
                continue
                
            if not (5 <= len(qr_req.batch_no) <= 10) or not qr_req.batch_no.isdigit():
                fail_list.append({
                    "index": idx,
                    "params": qr_req.dict(),
                    "reason": "批号格式错误，应为5-10位纯数字"
                })
                fail_count += 1
                continue
            
            # 生成二维码内容
            qrcode_origin = f"{qr_req.enterprise_code};{qr_req.cj_id};{qr_req.spec};{qr_req.batch_no};{qr_req.num};{qr_req.weight}"
            
            # 转换为 GB2312 再 Base64
            try:
                qrcode_bytes = qrcode_origin.encode("gb2312")
            except:
                qrcode_bytes = qrcode_origin.encode("utf-8")
            
            base64_str = base64.b64encode(qrcode_bytes).decode()
            qrcode_id = f"QR{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{int(time.time() % 1000)}{idx:03d}"
            qrcode_url = f"http://localhost:8000/zyfh/qrcodes/{qrcode_id}.png"
            
            # 保存到数据库
            qrcode = models.QRCodeGenerate(
                qrcode_id=qrcode_id,
                enterprise_code=qr_req.enterprise_code,
                cj_id=qr_req.cj_id,
                spec=qr_req.spec,
                batch_no=qr_req.batch_no,
                num=qr_req.num,
                weight=qr_req.weight,
                qrcode_origin=qrcode_origin,
                base64_str=base64_str,
                qrcode_url=qrcode_url,
                generate_by=create_by
            )
            db.add(qrcode)
            success_count += 1
            
        except Exception as e:
            fail_list.append({
                "index": idx,
                "params": qr_req.dict(),
                "reason": str(e)
            })
            fail_count += 1
    
    db.commit()
    
    return success_response({
        "successNum": success_count,
        "failNum": fail_count,
        "failList": fail_list,
        "downloadUrl": f"http://localhost:8000/zyfh/qrcodes/batch/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"
    })

@app.post("/zyfh/api/v1/qrcode/parse")
def parse_qrcode(payload: dict, db: Session = Depends(get_db)):
    """解析二维码"""
    base64_str = payload.get("qrcode_string")
    if not base64_str:
        return error_response("1000", "缺少二维码参数")
    
    try:
        qrcode_bytes = base64.b64decode(base64_str)
        # 尝试 GB2312 解码，失败回退 UTF-8
        try:
            raw = qrcode_bytes.decode("gb2312")
        except:
            raw = qrcode_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        return error_response("7000", f"二维码解析失败: {str(e)}")
    
    parts = raw.split(";")
    if len(parts) < 6:
        return error_response("7000", "二维码格式无效")
    
    try:
        result = {
            "enterprise_code": int(parts[0]),
            "cj_id": parts[1],
            "spec": parts[2],
            "batch_no": parts[3],
            "num": int(parts[4]),
            "weight": float(parts[5]),
            "raw": raw
        }
        return success_response(result)
    except Exception as e:
        return error_response("7000", f"二维码字段转换失败: {str(e)}")

@app.post("/zyfh/api/v1/qrcode/verify")
def verify_qrcode(payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """二维码校验"""
    base64_str = payload.get("qrcode_content")
    if not base64_str:
        return error_response("1000", "缺少二维码参数")
    
    # 解析二维码
    try:
        qrcode_bytes = base64.b64decode(base64_str)
        try:
            decrypt_content = qrcode_bytes.decode("gb2312")
        except:
            decrypt_content = qrcode_bytes.decode("utf-8")
    except:
        return error_response("7000", "二维码解析失败")
    
    # 查询原始记录
    original = db.query(models.QRCodeGenerate).filter(
        models.QRCodeGenerate.qrcode_origin == decrypt_content
    ).first()
    
    verify_result = "SUCCESS" if original else "FAIL"
    verify_reason = None if verify_result == "SUCCESS" else "二维码内容与原始记录不匹配"
    
    # 保存校验记录
    record = models.QRCodeVerify(
        qrcode_id=original.qrcode_id if original else "UNKNOWN",
        verify_base64=base64_str,
        decrypt_origin=decrypt_content,
        verify_result=verify_result,
        verify_reason=verify_reason,
        verify_by=current_user.user_account
    )
    db.add(record)
    db.commit()
    
    return success_response({
        "decryptContent": decrypt_content,
        "verifyResult": verify_result,
        "verifyReason": verify_reason
    })

@app.get("/zyfh/api/v1/qrcode/record/query")
def query_qrcode_records(enterprise_code: int = None, cj_id: str = None, 
                        batch_no: str = None, verify_result: str = None,
                        start_time: str = None, end_time: str = None,
                        page: int = 1, size: int = 20,
                        db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """二维码历史记录查询（分页）"""
    # 查询生成记录
    query_generate = db.query(models.QRCodeGenerate)
    if enterprise_code:
        query_generate = query_generate.filter(models.QRCodeGenerate.enterprise_code == enterprise_code)
    if cj_id:
        query_generate = query_generate.filter(models.QRCodeGenerate.cj_id == cj_id)
    if batch_no:
        query_generate = query_generate.filter(models.QRCodeGenerate.batch_no == batch_no)
    
    generate_records = query_generate.order_by(desc(models.QRCodeGenerate.generate_time)).offset((page - 1) * size).limit(size).all()
    
    # 查询校验记录
    query_verify = db.query(models.QRCodeVerify)
    if verify_result:
        query_verify = query_verify.filter(models.QRCodeVerify.verify_result == verify_result)
    if start_time and end_time:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        query_verify = query_verify.filter(models.QRCodeVerify.verify_time.between(start_dt, end_dt))
    
    verify_records = query_verify.order_by(desc(models.QRCodeVerify.verify_time)).offset((page - 1) * size).limit(size).all()
    
    # 合并结果
    records = []
    for rec in generate_records:
        records.append({
            "type": "generate",
            "qrcode_id": rec.qrcode_id,
            "enterprise_code": rec.enterprise_code,
            "cj_id": rec.cj_id,
            "batch_no": rec.batch_no,
            "generate_by": rec.generate_by,
            "generate_time": rec.generate_time.isoformat() if rec.generate_time else None
        })
    
    for rec in verify_records:
        records.append({
            "type": "verify",
            "qrcode_id": rec.qrcode_id,
            "verify_result": rec.verify_result,
            "verify_reason": rec.verify_reason,
            "verify_by": rec.verify_by,
            "verify_time": rec.verify_time.isoformat() if rec.verify_time else None
        })
    
    return success_response({
        "total": len(records),
        "pages": (len(records) + size - 1) // size,
        "page": page,
        "size": size,
        "list": records
    })

# ========== 扫码复核模块 ==========

@app.post("/zyfh/api/v1/check/his/sync")
def sync_his_prescription(req: schemas.HISPrescriptionSyncRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """HIS处方信息同步"""
    # Mock 实现，实际应调用医院 HIS 系统接口
    prescriptions_to_add = []
    
    if req.pres_no:
        # 单个处方同步
        existing = db.query(models.HISPrescription).filter(models.HISPrescription.pres_no == req.pres_no).first()
        if existing:
            return success_response({"count": 0, "data": []}, "处方已存在")
        
        # Mock 数据 - 实际应该从HIS系统获取
        pres = models.HISPrescription(
            pres_no=req.pres_no,
            patient_name="示例患者",
            patient_id="430102XXXXXXXXXXXX",
            dept_name="中医科",
            doc_name="李医生",
            pres_time=datetime.strptime("2026-02-28 09:00:00", "%Y-%m-%d %H:%M:%S") if req.start_time else datetime.utcnow(),
            drug_total=5,
            sync_time=datetime.utcnow(),
            pres_status=1  # 未复核
        )
        prescriptions_to_add.append(pres)
    elif req.start_time and req.end_time:
        # 时间范围内批量同步
        # Mock 实现 - 实际应从HIS系统获取指定时间段的处方
        for i in range(3):
            pres_no = f"CF{datetime.utcnow().strftime('%Y%m%d')}{i+1:03d}"
            existing = db.query(models.HISPrescription).filter(models.HISPrescription.pres_no == pres_no).first()
            if not existing:
                pres = models.HISPrescription(
                    pres_no=pres_no,
                    patient_name=f"示例患者{i+1}",
                    patient_id=f"430102XXXXXXXXXX{i+1:02d}",
                    dept_name="中医科",
                    doc_name="李医生",
                    pres_time=datetime.strptime(f"2026-02-28 09:0{i+1}:00", "%Y-%m-%d %H:%M:%S"),
                    drug_total=5,
                    sync_time=datetime.utcnow(),
                    pres_status=1  # 未复核
                )
                prescriptions_to_add.append(pres)
    else:
        return error_response("1000", "参数错误：必须提供处方号或开始时间和结束时间")
    
    # 批量插入处方
    for pres in prescriptions_to_add:
        db.add(pres)
    
    db.commit()
    return success_response({"count": len(prescriptions_to_add)}, "同步成功")

@app.post("/zyfh/api/v1/check/init")
def init_check(req: schemas.CheckInitRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """扫码复核初始化"""
    # 检查处方是否存在
    pres = db.query(models.HISPrescription).filter(models.HISPrescription.pres_no == req.pres_no).first()
    if not pres:
        return error_response("8000", "处方不存在")
    
    # 检查是否已在复核
    existing = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.pres_no == req.pres_no).first()
    if existing and existing.check_status in [1, 2]:
        return error_response("8000", "处方已在复核或已复核")
    
    # 初始化复核
    check_main = models.DrugCheckMain(
        pres_no=req.pres_no,
        check_by=req.check_by,
        check_station=req.check_station,
        check_status=1  # 复核中
    )
    db.add(check_main)
    
    # 更新处方状态
    pres.pres_status = 2  # 复核中
    
    db.commit()
    db.refresh(check_main)
    
    return success_response({
        "check_main_id": check_main.id,
        "pres_no": req.pres_no,
        "status": "initialized"
    })

@app.post("/zyfh/api/v1/check/scan")
def scan_check(req: schemas.ScanCheckRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """实时扫码复核"""
    # 1. 参数校验
    if not req.pres_no:
        return error_response("1000", "处方号不能为空")
    if not req.basket_no:
        return error_response("1000", "筐号不能为空")
    if not req.qrcode_content:
        return error_response("1000", "二维码内容不能为空")
    
    # 2. 检查网络连接状态
    is_online = check_network_connection()
    
    if not is_online:
        # 离线模式：保存到本地数据库
        save_offline_scan_record(req.pres_no, req.basket_no, req.qrcode_content, req.check_by)
        return success_response({
            "drug_name": "离线模式",
            "scan_result": "OFFLINE_SAVED",
            "cj_id": "OFFLINE",
            "spec": "OFFLINE",
            "message": "网络离线，数据已保存至本地，网络恢复后自动同步"
        })
    
    # 3. 在线模式：正常处理
    # 获取复核主表
    check_main = db.query(models.DrugCheckMain).filter(
        models.DrugCheckMain.pres_no == req.pres_no
    ).first()
    if not check_main:
        return error_response("8000", "尚未初始化复核")
    
    # 检查复核状态
    if check_main.check_status == 2:
        return error_response("8000", "该处方已复核完成，不可再扫码")
    
    # 4. 解析二维码
    try:
        qrcode_bytes = base64.b64decode(req.qrcode_content)
        try:
            raw = qrcode_bytes.decode("gb2312")
        except:
            raw = qrcode_bytes.decode("utf-8")
    except Exception as e:
        return error_response("7000", f"二维码解析失败: {str(e)}")
    
    parts = raw.split(";")
    if len(parts) < 6:
        return error_response("7000", "二维码格式无效")
    
    try:
        scan_cj_id = parts[1]
        scan_spec = parts[2]
        batch_no = parts[3]
        num = int(parts[4])
        weight = float(parts[5])
    except Exception as e:
        return error_response("7000", f"二维码字段解析失败: {str(e)}")
    
    # 5. 获取药品信息
    drug = db.query(models.DrugInfo).filter(models.DrugInfo.cj_id == scan_cj_id).first()
    drug_name = drug.drug_name if drug else f"未知药品({scan_cj_id})"
    
    # 6. 保存扫码记录
    detail = models.DrugCheckDetail(
        check_main_id=check_main.id,
        pres_no=req.pres_no,
        cj_id=scan_cj_id,
        drug_name=drug_name,
        spec=scan_spec,
        pres_num=2,  # 应该从处方中获取
        qrcode_id=f"QR{int(time.time())}",
        scan_spec=scan_spec,
        scan_num=num,
        basket_no=req.basket_no,
        scan_result=1,  # 匹配
        is_check=1
    )
    db.add(detail)
    
    # 7. 记录操作日志
    log_entry = models.CheckOperateRecord(
        pres_no=req.pres_no,
        check_main_id=check_main.id,
        operate_user=req.check_by,
        operate_module="扫码复核",
        operate_type="扫码",
        operate_desc=f"对处方{req.pres_no}进行扫码复核，扫码药品{drug_name}",
        operate_time=datetime.utcnow(),
        operate_ip="127.0.0.1"  # 实际应该从请求中获取
    )
    db.add(log_entry)
    
    db.commit()
    
    return success_response({
        "drug_name": drug_name,
        "scan_result": "SUCCESS",
        "cj_id": scan_cj_id,
        "spec": scan_spec,
        "batch_no": batch_no,
        "num": num,
        "weight": weight,
        "basket_no": req.basket_no,
        "scan_time": datetime.utcnow().isoformat()
    })

@app.post("/zyfh/api/v1/check/progress/save")
def save_check_progress(req: schemas.CheckProgressSaveRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """复核进度保存"""
    # 检查网络连接状态
    is_online = check_network_connection()
    
    if not is_online:
        # 离线模式：保存到本地数据库
        progress_info = {
            "finished_drugs": req.finished_drugs,
            "unfinished_drugs": req.unfinished_drugs,
            "current_basket": req.current_basket
        }
        save_offline_progress_record(req.pres_no, req.check_by, progress_info)
        return success_response({
            "progress_saved": True,
            "message": "网络离线，进度已保存至本地，网络恢复后自动同步"
        })
    
    # 在线模式：正常处理
    check_main = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.pres_no == req.pres_no).first()
    if not check_main:
        return error_response("8000", "复核记录不存在")
    
    progress_json = json.dumps({
        "finished": req.finished_drugs,
        "unfinished": req.unfinished_drugs
    })
    
    existing = db.query(models.DrugCheckProgress).filter(models.DrugCheckProgress.check_main_id == check_main.id).first()
    if existing:
        existing.finished_drug = len(req.finished_drugs)
        existing.unfinish_drug = len(req.unfinished_drugs)
        existing.current_basket = req.current_basket
        existing.progress_json = progress_json
        existing.save_time = datetime.utcnow()
    else:
        progress = models.DrugCheckProgress(
            check_main_id=check_main.id,
            pres_no=req.pres_no,
            finished_drug=len(req.finished_drugs),
            unfinish_drug=len(req.unfinished_drugs),
            current_basket=req.current_basket,
            progress_json=progress_json,
            save_by=req.check_by
        )
        db.add(progress)
    
    db.commit()
    return success_response({"progress_saved": True})

@app.post("/zyfh/api/v1/check/submit")
def submit_check(req: schemas.CheckSubmitRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """复核完成提交"""
    # 检查网络连接状态
    is_online = check_network_connection()
    
    if not is_online:
        # 离线模式：保存到本地数据库
        save_offline_submit_record(req.pres_no, req.check_by)
        return success_response({
            "pres_no": req.pres_no,
            "status": "OFFLINE_SAVED",
            "qualified": True,
            "message": "网络离线，提交已保存至本地，网络恢复后自动同步"
        })
    
    # 在线模式：正常处理
    check_main = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.pres_no == req.pres_no).first()
    if not check_main:
        return error_response("8000", "复核记录不存在")
    
    # 更新复核状态
    check_main.check_status = 2  # 已完成
    check_main.check_end_time = datetime.utcnow()
    check_main.check_qualified = 1  # 假设合格
    check_main.submit_by = req.check_by
    check_main.submit_time = datetime.utcnow()
    
    # 更新处方状态
    pres = db.query(models.HISPrescription).filter(models.HISPrescription.pres_no == req.pres_no).first()
    if pres:
        pres.pres_status = 3  # 已复核
    
    db.commit()
    
    return success_response({
        "pres_no": req.pres_no,
        "status": "submitted",
        "qualified": True
    })

@app.get("/zyfh/api/v1/system/status")
def get_system_status(db: Session = Depends(get_db)):
    """获取系统整体状态"""
    total_users = db.query(func.count(models.SysUser.id)).scalar() or 0
    total_devices = db.query(func.count(models.SysDeviceManage.id)).scalar() or 0
    online_devices = db.query(func.count(models.SysDeviceManage.id)).filter(
        models.SysDeviceManage.device_status == 'ONLINE'
    ).scalar() or 0
    
    return success_response({
        "total_users": total_users,
        "total_devices": total_devices,
        "online_devices": online_devices,
        "system_status": "running"
    })

# ========== 错误提醒模块 ==========

@app.post("/zyfh/api/v1/alert/error/save")
def save_error_record(req: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """保存错误提醒记录"""
    error_record = models.CheckErrorRecord(
        pres_no=req.get("pres_no"),
        error_type=req.get("error_type"),  # DRUG_NOT_MATCH, SPEC_ERROR, WEIGHT_ERROR 等
        error_desc=req.get("error_desc"),
        error_level=req.get("error_level", 1),  # 1=普通, 2=警告, 3=严重
        drug_name=req.get("drug_name"),
        pres_spec=req.get("pres_spec"),
        scan_spec=req.get("scan_spec"),
        pres_num=req.get("pres_num"),
        scan_num=req.get("scan_num"),
        error_by=current_user.user_account,
        error_status=0  # 待处理
    )
    db.add(error_record)
    db.commit()
    db.refresh(error_record)
    
    return success_response({"error_id": error_record.id, "status": "saved"})

@app.put("/zyfh/api/v1/alert/error/handle")
def handle_error_record(req: schemas.ErrorHandleRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """处理（解决）错误提醒"""
    error_record = db.query(models.CheckErrorRecord).filter(models.CheckErrorRecord.id == int(req.error_id)).first()
    if not error_record:
        return error_response("8000", "错误记录不存在")
    
    # 保存错误处理记录
    error_handle = models.CheckErrorHandle(
        error_id=int(req.error_id),
        check_detail_id=error_record.check_detail_id,
        pres_no=error_record.pres_no,
        handle_type=req.handle_result,  # REPLACE-错抓更换, ADD-少包补加, CANCEL-误扫取消
        handle_desc=req.handle_desc or "",
        handle_by=req.handle_by
    )
    db.add(error_handle)
    
    # 更新错误记录状态
    error_record.error_status = 2  # 已处理
    
    db.commit()
    
    return success_response({"error_id": req.error_id, "handle_result": "success"})

@app.get("/zyfh/api/v1/alert/error/list")
def list_error_records(pres_no: str = None, error_status: int = None, 
                      db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询错误提醒列表"""
    query = db.query(models.CheckErrorRecord)
    
    if pres_no:
        query = query.filter(models.CheckErrorRecord.pres_no == pres_no)
    if error_status is not None:
        query = query.filter(models.CheckErrorRecord.error_status == error_status)
    
    records = query.order_by(desc(models.CheckErrorRecord.create_time)).limit(100).all()
    
    return success_response({
        "total": len(records),
        "records": [
            {
                "error_id": r.id,
                "pres_no": r.pres_no,
                "error_type": r.error_type,
                "error_desc": r.error_desc,
                "error_level": r.error_level,
                "error_status": r.error_status,
                "handle_type": r.handle_type,
                "error_by": r.error_by,
                "handle_by": r.handle_by
            } for r in records
        ]
    })

# ========== 分筐管理模块 ==========

@app.post("/zyfh/api/v1/basket/save")
def save_basket(req: schemas.BasketCreateRequest, db: Session = Depends(get_db), 
               current_user=Depends(get_current_user)):
    """新增/维护分筐"""
    existing = db.query(models.BasketManage).filter(models.BasketManage.basket_no == req.basket_no).first()
    if existing:
        existing.basket_name = req.basket_name
        existing.status = req.status if hasattr(req, 'status') else 1
        existing.update_by = req.create_by
        existing.update_time = datetime.utcnow()
    else:
        basket = models.BasketManage(
            basket_no=req.basket_no,
            basket_name=req.basket_name,
            status=req.status if hasattr(req, 'status') else 1,
            create_by=req.create_by
        )
        db.add(basket)
    
    db.commit()
    return success_response({"basket_no": req.basket_no, "status": "saved"})

@app.post("/zyfh/api/v1/basket/relation/save")
def save_basket_relation(req: schemas.BasketDrugRelationRequest, 
                        db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """分筐关联（处方 -> 分筐 -> 药品）"""
    # 检查分筐是否存在
    basket = db.query(models.BasketManage).filter(models.BasketManage.basket_no == req.basket_no).first()
    if not basket:
        return error_response("8000", "分筐不存在")
    
    # 清除已有关系（如果需要更新的话）
    existing_relations = db.query(models.PresBasketRelation).filter(
        models.PresBasketRelation.pres_no == req.pres_no,
        models.PresBasketRelation.basket_no == req.basket_no
    ).all()
    
    for rel in existing_relations:
        rel.is_delete = 1  # 逻辑删除旧关联
    
    # 添加新的关联关系
    for cj_id in req.cj_id_list:
        # 获取药品信息
        drug_info = db.query(models.DrugInfo).filter(models.DrugInfo.cj_id == cj_id).first()
        drug_name = drug_info.drug_name if drug_info else f"未知药品({cj_id})"
        
        relation = models.PresBasketRelation(
            pres_no=req.pres_no,
            basket_no=req.basket_no,
            cj_id=cj_id,
            drug_name=drug_name,
            basket_drug_num=1,  # 默认数量为1，实际应从处方中获取
            create_by=req.create_by
        )
        db.add(relation)
    
    db.commit()
    return success_response({"basket_no": req.basket_no, "drug_count": len(req.cj_id_list), "status": "saved"})

@app.post("/zyfh/api/v1/basket/check/confirm")
def confirm_basket_check(req: schemas.BasketCheckConfirmRequest, 
                        db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """分筐复核确认"""
    # 更新分筐关联表中的状态
    relations = db.query(models.PresBasketRelation).filter(
        models.PresBasketRelation.basket_no == req.basket_no
    ).all()
    
    if not relations:
        return error_response("8000", "未找到对应的分筐关联记录")
    
    # 更新所有关联记录的状态
    for relation in relations:
        relation.basket_status = 3  # 3-已完成
    
    db.commit()
    return success_response({
        "basket_no": req.basket_no, 
        "confirm_by": req.confirm_by, 
        "status": "confirmed"
    })

@app.get("/zyfh/api/v1/basket/list")
def list_baskets(status: int = None, pres_no: str = None, 
                db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询分筐列表"""
    query = db.query(models.BasketManage)
    
    if status is not None:
        query = query.filter(models.BasketManage.status == status)
    
    baskets = query.order_by(desc(models.BasketManage.create_time)).limit(50).all()
    
    return success_response({
        "total": len(baskets),
        "baskets": [
            {
                "basket_no": b.basket_no,
                "status": b.status,
                "create_by": b.create_by,
                "create_time": b.create_time.timestamp() if b.create_time else None
            } for b in baskets
        ]
    })

# ========== 溯源管理模块 ==========

@app.get("/zyfh/api/v1/trace/record/query")
def query_trace_records(req: schemas.TraceRecordQueryRequest = Depends(), 
                       db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询操作记录（溯源）"""
    query = db.query(models.CheckOperateRecord)
    
    if req.pres_no:
        query = query.filter(models.CheckOperateRecord.pres_no == req.pres_no)
    if req.cj_id:
        query = query.filter(models.CheckOperateRecord.cj_id == req.cj_id)
    if req.check_by:
        query = query.filter(models.CheckOperateRecord.operate_user == req.check_by)
    if req.start_time and req.end_time:
        start_dt = datetime.strptime(req.start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(req.end_time, "%Y-%m-%d %H:%M:%S")
        query = query.filter(models.CheckOperateRecord.operate_time.between(start_dt, end_dt))
    
    # 分页处理
    total = query.count()
    records = query.offset((req.page - 1) * req.size).limit(req.size).all()
    
    return success_response({
        "total": total,
        "pages": (total + req.size - 1) // req.size,
        "page": req.page,
        "size": req.size,
        "list": [
            {
                "operate_id": r.id,
                "pres_no": r.pres_no,
                "cj_id": r.cj_id,
                "operate_type": r.operate_type,
                "operate_content": r.operate_content,
                "operate_by": r.operate_user,
                "operate_time": r.operate_time.isoformat() if r.operate_time else None,
                "ip_address": r.operate_ip
            } for r in records
        ]
    })

@app.get("/zyfh/api/v1/trace/video/query")
def query_video_link(pres_no: str, scan_time: str, check_station: str, 
                    db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询关联视频（基于时间戳精准匹配）"""
    # 将时间字符串转换为datetime对象
    scan_datetime = datetime.strptime(scan_time, "%Y-%m-%d %H:%M:%S")
    
    # 查询视频监控联动记录，时间匹配精度为±1秒
    query = db.query(models.VideoMonitorLink).filter(
        models.VideoMonitorLink.pres_no == pres_no,
        models.VideoMonitorLink.check_station == check_station,
        models.VideoMonitorLink.scan_time.between(
            scan_datetime - timedelta(seconds=1), 
            scan_datetime + timedelta(seconds=1)
        )
    )
    
    links = query.all()
    
    return success_response({
        "total": len(links),
        "videos": [
            {
                "video_id": l.id,
                "pres_no": l.pres_no,
                "video_url": l.video_url,
                "video_download": l.video_download,
                "video_snapshot": l.video_snapshot,
                "scan_time": l.scan_time.isoformat() if l.scan_time else None,
                "check_station": l.check_station,
                "camera_no": l.camera_no
            } for l in links
        ]
    })

@app.post("/zyfh/api/v1/trace/report/generate")
def generate_trace_report(pres_no: str, db: Session = Depends(get_db), 
                         current_user=Depends(get_current_user)):
    """生成溯源报告"""
    # 查询该处方的所有操作记录
    records = db.query(models.CheckOperateRecord).filter(
        models.CheckOperateRecord.pres_no == pres_no
    ).order_by(models.CheckOperateRecord.operate_time).all()
    
    # 生成报告内容
    report_content = {
        "report_id": f"RPT{int(time.time())}",
        "pres_no": pres_no,
        "total_operations": len(records),
        "operations": [
            {
                "time": r.operate_time.isoformat() if r.operate_time else None,
                "type": r.operate_type,
                "user": r.operate_by,
                "content": r.operate_content
            } for r in records
        ],
        "generated_by": current_user.user_account,
        "generated_time": datetime.utcnow().isoformat()
    }
    
    return success_response({
        "report_id": f"RPT{int(time.time())}",
        "pres_no": pres_no,
        "operation_count": len(records),
        "status": "generated"
    })

# ========== 工作量统计模块 ==========

@app.get("/zyfh/api/v1/stat/workload/query")
def query_workload_stat(req: schemas.WorkloadStatQueryRequest = Depends(),
                       db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询工作量统计"""
    # 根据统计类型构建查询
    query_obj = db.query(models.CheckWorkloadStat)
    
    # 根据统计类型过滤
    if req.stat_type == "USER":
        if req.check_by:
            query_obj = query_obj.filter(models.CheckWorkloadStat.check_by == req.check_by)
    elif req.stat_type == "TIME":
        if req.time_type and req.stat_time:
            query_obj = query_obj.filter(
                models.CheckWorkloadStat.stat_time_type == req.time_type,
                models.CheckWorkloadStat.stat_time.like(f"{req.stat_time}%")
            )
    elif req.stat_type == "PRES":
        # 按处方维度的统计可能需要另外实现
        pass
    
    # 分页处理
    total = query_obj.count()
    stats = query_obj.offset((req.page - 1) * req.size).limit(req.size).all()
    
    return success_response({
        "total": total,
        "pages": (total + req.size - 1) // req.size,
        "page": req.page,
        "size": req.size,
        "list": [
            {
                "id": s.id,
                "check_by": s.check_by,
                "stat_time_type": s.stat_time_type,
                "stat_time": s.stat_time,
                "pres_total": s.pres_total,
                "drug_total": s.drug_total,
                "qrcode_total": s.qrcode_total,
                "qualified_pres": s.qualified_pres,
                "error_total": s.error_total,
                "handle_error": s.handle_error,
                "check_hours": float(s.check_hours) if s.check_hours else 0.0,
                "update_time": s.update_time.isoformat() if s.update_time else None
            } for s in stats
        ]
    })

@app.post("/zyfh/api/v1/stat/report/generate")
def generate_stat_report(start_date: str, end_date: str, report_type: str = "detailed",
                        db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """生成统计报告（含图表数据）"""
    stats = db.query(models.CheckWorkloadStat).order_by(
        models.CheckWorkloadStat.stat_date
    ).limit(30).all()
    
    total_pres = sum([s.pres_total for s in stats])
    total_drugs = sum([s.drug_total for s in stats])
    total_qualified = sum([s.qualified_total for s in stats])
    total_errors = sum([s.error_total for s in stats])
    qualified_rate = (total_qualified / total_drugs * 100) if total_drugs > 0 else 0
    
    return success_response({
        "report_id": f"STAT{int(time.time())}",
        "period": f"{start_date} - {end_date}",
        "total_prescriptions": total_pres,
        "total_drugs": total_drugs,
        "total_qualified": total_qualified,
        "total_errors": total_errors,
        "qualified_rate": round(qualified_rate, 2),
        "status": "generated"
    })

# ========== 系统管理模块 ==========

@app.post("/zyfh/api/v1/sys/user/save")
def save_user(req: schemas.UserCreateRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """新增/编辑用户"""
    existing = db.query(models.SysUser).filter(models.SysUser.user_account == req.user_account).first()
    if existing:
        # 编辑现有用户
        existing.user_name = req.user_name
        existing.dept_name = req.dept_name
        existing.post = req.post
        existing.phone = req.phone
        existing.status = req.status
        existing.update_by = current_user.user_account
        existing.update_time = datetime.utcnow()
        if req.user_pwd:  # 如果提供了新密码，则更新
            existing.user_pwd = hash_password(req.user_pwd)
    else:
        # 新增用户
        user = models.SysUser(
            user_account=req.user_account,
            user_name=req.user_name,
            user_pwd=hash_password(req.user_pwd),
            dept_name=req.dept_name,
            post=req.post,
            phone=req.phone,
            status=req.status,
            create_by=current_user.user_account
        )
        db.add(user)
    
    db.commit()
    return success_response({"user_account": req.user_account, "status": "saved"})

@app.get("/zyfh/api/v1/sys/user/list")
def list_users(user_account: str = None, user_name: str = None, dept_name: str = None, 
                status: int = None, page: int = 1, size: int = 20,
                db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询用户列表（分页）"""
    query = db.query(models.SysUser)
    
    if user_account:
        query = query.filter(models.SysUser.user_account.like(f"%{user_account}%"))
    if user_name:
        query = query.filter(models.SysUser.user_name.like(f"%{user_name}%"))
    if dept_name:
        query = query.filter(models.SysUser.dept_name == dept_name)
    if status is not None:
        query = query.filter(models.SysUser.status == status)
    
    total = query.count()
    users = query.order_by(desc(models.SysUser.create_time)).offset((page - 1) * size).limit(size).all()
    
    return success_response({
        "total": total,
        "pages": (total + size - 1) // size,
        "page": page,
        "size": size,
        "list": [
            {
                "id": u.id,
                "user_account": u.user_account,
                "user_name": u.user_name,
                "dept_name": u.dept_name,
                "post": u.post,
                "phone": u.phone,
                "status": u.status,
                "create_time": u.create_time.timestamp() if u.create_time else None
            } for u in users
        ]
    })

@app.delete("/zyfh/api/v1/sys/user/delete")
def delete_user(id: int, operate_by: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """系统用户删除（逻辑删除）"""
    user = db.query(models.SysUser).filter(models.SysUser.id == id).first()
    if not user:
        return error_response("5000", "用户不存在")
    
    user.is_delete = 1
    user.update_by = operate_by
    user.update_time = datetime.utcnow()
    
    # 逻辑删除该用户的角色关联
    user_roles = db.query(models.SysUserRole).filter(models.SysUserRole.user_id == id).all()
    for ur in user_roles:
        ur.is_delete = 1
    
    db.commit()
    return success_response({"user_id": id, "status": "deleted"})

@app.post("/zyfh/api/v1/sys/role/save")
def save_role(req: schemas.RoleCreateRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """新增/编辑角色"""
    existing = db.query(models.SysRole).filter(models.SysRole.role_code == req.role_code).first()
    if existing:
        existing.role_name = req.role_name
        existing.role_permission = req.role_permission
        existing.role_desc = req.role_desc
        existing.status = req.status
        existing.update_by = current_user.user_account
        existing.update_time = datetime.utcnow()
    else:
        role = models.SysRole(
            role_code=req.role_code,
            role_name=req.role_name,
            role_permission=req.role_permission,
            role_desc=req.role_desc,
            status=req.status,
            create_by=current_user.user_account
        )
        db.add(role)
    
    db.commit()
    return success_response({"role_code": req.role_code, "status": "saved"})

@app.get("/zyfh/api/v1/sys/role/list")
def list_roles(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询角色列表"""
    roles = db.query(models.SysRole).order_by(desc(models.SysRole.create_time)).limit(100).all()
    
    return success_response({
        "total": len(roles),
        "list": [
            {
                "id": r.id,
                "role_code": r.role_code,
                "role_name": r.role_name,
                "role_permission": r.role_permission,
                "role_desc": r.role_desc,
                "status": r.status,
                "create_time": r.create_time.timestamp() if r.create_time else None
            } for r in roles
        ]
    })

@app.post("/zyfh/api/v1/sys/user_role/bind")
def bind_user_role(req: schemas.UserRoleBindRequest, db: Session = Depends(get_db),
                  current_user=Depends(get_current_user)):
    """绑定用户角色"""
    # 先清除用户现有的角色绑定
    existing_bindings = db.query(models.SysUserRole).filter(
        models.SysUserRole.user_id == req.user_id
    ).all()
    
    for binding in existing_bindings:
        binding.is_delete = 1  # 逻辑删除现有绑定
    
    # 添加新的角色绑定
    for role_id in req.role_id_list:
        user_role = models.SysUserRole(
            user_id=req.user_id,
            role_id=role_id,
            create_by=req.operate_by
        )
        db.add(user_role)
    
    db.commit()
    return success_response({
        "user_id": req.user_id, 
        "role_id_list": req.role_id_list, 
        "status": "bound"
    })

@app.post("/zyfh/api/v1/sys/device/save")
def save_device(req: schemas.DeviceRegisterRequest, db: Session = Depends(get_db),
               current_user=Depends(get_current_user)):
    """注册/更新设备"""
    existing = db.query(models.SysDeviceManage).filter(models.SysDeviceManage.device_no == req.device_no).first()
    if existing:
        existing.device_name = req.device_name
        existing.device_type = req.device_type
        existing.bind_station = req.bind_station
        existing.bind_user = req.bind_user
        existing.update_by = current_user.user_account
        existing.update_time = datetime.utcnow()
    else:
        device = models.SysDeviceManage(
            device_no=req.device_no,
            device_name=req.device_name,
            device_type=req.device_type,  # SCAN-扫码枪, PAD-平板, PRINT-打印机, CAM-摄像头
            bind_station=req.bind_station,
            bind_user=req.bind_user,
            device_status="ONLINE",
            create_by=current_user.user_account
        )
        db.add(device)
    
    db.commit()
    return success_response({"device_no": req.device_no, "status": "saved"})

@app.post("/zyfh/api/v1/sys/base/drug/sync/his")
def sync_his_drug_base(sync_type: str, operate_by: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """院内药品基础数据同步（从HIS）"""
    # Mock 实现，实际应调用HIS系统接口
    success_count = 0
    fail_count = 0
    
    if sync_type == "ALL":
        # 全量同步：清空本地数据，重新同步
        # 在实际应用中，这里会调用HIS系统的接口获取药品数据
        
        # Mock 数据
        mock_drugs = [
            {"cj_id": "13310", "drug_name": "盐巴戟天", "drug_type": "补益药", "spec_range": "5g,10g"},
            {"cj_id": "13311", "drug_name": "熟地黄", "drug_type": "补益药", "spec_range": "10g,15g"},
            {"cj_id": "13312", "drug_name": "山茱萸", "drug_type": "补益药", "spec_range": "5g,10g"},
            {"cj_id": "13313", "drug_name": "山药", "drug_type": "补益药", "spec_range": "10g,15g"},
            {"cj_id": "13314", "drug_name": "茯苓", "drug_type": "利水渗湿药", "spec_range": "10g,15g"}
        ]
        
        for drug_data in mock_drugs:
            existing = db.query(models.DrugInfo).filter(models.DrugInfo.cj_id == drug_data["cj_id"]).first()
            if existing:
                # 更新现有记录
                existing.drug_name = drug_data["drug_name"]
                existing.drug_type = drug_data["drug_type"]
                existing.spec_range = drug_data["spec_range"]
                existing.his_sync_time = datetime.utcnow()
            else:
                # 插入新记录
                drug = models.DrugInfo(
                    cj_id=drug_data["cj_id"],
                    drug_name=drug_data["drug_name"],
                    drug_type=drug_data["drug_type"],
                    spec_range=drug_data["spec_range"],
                    his_sync_time=datetime.utcnow(),
                    status=1
                )
                db.add(drug)
            success_count += 1
    
    elif sync_type == "UPDATE":
        # 增量更新：仅同步HIS中新增/修改的药品数据
        # 在实际应用中，这里会调用HIS系统的接口获取增量数据
        success_count = 0  # Mock 没有增量数据
    else:
        return error_response("1000", "同步类型错误，应为ALL或UPDATE")
    
    db.commit()
    
    return success_response({
        "syncType": sync_type,
        "successCount": success_count,
        "failCount": fail_count,
        "syncTime": datetime.utcnow().isoformat()
    })

@app.get("/zyfh/api/v1/sys/device/list")
def list_devices(device_status: str = None, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    """查询设备列表"""
    query = db.query(models.SysDeviceManage)
    
    if device_status:
        query = query.filter(models.SysDeviceManage.device_status == device_status)
    
    devices = query.order_by(desc(models.SysDeviceManage.create_time)).limit(100).all()
    
    return success_response({
        "total": len(devices),
        "devices": [
            {
                "device_id": d.id,
                "device_code": d.device_code,
                "device_name": d.device_name,
                "device_type": d.device_type,
                "ip_address": d.ip_address,
                "device_status": d.device_status,
                "create_time": d.create_time.timestamp() if d.create_time else None
            } for d in devices
        ]
    })

@app.get("/zyfh/api/v1/sys/log/query")
def query_system_logs(log_type: str = None, user_account: str = None, 
                     db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询系统操作日志"""
    query = db.query(models.CheckOperateRecord)
    
    if log_type:
        query = query.filter(models.CheckOperateRecord.operate_type == log_type)
    if user_account:
        query = query.filter(models.CheckOperateRecord.operate_user == user_account)
    
    logs = query.order_by(desc(models.CheckOperateRecord.operate_time)).limit(200).all()
    
    return success_response({
        "total": len(logs),
        "logs": [
            {
                "log_id": l.id,
                "operate_type": l.operate_type,
                "operate_by": l.operate_user,
                "operate_time": l.operate_time.timestamp() if l.operate_time else None,
                "ip_address": l.operate_ip,
                "operate_content": l.operate_content
            } for l in logs
        ]
    })

# 添加系统参数配置接口
from pydantic import BaseModel

class ParamConfigRequest(BaseModel):
    param_key: str
    param_value: str
    param_desc: str
    operate_by: str

@app.post("/zyfh/api/v1/sys/param/config/save")
def save_param_config(req: ParamConfigRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """系统参数配置"""
    # 这里我们使用一个简单的字典来模拟参数配置表
    # 在实际应用中，应该有一个专门的参数配置表
    import json
    config_key = f"sys_param_{req.param_key}"
    
    # 保存参数到系统配置中
    # 这里我们简单地记录操作日志
    log_entry = models.CheckOperateRecord(
        operate_user=current_user.user_account,
        operate_module="系统管理",
        operate_type="PARAM_CONFIG_SAVE",
        operate_desc=f"配置参数 {req.param_key} = {req.param_value}",
        operate_time=datetime.utcnow(),
        operate_ip="127.0.0.1"
    )
    db.add(log_entry)
    db.commit()
    
    return success_response({
        "param_key": req.param_key,
        "param_value": req.param_value,
        "status": "saved"
    })

@app.get("/zyfh/api/v1/sys/param/config/query")
def query_param_config(param_key: str = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """系统参数查询"""
    # 在实际应用中，这应该查询参数配置表
    # 这里我们返回一些预设的参数
    predefined_params = {
        "offline_cache_time": {"value": "72", "desc": "离线缓存时长（小时）"},
        "auto_save_progress": {"value": "30", "desc": "自动保存进度时间（分钟）"},
        "qrcode_dpi": {"value": "300", "desc": "二维码生成分辨率（dpi）"},
        "token_expire_hour": {"value": "24", "desc": "Token有效期（小时）"},
        "video_valid_hour": {"value": "24", "desc": "视频地址有效时长（小时）"}
    }
    
    if param_key:
        if param_key in predefined_params:
            result = [{"param_key": param_key, "param_value": predefined_params[param_key]["value"], "param_desc": predefined_params[param_key]["desc"]}]
        else:
            result = []
    else:
        result = [{"param_key": k, "param_value": v["value"], "param_desc": v["desc"]} for k, v in predefined_params.items()]
    
    return success_response({
        "total": len(result),
        "list": result
    })

# 添加数据备份接口
class DataBackupRequest(BaseModel):
    backup_type: str  # FULL-全量备份，INCREMENT-增量备份
    backup_desc: str = None
    operate_by: str

@app.post("/zyfh/api/v1/sys/data/backup/trigger")
def trigger_data_backup(req: DataBackupRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """数据备份手动触发"""
    import uuid
    backup_id = f"BACK{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8].upper()}"
    
    # 这里应该实际执行备份逻辑
    # 模拟备份过程
    backup_info = {
        "backupId": backup_id,
        "backupPath": f"/data/backup/{datetime.utcnow().strftime('%Y/%m/%d')}/{req.backup_type.lower()}/",
        "backupTime": datetime.utcnow().isoformat(),
        "backupStatus": "SUCCESS",  # RUNNING, SUCCESS, FAIL
        "backupType": req.backup_type,
        "backupDesc": req.backup_desc
    }
    
    # 记录备份操作日志
    log_entry = models.CheckOperateRecord(
        operate_user=current_user.user_account,
        operate_module="系统管理",
        operate_type="DATA_BACKUP",
        operate_desc=f"执行{req.backup_type}备份，ID: {backup_id}",
        operate_time=datetime.utcnow(),
        operate_ip="127.0.0.1"
    )
    db.add(log_entry)
    db.commit()
    
    return success_response(backup_info)

@app.get("/zyfh/api/v1/sys/data/backup/record/query")
def query_backup_records(backup_type: str = None, backup_status: str = None, 
                       start_time: str = None, end_time: str = None,
                       db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """数据备份记录查询"""
    # 模拟备份记录
    mock_backups = [
        {
            "backupId": "BACK20260228120001A1B2C3D4",
            "backupType": "FULL",
            "backupPath": "/data/backup/2026/02/28/full/",
            "backupStatus": "SUCCESS",
            "triggerBy": "admin",
            "backupTime": "2026-02-28T12:00:01",
            "backupSize": "2.5GB"
        },
        {
            "backupId": "BACK20260228130002E5F6G7H8",
            "backupType": "INCREMENT",
            "backupPath": "/data/backup/2026/02/28/increment/",
            "backupStatus": "SUCCESS",
            "triggerBy": "admin",
            "backupTime": "2026-02-28T13:00:02",
            "backupSize": "150MB"
        }
    ]
    
    # 根据查询条件过滤
    filtered_backups = mock_backups
    if backup_type:
        filtered_backups = [b for b in filtered_backups if b["backupType"] == backup_type]
    if backup_status:
        filtered_backups = [b for b in filtered_backups if b["backupStatus"] == backup_status]
    
    return success_response({
        "total": len(filtered_backups),
        "pages": 1,
        "page": 1,
        "size": len(filtered_backups),
        "list": filtered_backups
    })

# 离线数据同步接口
@app.post("/zyfh/api/v1/system/offline/sync")
def sync_offline_data(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """同步离线数据到服务器"""
    synced_count = 0
    failed_count = 0
    results = []
    
    # 同步离线扫码记录
    offline_scans = get_offline_records('local_scan_records')
    for record in offline_scans:
        try:
            # 获取复核主表
            check_main = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.pres_no == record[1]).first()
            if not check_main:
                # 如果处方未初始化，跳过同步
                results.append({
                    "type": "scan",
                    "id": record[0],
                    "status": "FAILED",
                    "reason": "复核未初始化"
                })
                failed_count += 1
                continue
            
            # 解析二维码
            try:
                qrcode_bytes = base64.b64decode(record[3])  # qrcode_content
                try:
                    raw = qrcode_bytes.decode("gb2312")
                except:
                    raw = qrcode_bytes.decode("utf-8")
            except:
                results.append({
                    "type": "scan",
                    "id": record[0],
                    "status": "FAILED",
                    "reason": "二维码解析失败"
                })
                failed_count += 1
                continue
            
            parts = raw.split(";")
            if len(parts) < 6:
                results.append({
                    "type": "scan",
                    "id": record[0],
                    "status": "FAILED",
                    "reason": "二维码格式无效"
                })
                failed_count += 1
                continue
            
            scan_cj_id = parts[1]
            scan_spec = parts[2]
            
            # 保存扫码记录到主数据库
            detail = models.DrugCheckDetail(
                check_main_id=check_main.id,
                pres_no=record[1],  # pres_no
                cj_id=scan_cj_id,
                drug_name="示例药品",
                spec=scan_spec,
                pres_num=2,
                qrcode_id=f"QR{int(time.time())}",
                scan_spec=scan_spec,
                scan_num=2,
                basket_no=record[2],  # basket_no
                scan_result=1,  # 匹配
                is_check=1
            )
            db.add(detail)
            
            # 标记本地记录为已同步
            mark_synced_record('local_scan_records', record[0])
            synced_count += 1
            
            results.append({
                "type": "scan",
                "id": record[0],
                "status": "SUCCESS",
                "pres_no": record[1]
            })
        except Exception as e:
            results.append({
                "type": "scan",
                "id": record[0],
                "status": "FAILED",
                "reason": str(e)
            })
            failed_count += 1
    
    # 同步离线进度记录
    offline_progress = get_offline_records('local_progress_records')
    for record in offline_progress:
        try:
            check_main = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.pres_no == record[1]).first()
            if not check_main:
                results.append({
                    "type": "progress",
                    "id": record[0],
                    "status": "FAILED",
                    "reason": "复核未初始化"
                })
                failed_count += 1
                continue
            
            progress_json = record[3]  # progress_info
            
            existing = db.query(models.DrugCheckProgress).filter(models.DrugCheckProgress.check_main_id == check_main.id).first()
            if existing:
                # 更新现有进度
                existing.progress_json = progress_json
                existing.save_time = datetime.utcnow()
            else:
                # 创建新进度记录
                progress = models.DrugCheckProgress(
                    check_main_id=check_main.id,
                    pres_no=record[1],  # pres_no
                    progress_json=progress_json,
                    save_by=record[2]  # check_by
                )
                db.add(progress)
            
            # 标记本地记录为已同步
            mark_synced_record('local_progress_records', record[0])
            synced_count += 1
            
            results.append({
                "type": "progress",
                "id": record[0],
                "status": "SUCCESS",
                "pres_no": record[1]
            })
        except Exception as e:
            results.append({
                "type": "progress",
                "id": record[0],
                "status": "FAILED",
                "reason": str(e)
            })
            failed_count += 1
    
    # 同步离线提交记录
    offline_submits = get_offline_records('local_submit_records')
    for record in offline_submits:
        try:
            check_main = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.pres_no == record[1]).first()
            if not check_main:
                results.append({
                    "type": "submit",
                    "id": record[0],
                    "status": "FAILED",
                    "reason": "复核记录不存在"
                })
                failed_count += 1
                continue
            
            # 更新复核状态
            check_main.check_status = 2  # 已完成
            check_main.check_end_time = datetime.utcnow()
            check_main.check_qualified = 1  # 假设合格
            check_main.submit_by = record[2]  # check_by
            check_main.submit_time = datetime.utcnow()
            
            # 更新处方状态
            pres = db.query(models.HISPrescription).filter(models.HISPrescription.pres_no == record[1]).first()
            if pres:
                pres.pres_status = 3  # 已复核
            
            # 标记本地记录为已同步
            mark_synced_record('local_submit_records', record[0])
            synced_count += 1
            
            results.append({
                "type": "submit",
                "id": record[0],
                "status": "SUCCESS",
                "pres_no": record[1]
            })
        except Exception as e:
            results.append({
                "type": "submit",
                "id": record[0],
                "status": "FAILED",
                "reason": str(e)
            })
            failed_count += 1
    
    db.commit()
    
    return success_response({
        "synced_count": synced_count,
        "failed_count": failed_count,
        "total_processed": synced_count + failed_count,
        "results": results,
        "message": f"离线数据同步完成，成功: {synced_count}，失败: {failed_count}"
    })
