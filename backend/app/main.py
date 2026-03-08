from fastapi import FastAPI, Depends, HTTPException, Header, Request, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, inspect, text
import base64
import hashlib
import jwt
import json
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional, Any
import os
import sys
import qrcode as qrcode_module
from io import BytesIO

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, Base, engine
from app import models, schemas

# 创建所有数据库表
Base.metadata.create_all(bind=engine)


def ensure_schema_compatibility():
    """兼容历史数据库结构，避免老库缺列导致 500。"""
    try:
        inspector = inspect(engine)
        if "check_error_record" not in inspector.get_table_names():
            return

        existing_columns = {column["name"] for column in inspector.get_columns("check_error_record")}
        required_columns = {
            "drug_name": "VARCHAR(50)",
            "pres_spec": "VARCHAR(10)",
            "scan_spec": "VARCHAR(10)",
            "pres_num": "INTEGER",
            "scan_num": "INTEGER",
            "error_by": "VARCHAR(20)",
            "handle_type": "VARCHAR(20)",
            "handle_by": "VARCHAR(20)"
        }

        with engine.begin() as conn:
            for column_name, column_type in required_columns.items():
                if column_name in existing_columns:
                    continue
                conn.execute(text(f"ALTER TABLE check_error_record ADD COLUMN {column_name} {column_type}"))
                print(f"✅ 自动补齐字段: check_error_record.{column_name}")
    except Exception as exc:
        print(f"⚠️ 数据库兼容检查失败: {str(exc)[:200]}")


ensure_schema_compatibility()

# 创建二维码图片存储目录
QRCODE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "qrcodes")
os.makedirs(QRCODE_DIR, exist_ok=True)

# 创建报告存储目录
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# ========== CORS 跨域配置 ==========
app = FastAPI(title="饮片复核系统 API", version="1.0.0")

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
    try:
        # 仅检测业务数据库连通性，避免外网不可达导致误判离线
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except:
        return False

def ensure_demo_business_data(db: Session):
    """当业务数据为空时，补充最小可用演示数据。"""
    now = datetime.utcnow()

    if db.query(models.DrugInfo).filter(models.DrugInfo.is_delete == 0).count() == 0:
        demo_drugs = [
            ("13310", "盐巴戟天", "5g"),
            ("13311", "当归", "3g"),
            ("13312", "黄芪", "10g"),
            ("13313", "党参", "6g"),
            ("13314", "陈皮", "4g")
        ]
        for cj_id, drug_name, spec in demo_drugs:
            db.add(models.DrugInfo(
                cj_id=cj_id,
                drug_name=drug_name,
                drug_type="中药饮片",
                spec_range=spec,
                his_sync_time=now,
                status=1
            ))

    if db.query(models.BasketManage).filter(models.BasketManage.is_delete == 0).count() == 0:
        for index in range(1, 4):
            basket_no = f"K{now.strftime('%Y%m%d')}{index:03d}"
            db.add(models.BasketManage(
                basket_no=basket_no,
                basket_name=f"复核筐{index}",
                create_type=1,
                status=1,
                create_by="system"
            ))

    if db.query(models.HISPrescription).filter(models.HISPrescription.is_delete == 0).count() == 0:
        pres_list = [
            (f"CF{now.strftime('%Y%m%d')}001", "张三", "中医科", "李医生", 3, 3),
            (f"CF{now.strftime('%Y%m%d')}002", "李四", "中医科", "王医生", 3, 2),
            (f"CF{now.strftime('%Y%m%d')}003", "王五", "针灸科", "赵医生", 2, 1)
        ]
        for pres_no, patient_name, dept_name, doc_name, drug_total, pres_status in pres_list:
            db.add(models.HISPrescription(
                pres_no=pres_no,
                patient_name=patient_name,
                patient_id="430102199001010000",
                dept_name=dept_name,
                doc_name=doc_name,
                pres_time=now - timedelta(minutes=15),
                drug_total=drug_total,
                sync_time=now,
                pres_status=pres_status
            ))

    db.flush()

    if db.query(models.DrugCheckMain).filter(models.DrugCheckMain.is_delete == 0).count() == 0:
        target_pres = db.query(models.HISPrescription).filter(
            models.HISPrescription.is_delete == 0,
            models.HISPrescription.pres_status.in_([2, 3])
        ).order_by(desc(models.HISPrescription.pres_time)).limit(2).all()

        reviewers = ["fh001", "fh002"]
        for index, pres in enumerate(target_pres):
            is_completed = pres.pres_status == 3
            start_time = now - timedelta(minutes=30 - index * 10)
            check_main = models.DrugCheckMain(
                pres_no=pres.pres_no,
                check_by=reviewers[index % len(reviewers)],
                check_station=f"T0{index + 1}",
                check_start_time=start_time,
                check_end_time=(start_time + timedelta(minutes=8)) if is_completed else None,
                check_status=2 if is_completed else 1,
                check_qualified=1 if is_completed else None,
                submit_by=reviewers[index % len(reviewers)] if is_completed else None,
                submit_time=(start_time + timedelta(minutes=8)) if is_completed else None,
                error_total=0
            )
            db.add(check_main)

    db.flush()

    if db.query(models.DrugCheckDetail).filter(models.DrugCheckDetail.is_delete == 0).count() == 0:
        check_mains = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.is_delete == 0).all()
        drug_pool = db.query(models.DrugInfo).filter(models.DrugInfo.is_delete == 0).order_by(models.DrugInfo.id).limit(3).all()

        for check_main in check_mains:
            for index, drug in enumerate(drug_pool, start=1):
                pres_num = 2 if index == 1 else 1
                is_match = not (check_main.check_status == 2 and check_main.check_qualified == 0 and index == len(drug_pool))
                db.add(models.DrugCheckDetail(
                    check_main_id=check_main.id,
                    pres_no=check_main.pres_no,
                    cj_id=drug.cj_id,
                    drug_name=drug.drug_name,
                    spec=(drug.spec_range or "5g")[:10],
                    pres_num=pres_num,
                    qrcode_id=f"QR{int(time.time())}{check_main.id}{index}",
                    scan_spec=(drug.spec_range or "5g")[:10],
                    scan_num=pres_num if is_match else max(pres_num - 1, 1),
                    scan_time=now - timedelta(minutes=index),
                    basket_no=f"K{now.strftime('%Y%m%d')}001",
                    scan_result=1 if is_match else 0,
                    is_check=1 if is_match else 0
                ))

    db.flush()

    if db.query(models.PresBasketRelation).filter(models.PresBasketRelation.is_delete == 0).count() == 0:
        detail_rows = db.query(models.DrugCheckDetail).filter(models.DrugCheckDetail.is_delete == 0).limit(10).all()
        for detail in detail_rows:
            db.add(models.PresBasketRelation(
                pres_no=detail.pres_no,
                check_main_id=detail.check_main_id,
                basket_no=detail.basket_no,
                cj_id=detail.cj_id,
                drug_name=detail.drug_name,
                basket_drug_num=detail.pres_num,
                basket_status=1,
                create_by="system"
            ))

    if db.query(models.CheckErrorRecord).filter(models.CheckErrorRecord.is_delete == 0).count() == 0:
        sample_detail = db.query(models.DrugCheckDetail).filter(models.DrugCheckDetail.is_delete == 0).first()
        if sample_detail:
            db.add(models.CheckErrorRecord(
                check_detail_id=sample_detail.id,
                check_main_id=sample_detail.check_main_id,
                pres_no=sample_detail.pres_no,
                cj_id=sample_detail.cj_id,
                drug_name=sample_detail.drug_name,
                error_type="NUM_ERROR",
                error_desc="扫码数量与处方数量不一致",
                pres_standard=f"{sample_detail.spec}/{sample_detail.pres_num}",
                scan_actual=f"{sample_detail.scan_spec}/{sample_detail.scan_num}",
                error_time=now - timedelta(minutes=5),
                error_status=1,
                pres_spec=sample_detail.spec,
                scan_spec=sample_detail.scan_spec,
                pres_num=sample_detail.pres_num,
                scan_num=sample_detail.scan_num,
                error_by="fh001"
            ))

    if db.query(models.CheckOperateRecord).filter(models.CheckOperateRecord.is_delete == 0).count() == 0:
        mains = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.is_delete == 0).limit(5).all()
        for main in mains:
            db.add(models.CheckOperateRecord(
                pres_no=main.pres_no,
                check_main_id=main.id,
                operate_user=main.check_by,
                operate_module="扫码复核",
                operate_type="提交",
                operate_desc=f"处方{main.pres_no}完成复核流程",
                operate_time=main.check_end_time or main.check_start_time or now,
                operate_ip="127.0.0.1"
            ))

    if db.query(models.VideoMonitorLink).filter(models.VideoMonitorLink.is_delete == 0).count() == 0:
        sample_detail = db.query(models.DrugCheckDetail).filter(models.DrugCheckDetail.is_delete == 0).first()
        if sample_detail:
            check_main = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.id == sample_detail.check_main_id).first()
            video_time = sample_detail.scan_time or now
            db.add(models.VideoMonitorLink(
                check_detail_id=sample_detail.id,
                pres_no=sample_detail.pres_no,
                scan_time=video_time,
                check_station=(check_main.check_station if check_main else "T01"),
                camera_no="CAM01",
                video_url="https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
                video_download="https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
                video_snapshot="",
                video_valid_time=video_time + timedelta(days=7)
            ))


# 初始化默认数据
def init_default_data():
    """创建默认管理员、角色、企业及最小可用演示数据（幂等）。"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        admin_pwd_hash = hashlib.md5("admin123".encode()).hexdigest()
        force_reset_admin_password = os.getenv("RESET_ADMIN_PASSWORD", "false").lower() == "true"
        admin_user = db.query(models.SysUser).filter(models.SysUser.user_account == "admin").first()
        if not admin_user:
            db.add(models.SysUser(
                user_account="admin",
                user_name="超级管理员",
                user_pwd=admin_pwd_hash,
                dept_name="系统管理",
                post="系统管理员",
                status=1,
                create_by="system"
            ))
        else:
            if admin_user.is_delete == 1:
                admin_user.is_delete = 0
            if admin_user.status == 0:
                admin_user.status = 1
            if not admin_user.user_name:
                admin_user.user_name = "超级管理员"
            if not admin_user.dept_name:
                admin_user.dept_name = "系统管理"
            if not admin_user.post:
                admin_user.post = "系统管理员"
            if force_reset_admin_password or not admin_user.user_pwd:
                admin_user.user_pwd = admin_pwd_hash
                admin_user.update_by = "system"
                admin_user.update_time = datetime.utcnow()

        review_users = [
            ("fh001", "复核员一", "中药房", "复核员", "13800138001"),
            ("fh002", "复核员二", "中药房", "复核员", "13800138002")
        ]
        for account, name, dept, post, phone in review_users:
            existing_user = db.query(models.SysUser).filter(models.SysUser.user_account == account).first()
            if existing_user:
                if existing_user.is_delete == 1:
                    existing_user.is_delete = 0
                    existing_user.status = 1
            else:
                db.add(models.SysUser(
                    user_account=account,
                    user_name=name,
                    user_pwd=hashlib.md5("123456".encode()).hexdigest(),
                    dept_name=dept,
                    post=post,
                    phone=phone,
                    status=1,
                    create_by="system"
                ))

        enterprises = [
            (1, '亳州市沪谯药业有限公司'),
            (2, '湖南三湘中药饮片有限公司'),
            (3, '长沙新林制药有限公司'),
            (4, '安徽亳药千草中药饮片有限公司'),
            (5, '北京仟草中药饮片有限公司'),
            (6, '天津尚药堂制药有限公司')
        ]
        for code, name in enterprises:
            enterprise = db.query(models.Enterprise).filter(models.Enterprise.enterprise_code == code).first()
            if enterprise:
                enterprise.enterprise_name = name
                enterprise.status = 1
                if enterprise.is_delete == 1:
                    enterprise.is_delete = 0
            else:
                db.add(models.Enterprise(
                    enterprise_code=code,
                    enterprise_name=name,
                    create_by="system",
                    status=1
                ))

        roles = [
            ("SUPER_ADMIN", "超级管理员", "ALL"),
            ("SYS_ADMIN", "系统管理员", "SYS:*"),
            ("QR_MANAGER", "二维码管理员", "QR:*"),
            ("REVIEWER", "复核员", "CHECK:*"),
            ("VIEWER", "查询员", "VIEW:*"),
            ("TRACE_MANAGER", "溯源管理员", "TRACE:*")
        ]
        for role_code, role_name, permissions in roles:
            role = db.query(models.SysRole).filter(models.SysRole.role_code == role_code).first()
            if role:
                role.role_name = role_name
                role.role_permission = permissions
                role.role_desc = f"{role_name}角色"
                role.status = 1
                if role.is_delete == 1:
                    role.is_delete = 0
            else:
                db.add(models.SysRole(
                    role_code=role_code,
                    role_name=role_name,
                    role_permission=permissions,
                    role_desc=f"{role_name}角色",
                    status=1,
                    create_time=datetime.utcnow()
                ))

        ensure_demo_business_data(db)
        db.commit()
        print("✅ 默认数据初始化成功")
        print("   默认管理员账号: admin / admin123")
        if force_reset_admin_password:
            print("   已按环境变量 RESET_ADMIN_PASSWORD=true 重置管理员密码")
    except Exception as e:
        db.rollback()
        print(f"⚠️ 初始化数据失败: {str(e)[:200]}")
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

# 二维码图片访问路由
@app.get("/zyfh/qrcodes/{qrcode_id}.png")
async def get_qrcode_image(qrcode_id: str, db: Session = Depends(get_db)):
    """获取二维码图片"""
    img_path = os.path.join(QRCODE_DIR, f"{qrcode_id}.png")
    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/png")

    qrcode_record = db.query(models.QRCodeGenerate).filter(
        models.QRCodeGenerate.qrcode_id == qrcode_id,
        models.QRCodeGenerate.is_delete == 0
    ).first()

    if not qrcode_record:
        raise HTTPException(status_code=404, detail="二维码图片不存在")

    try:
        qr = qrcode_module.QRCode(
            version=1,
            error_correction=qrcode_module.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qrcode_record.qrcode_origin)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(img_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"二维码图片重建失败: {str(exc)[:120]}")

    if os.path.exists(img_path):
        return FileResponse(img_path, media_type="image/png")

    raise HTTPException(status_code=404, detail="二维码图片不存在")

@app.get("/zyfh/reports/{report_file}")
async def get_report_file(report_file: str):
    """下载溯源报告"""
    report_path = os.path.join(REPORT_DIR, report_file)
    if os.path.exists(report_path):
        return FileResponse(report_path, media_type="application/json", filename=report_file)
    raise HTTPException(status_code=404, detail="报告文件不存在")

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

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常统一响应"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(str(exc.status_code), str(exc.detail))
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """未捕获异常统一响应，避免前端收到无 CORS 头的裸 500"""
    return JSONResponse(
        status_code=500,
        content=error_response("5000", f"服务器内部错误: {str(exc)}")
    )

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


def parse_datetime_value(value: Optional[str]) -> Optional[datetime]:
    """兼容常见日期时间格式（含 ISO 字符串）。"""
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None

    for fmt in [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d"
    ]:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    try:
        iso_value = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_value)
        if dt.tzinfo:
            return dt.replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def map_dashboard_status(check_status: Optional[int], check_qualified: Optional[int]) -> int:
    """统一工作台状态编码：1未复核 2已复核 3复核异常 4复核中。"""
    if check_status == 1:
        return 4
    if check_status == 2:
        return 2 if check_qualified == 1 else 3
    return 1

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """获取当前登录用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.replace("Bearer ", "").strip()
    user_id = verify_token(token)
    user = db.query(models.SysUser).filter(models.SysUser.id == user_id).first()
    if not user or user.is_delete == 1:
        raise HTTPException(status_code=401, detail="User not found")
    if user.status == 0:
        raise HTTPException(status_code=403, detail="User disabled")
    return user

# ========== 通用接口：系统认证 ==========

@app.post("/zyfh/api/v1/system/token/get")
def get_token(req: schemas.TokenRequest, db: Session = Depends(get_db)):
    """获取访问Token"""
    user = db.query(models.SysUser).filter(models.SysUser.user_account == req.user_account).first()
    if not user or user.is_delete == 1 or user.status == 0 or user.user_pwd != hash_password(req.user_pwd):
        return error_response("2000", "用户账号或密码错误")

    role_name = ""
    role_binding = db.query(models.SysUserRole).filter(
        models.SysUserRole.user_id == user.id,
        models.SysUserRole.is_delete == 0
    ).first()
    if role_binding:
        role = db.query(models.SysRole).filter(
            models.SysRole.id == role_binding.role_id,
            models.SysRole.is_delete == 0
        ).first()
        if role:
            role_name = role.role_name

    user.login_time = datetime.utcnow()
    db.commit()
    
    token = generate_token(user.id)
    expire_time = int(time.time()) + 86400
    return success_response({
        "token": f"Bearer {token}",
        "expireTime": expire_time,
        "userInfo": {
            "userAccount": user.user_account,
            "userName": user.user_name,
            "deptName": user.dept_name,
            "post": user.post,
            "phone": user.phone,
            "roleName": role_name
        }
    })

@app.get("/zyfh/api/v1/health")
def health_check():
    """健康检查"""
    return success_response({"status": "ok"}, "系统运行正常")

# ========== 二维码管理模块 ==========

@app.post("/zyfh/api/v1/qrcode/enterprise/save")
def save_enterprise(req: schemas.EnterpriseSaveRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """新增/维护企业标志"""
    existing = db.query(models.Enterprise).filter(models.Enterprise.enterprise_code == req.code).first()
    if existing:
        existing.enterprise_name = req.name
        existing.status = req.status
        existing.update_by = current_user.user_account
        existing.update_time = datetime.utcnow()
    else:
        enterprise = models.Enterprise(
            enterprise_code=req.code,
            enterprise_name=req.name,
            status=req.status,
            create_by=current_user.user_account
        )
        db.add(enterprise)
    db.commit()
    return success_response({"enterprise_code": req.code})

@app.get("/zyfh/api/v1/qrcode/enterprise/list")
def list_enterprises(status: int = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询企业列表"""
    query = db.query(models.Enterprise)
    if status is not None:
        query = query.filter(models.Enterprise.status == status)
    
    enterprises = query.all()
    result = []
    for enterprise in enterprises:
        result.append({
            "enterprise_code": enterprise.enterprise_code,
            "enterprise_name": enterprise.enterprise_name,
            "status": enterprise.status,
            "create_time": enterprise.create_time,
            "update_time": enterprise.update_time
        })
    
    return success_response({
        "total": len(result),
        "list": result
    })

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
    qrcode_url = f"/zyfh/qrcodes/{qrcode_id}.png"
    
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

    # 7. 生成二维码图片
    try:
        qr = qrcode_module.QRCode(
            version=1,
            error_correction=qrcode_module.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qrcode_origin)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_path = os.path.join(QRCODE_DIR, f"{qrcode_id}.png")
        img.save(img_path)
    except Exception as e:
        print(f"二维码图片生成失败: {e}")

    return success_response({
        "qrcode_id": qrcode_id,
        "qrcode_content": qrcode_origin,
        "base64_str": base64_str,
        "qrcode_url": qrcode_url
    })

@app.post("/zyfh/api/v1/qrcode/generate/batch")
def generate_batch_qrcode(payload: Any = Body(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """二维码批量生成"""
    if isinstance(payload, dict):
        raw_list = payload.get("qrcode_list") or payload.get("qrcodeList") or payload.get("list")
        create_by = payload.get("create_by") or payload.get("createBy") or current_user.user_account
    elif isinstance(payload, list):
        raw_list = payload
        create_by = current_user.user_account
    else:
        return error_response("1000", "批量参数格式错误")

    if not isinstance(raw_list, list) or len(raw_list) == 0:
        return error_response("1000", "缺少批量二维码数据")

    success_count = 0
    fail_count = 0
    fail_list = []
    
    for idx, item in enumerate(raw_list):
        try:
            if isinstance(item, schemas.QRGenerateRequest):
                qr_req = item
            elif isinstance(item, dict):
                qr_req = schemas.QRGenerateRequest(**item)
            else:
                raise ValueError("单条二维码参数格式错误")

            qr_req_dict = qr_req.dict() if hasattr(qr_req, "dict") else qr_req.model_dump()

            # 验证企业编码
            enterprise = db.query(models.Enterprise).filter(models.Enterprise.enterprise_code == qr_req.enterprise_code).first()
            if not enterprise:
                fail_list.append({
                    "index": idx,
                    "params": qr_req_dict,
                    "reason": "企业标志未维护"
                })
                fail_count += 1
                continue
            
            # 验证院内编码
            drug = db.query(models.DrugInfo).filter(models.DrugInfo.cj_id == qr_req.cj_id).first()
            if not drug:
                fail_list.append({
                    "index": idx,
                    "params": qr_req_dict,
                    "reason": "院内编码无效，请核对"
                })
                fail_count += 1
                continue
            
            # 数据校验
            if not qr_req.spec.endswith('g'):
                fail_list.append({
                    "index": idx,
                    "params": qr_req_dict,
                    "reason": "规格格式错误，应为数字+g，数字范围1-30"
                })
                fail_count += 1
                continue

            if not (1 <= float(qr_req.spec.rstrip('g')) <= 30):
                fail_list.append({
                    "index": idx,
                    "params": qr_req_dict,
                    "reason": "规格格式错误，应为数字+g，数字范围1-30"
                })
                fail_count += 1
                continue
                
            if not (5 <= len(qr_req.batch_no) <= 10) or not qr_req.batch_no.isdigit():
                fail_list.append({
                    "index": idx,
                    "params": qr_req_dict,
                    "reason": "批号格式错误，应为5-10位纯数字"
                })
                fail_count += 1
                continue

            if qr_req.num <= 0 or qr_req.weight <= 0:
                fail_list.append({
                    "index": idx,
                    "params": qr_req_dict,
                    "reason": "数量和重量必须大于0"
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
            qrcode_url = f"/zyfh/qrcodes/{qrcode_id}.png"
            
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

            try:
                qr = qrcode_module.QRCode(
                    version=1,
                    error_correction=qrcode_module.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qrcode_origin)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                img_path = os.path.join(QRCODE_DIR, f"{qrcode_id}.png")
                img.save(img_path)
            except Exception:
                pass

            success_count += 1
            
        except Exception as e:
            fail_list.append({
                "index": idx,
                "params": item,
                "reason": str(e)
            })
            fail_count += 1
    
    db.commit()
    
    return success_response({
        "success_num": success_count,
        "fail_num": fail_count,
        "fail_list": fail_list,
        "download_url": None
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
            "spec": rec.spec,
            "batch_no": rec.batch_no,
            "generate_by": rec.generate_by,
            "generate_time": rec.generate_time.isoformat() if rec.generate_time else None,
            "qrcode_url": rec.qrcode_url,
            "qrcode_origin": rec.qrcode_origin,
            "base64_str": rec.base64_str
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

def get_active_basket_nos(db: Session) -> List[str]:
    baskets = db.query(models.BasketManage).filter(
        models.BasketManage.is_delete == 0,
        models.BasketManage.status == 1
    ).order_by(desc(models.BasketManage.create_time)).limit(100).all()
    return [basket.basket_no for basket in baskets]


def build_check_drug_list(db: Session, pres_no: str, fallback_total: int = 0) -> List[Dict[str, Any]]:
    relation_rows = db.query(
        models.PresBasketRelation.cj_id,
        func.max(models.PresBasketRelation.drug_name).label("drug_name"),
        func.sum(models.PresBasketRelation.basket_drug_num).label("pres_num")
    ).filter(
        models.PresBasketRelation.pres_no == pres_no,
        models.PresBasketRelation.is_delete == 0
    ).group_by(models.PresBasketRelation.cj_id).all()

    rows: List[Dict[str, Any]] = []

    if relation_rows:
        for cj_id, drug_name, pres_num in relation_rows:
            detail = db.query(models.DrugCheckDetail).filter(
                models.DrugCheckDetail.pres_no == pres_no,
                models.DrugCheckDetail.cj_id == cj_id,
                models.DrugCheckDetail.is_delete == 0
            ).order_by(desc(models.DrugCheckDetail.scan_time)).first()
            drug_info = db.query(models.DrugInfo).filter(models.DrugInfo.cj_id == cj_id).first()
            rows.append({
                "cj_id": cj_id,
                "drug_name": drug_name or (drug_info.drug_name if drug_info else cj_id),
                "spec": (detail.spec if detail else (drug_info.spec_range if drug_info else "-")) or "-",
                "pres_num": int(pres_num or 0),
                "scan_num": int(detail.scan_num if detail else 0),
                "is_check": 1 if detail and detail.is_check == 1 else 0
            })
        return rows

    detail_rows = db.query(
        models.DrugCheckDetail.cj_id,
        func.max(models.DrugCheckDetail.drug_name).label("drug_name"),
        func.max(models.DrugCheckDetail.spec).label("spec"),
        func.sum(models.DrugCheckDetail.pres_num).label("pres_num"),
        func.sum(models.DrugCheckDetail.scan_num).label("scan_num"),
        func.max(models.DrugCheckDetail.is_check).label("is_check")
    ).filter(
        models.DrugCheckDetail.pres_no == pres_no,
        models.DrugCheckDetail.is_delete == 0
    ).group_by(models.DrugCheckDetail.cj_id).all()

    if detail_rows:
        for cj_id, drug_name, spec, pres_num, scan_num, is_check in detail_rows:
            rows.append({
                "cj_id": cj_id,
                "drug_name": drug_name,
                "spec": spec,
                "pres_num": int(pres_num or 0),
                "scan_num": int(scan_num or 0),
                "is_check": int(is_check or 0)
            })
        return rows

    limit_size = min(max(fallback_total or 3, 1), 10)
    demo_drugs = db.query(models.DrugInfo).filter(
        models.DrugInfo.is_delete == 0,
        models.DrugInfo.status == 1
    ).order_by(models.DrugInfo.id).limit(limit_size).all()

    for drug in demo_drugs:
        rows.append({
            "cj_id": drug.cj_id,
            "drug_name": drug.drug_name,
            "spec": drug.spec_range or "-",
            "pres_num": 1,
            "scan_num": 0,
            "is_check": 0
        })

    return rows

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
    pres = db.query(models.HISPrescription).filter(
        models.HISPrescription.pres_no == req.pres_no,
        models.HISPrescription.is_delete == 0
    ).first()
    if not pres:
        return error_response("8000", "处方不存在")

    check_main = db.query(models.DrugCheckMain).filter(
        models.DrugCheckMain.pres_no == req.pres_no,
        models.DrugCheckMain.is_delete == 0
    ).first()

    result_status = "initialized"
    if check_main:
        if check_main.check_status == 2:
            return error_response("8000", "处方已复核完成")

        result_status = "in_progress"
        check_main.check_by = req.check_by or check_main.check_by
        check_main.check_station = req.check_station or check_main.check_station
    else:
        check_main = models.DrugCheckMain(
            pres_no=req.pres_no,
            check_by=req.check_by,
            check_station=req.check_station,
            check_status=1
        )
        db.add(check_main)

    pres.pres_status = 2
    db.commit()
    db.refresh(check_main)

    drug_list = build_check_drug_list(db, req.pres_no, pres.drug_total)
    baskets = get_active_basket_nos(db)

    return success_response({
        "check_main_id": check_main.id,
        "pres_no": req.pres_no,
        "status": result_status,
        "prescription": {
            "pres_no": pres.pres_no,
            "patient_name": pres.patient_name,
            "doc_name": pres.doc_name,
            "dept_name": pres.dept_name,
            "pres_time": pres.pres_time.isoformat() if pres.pres_time else None,
            "drug_total": pres.drug_total
        },
        "drug_list": drug_list,
        "baskets": baskets
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
    
    # 5. 获取药品信息与处方预期
    drug = db.query(models.DrugInfo).filter(models.DrugInfo.cj_id == scan_cj_id).first()
    drug_name = drug.drug_name if drug else f"未知药品({scan_cj_id})"

    expected_relations = db.query(models.PresBasketRelation).filter(
        models.PresBasketRelation.pres_no == req.pres_no,
        models.PresBasketRelation.is_delete == 0
    ).all()
    expected_cj_ids = {item.cj_id for item in expected_relations}
    expected_num = sum(item.basket_drug_num for item in expected_relations if item.cj_id == scan_cj_id)
    if expected_num <= 0:
        expected_num = num if num > 0 else 1

    is_match = True if not expected_cj_ids else (scan_cj_id in expected_cj_ids)

    # 6. 保存扫码记录
    detail = models.DrugCheckDetail(
        check_main_id=check_main.id,
        pres_no=req.pres_no,
        cj_id=scan_cj_id,
        drug_name=drug_name,
        spec=scan_spec,
        pres_num=expected_num,
        qrcode_id=f"QR{int(time.time())}",
        scan_spec=scan_spec,
        scan_num=num,
        basket_no=req.basket_no,
        scan_result=1 if is_match else 0,
        is_check=1 if is_match and num >= expected_num else 0
    )
    db.add(detail)
    db.flush()

    if not is_match:
        exists_error = db.query(models.CheckErrorRecord).filter(
            models.CheckErrorRecord.check_detail_id == detail.id,
            models.CheckErrorRecord.is_delete == 0
        ).first()
        if not exists_error:
            db.add(models.CheckErrorRecord(
                check_detail_id=detail.id,
                check_main_id=check_main.id,
                pres_no=req.pres_no,
                cj_id=scan_cj_id,
                drug_name=drug_name,
                error_type="DRUG_ERROR",
                error_desc="扫描药品与处方药品不匹配",
                pres_standard="处方药品列表",
                scan_actual=f"{scan_cj_id}/{scan_spec}",
                error_status=1,
                pres_spec="-",
                scan_spec=scan_spec,
                pres_num=expected_num,
                scan_num=num,
                error_by=req.check_by
            ))
            check_main.error_total = (check_main.error_total or 0) + 1

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

    scan_result = "match" if is_match else "mismatch"

    return success_response({
        "drug_name": drug_name,
        "scan_result": "SUCCESS" if is_match else "MISMATCH",
        "scan_result_text": scan_result,
        "scanResult": scan_result,
        "cj_id": scan_cj_id,
        "spec": scan_spec,
        "batch_no": batch_no,
        "num": num,
        "weight": weight,
        "basket_no": req.basket_no,
        "scan_time": datetime.utcnow().isoformat(),
        "drug_info": {
            "cj_id": scan_cj_id,
            "drug_name": drug_name,
            "spec": scan_spec,
            "pres_num": expected_num
        },
        "drugInfo": {
            "cjId": scan_cj_id,
            "drugName": drug_name,
            "spec": scan_spec,
            "presNum": expected_num
        }
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


@app.get("/zyfh/api/v1/dashboard/overview")
def get_dashboard_overview(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """工作台数据总览（真实业务数据聚合）。"""
    now = datetime.utcnow()
    day_start = datetime(now.year, now.month, now.day)
    day_end = day_start + timedelta(days=1)

    today_checks = db.query(models.DrugCheckMain).filter(
        models.DrugCheckMain.is_delete == 0,
        models.DrugCheckMain.check_start_time >= day_start,
        models.DrugCheckMain.check_start_time < day_end
    ).all()

    today_pres = len(today_checks)
    qualified_total = sum(1 for item in today_checks if item.check_qualified == 1)
    qualified_rate = round((qualified_total / today_pres * 100), 1) if today_pres else 0

    today_errors = db.query(func.count(models.CheckErrorRecord.id)).filter(
        models.CheckErrorRecord.is_delete == 0,
        models.CheckErrorRecord.error_time >= day_start,
        models.CheckErrorRecord.error_time < day_end
    ).scalar() or 0

    pending_pres = db.query(func.count(models.HISPrescription.id)).filter(
        models.HISPrescription.is_delete == 0,
        models.HISPrescription.pres_status.in_([1, 2])
    ).scalar() or 0

    recent_rows = db.query(
        models.DrugCheckMain.pres_no,
        models.DrugCheckMain.check_by,
        models.DrugCheckMain.check_status,
        models.DrugCheckMain.check_qualified,
        models.DrugCheckMain.check_start_time,
        models.DrugCheckMain.check_end_time,
        models.HISPrescription.patient_name
    ).outerjoin(
        models.HISPrescription,
        models.HISPrescription.pres_no == models.DrugCheckMain.pres_no
    ).filter(
        models.DrugCheckMain.is_delete == 0
    ).order_by(desc(models.DrugCheckMain.check_start_time)).limit(10).all()

    recent_records = []
    for pres_no, check_by, check_status, check_qualified, check_start_time, check_end_time, patient_name in recent_rows:
        check_time = check_end_time or check_start_time
        recent_records.append({
            "pres_no": pres_no,
            "patient_name": patient_name or "-",
            "check_by": check_by,
            "check_time": check_time.isoformat() if check_time else None,
            "status": map_dashboard_status(check_status, check_qualified)
        })

    return success_response({
        "today_pres": today_pres,
        "qualified_rate": qualified_rate,
        "today_errors": today_errors,
        "pending_pres": pending_pres,
        "recent_records": recent_records
    })

# ========== 错误提醒模块 ==========

@app.post("/zyfh/api/v1/alert/error/save")
def save_error_record(req: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """保存错误提醒记录"""
    check_detail_id = int(req.get("check_detail_id") or int(time.time() * 1000))
    while db.query(models.CheckErrorRecord).filter(models.CheckErrorRecord.check_detail_id == check_detail_id).first():
        check_detail_id += 1

    pres_standard = req.get("pres_standard") or req.get("pres_spec")
    scan_actual = req.get("scan_actual") or req.get("scan_spec")

    if not pres_standard:
        pres_standard = f"{req.get('pres_spec') or ''}/{req.get('pres_num') or ''}".strip("/") or "-"
    if not scan_actual:
        scan_actual = f"{req.get('scan_spec') or ''}/{req.get('scan_num') or ''}".strip("/") or "-"

    error_record = models.CheckErrorRecord(
        check_detail_id=check_detail_id,
        check_main_id=int(req.get("check_main_id") or 0),
        pres_no=req.get("pres_no") or "UNKNOWN",
        cj_id=req.get("cj_id") or "UNKNOWN",
        error_type=req.get("error_type") or "UNKNOWN",  # DRUG_NOT_MATCH, SPEC_ERROR, WEIGHT_ERROR 等
        error_desc=req.get("error_desc") or "未提供错误描述",
        pres_standard=pres_standard,
        scan_actual=scan_actual,
        drug_name=req.get("drug_name"),
        pres_spec=req.get("pres_spec"),
        scan_spec=req.get("scan_spec"),
        pres_num=req.get("pres_num"),
        scan_num=req.get("scan_num"),
        error_by=current_user.user_account,
        error_status=1  # 待处理
    )
    db.add(error_record)
    db.commit()
    db.refresh(error_record)
    
    return success_response({"error_id": error_record.id, "status": "saved"})

@app.put("/zyfh/api/v1/alert/error/handle")
def handle_error_record(req: schemas.ErrorHandleRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """处理（解决）错误提醒"""
    error_record = db.query(models.CheckErrorRecord).filter(
        models.CheckErrorRecord.id == int(req.error_id),
        models.CheckErrorRecord.is_delete == 0
    ).first()
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
    error_record.handle_type = req.handle_result
    error_record.handle_by = req.handle_by
    
    db.commit()
    
    return success_response({"error_id": req.error_id, "handle_result": "success"})

@app.get("/zyfh/api/v1/alert/error/stat/query")
@app.get("/zyfh/api/v1/alert/error/list")
def list_error_records(pres_no: str = None, error_status: int = None,
                      error_type: str = None, page: int = 1, size: int = 20,
                      presNo: str = None, errorType: str = None,
                      db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询错误提醒列表"""
    filter_pres_no = pres_no or presNo
    filter_error_type = error_type or errorType
    page = max(page, 1)
    size = min(max(size, 1), 200)

    query = db.query(models.CheckErrorRecord).filter(models.CheckErrorRecord.is_delete == 0)
    
    if filter_pres_no:
        query = query.filter(models.CheckErrorRecord.pres_no == filter_pres_no)
    if error_status is not None:
        query = query.filter(models.CheckErrorRecord.error_status == error_status)
    if filter_error_type:
        query = query.filter(models.CheckErrorRecord.error_type == filter_error_type)

    total = query.count()
    records = query.order_by(desc(models.CheckErrorRecord.error_time)).offset((page - 1) * size).limit(size).all()

    record_list = [
        {
            "error_id": r.id,
            "error_time": r.error_time.isoformat() if r.error_time else None,
            "pres_no": r.pres_no,
            "cj_id": r.cj_id,
            "drug_name": r.drug_name,
            "error_type": r.error_type,
            "error_desc": r.error_desc,
            "error_status": r.error_status,
            "handle_type": r.handle_type,
            "error_by": r.error_by,
            "handle_by": r.handle_by
        } for r in records
    ]

    return success_response({
        "total": total,
        "pages": (total + size - 1) // size,
        "page": page,
        "size": size,
        "list": record_list,
        "records": record_list
    })

# ========== 分筐管理模块 ==========

@app.post("/zyfh/api/v1/basket/save")
def save_basket(req: schemas.BasketCreateRequest, db: Session = Depends(get_db), 
               current_user=Depends(get_current_user)):
    """新增/维护分筐"""
    existing = db.query(models.BasketManage).filter(models.BasketManage.basket_no == req.basket_no).first()
    if existing:
        existing.basket_name = req.basket_name
        existing.status = req.status if req.status is not None else existing.status
        existing.is_delete = 0
    else:
        basket = models.BasketManage(
            basket_no=req.basket_no,
            basket_name=req.basket_name,
            status=req.status if req.status is not None else 1,
            create_by=req.create_by
        )
        db.add(basket)
    
    db.commit()
    return success_response({"basket_no": req.basket_no, "status": "saved"})

@app.post("/zyfh/api/v1/basket/relation/save")
def save_basket_relation(req: schemas.BasketDrugRelationRequest, 
                        db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """分筐关联（处方 -> 分筐 -> 药品）"""
    effective_create_by = req.create_by or current_user.user_account
    effective_check_main_id = req.check_main_id
    if effective_check_main_id is None:
        check_main = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.pres_no == req.pres_no).first()
        effective_check_main_id = check_main.id if check_main else 0

    # 检查分筐是否存在
    basket = db.query(models.BasketManage).filter(
        models.BasketManage.basket_no == req.basket_no,
        models.BasketManage.is_delete == 0
    ).first()
    if not basket:
        return error_response("8000", "分筐不存在")
    
    # 清除已有关系（如果需要更新的话）
    existing_relations = db.query(models.PresBasketRelation).filter(
        models.PresBasketRelation.pres_no == req.pres_no,
        models.PresBasketRelation.basket_no == req.basket_no,
        models.PresBasketRelation.is_delete == 0
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
            check_main_id=effective_check_main_id,
            basket_no=req.basket_no,
            cj_id=cj_id,
            drug_name=drug_name,
            basket_drug_num=1,  # 默认数量为1，实际应从处方中获取
            create_by=effective_create_by
        )
        db.add(relation)
    
    db.commit()
    return success_response({"basket_no": req.basket_no, "drug_count": len(req.cj_id_list), "status": "saved"})


@app.get("/zyfh/api/v1/basket/relation/query")
@app.get("/zyfh/api/v1/basket/relation/list")
def query_basket_relations(pres_no: str, basket_no: str = None,
                          db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询处方分筐关联（用于前端刷新最新数据）"""
    relation_query = db.query(models.PresBasketRelation).filter(
        models.PresBasketRelation.pres_no == pres_no,
        models.PresBasketRelation.is_delete == 0
    )

    if basket_no:
        relation_query = relation_query.filter(models.PresBasketRelation.basket_no == basket_no)

    relations = relation_query.order_by(desc(models.PresBasketRelation.create_time)).all()

    if relations:
        records = []
        for relation in relations:
            drug_info = db.query(models.DrugInfo).filter(models.DrugInfo.cj_id == relation.cj_id).first()
            spec = ""
            if drug_info and drug_info.spec_range:
                spec = drug_info.spec_range.split(",")[0]
            records.append({
                "id": relation.id,
                "pres_no": relation.pres_no,
                "basket_no": relation.basket_no,
                "cj_id": relation.cj_id,
                "drug_name": relation.drug_name,
                "spec": spec,
                "pres_num": relation.basket_drug_num,
                "basket_status": relation.basket_status,
                "create_time": relation.create_time.isoformat() if relation.create_time else None
            })

        return success_response({
            "total": len(records),
            "list": records
        })

    fallback_drugs = db.query(models.DrugInfo).filter(
        models.DrugInfo.is_delete == 0,
        models.DrugInfo.status == 1
    ).order_by(models.DrugInfo.cj_id).limit(20).all()

    fallback_list = [
        {
            "pres_no": pres_no,
            "basket_no": "",
            "cj_id": drug.cj_id,
            "drug_name": drug.drug_name,
            "spec": (drug.spec_range or "").split(",")[0],
            "pres_num": 1,
            "basket_status": 1
        }
        for drug in fallback_drugs
    ]

    return success_response({
        "total": len(fallback_list),
        "list": fallback_list
    })

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
    query = db.query(models.BasketManage).filter(models.BasketManage.is_delete == 0)
    
    if status is not None:
        query = query.filter(models.BasketManage.status == status)
    
    baskets = query.order_by(desc(models.BasketManage.create_time)).limit(50).all()
    
    basket_list = [
        {
            "basket_no": b.basket_no,
            "basket_name": b.basket_name,
            "create_type": b.create_type,
            "status": b.status,
            "create_by": b.create_by,
            "create_time": b.create_time.isoformat() if b.create_time else None
        }
        for b in baskets
    ]

    return success_response({
        "total": len(basket_list),
        "list": basket_list,
        "baskets": basket_list
    })


@app.put("/zyfh/api/v1/basket/disable")
def disable_basket(req: schemas.BasketDisableRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """作废分筐"""
    basket = db.query(models.BasketManage).filter(
        models.BasketManage.basket_no == req.basket_no,
        models.BasketManage.is_delete == 0
    ).first()

    if not basket:
        return error_response("8000", "分筐不存在")

    basket.status = 0
    db.commit()

    return success_response({
        "basket_no": req.basket_no,
        "status": "disabled"
    })

# ========== 溯源管理模块 ==========

@app.get("/zyfh/api/v1/trace/record/query")
def query_trace_records(req: schemas.TraceRecordQueryRequest = Depends(), 
                       db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询操作记录（溯源）"""
    query = db.query(
        models.DrugCheckDetail,
        models.HISPrescription.patient_name,
        models.DrugCheckMain.check_by,
        models.DrugCheckMain.check_station
    ).outerjoin(
        models.DrugCheckMain,
        models.DrugCheckMain.id == models.DrugCheckDetail.check_main_id
    ).outerjoin(
        models.HISPrescription,
        models.HISPrescription.pres_no == models.DrugCheckDetail.pres_no
    ).filter(
        models.DrugCheckDetail.is_delete == 0
    )

    if req.pres_no:
        query = query.filter(models.DrugCheckDetail.pres_no == req.pres_no)
    if req.cj_id:
        query = query.filter(models.DrugCheckDetail.cj_id == req.cj_id)
    if req.basket_no:
        query = query.filter(models.DrugCheckDetail.basket_no == req.basket_no)
    if req.check_by:
        query = query.filter(models.DrugCheckMain.check_by == req.check_by)
    if req.start_time and req.end_time:
        start_dt = parse_datetime_value(req.start_time)
        end_dt = parse_datetime_value(req.end_time)
        if not start_dt or not end_dt:
            return error_response("1000", "时间格式错误")
        query = query.filter(models.DrugCheckDetail.scan_time.between(start_dt, end_dt))

    total = query.count()
    records = query.order_by(desc(models.DrugCheckDetail.scan_time)).offset((req.page - 1) * req.size).limit(req.size).all()

    return success_response({
        "total": total,
        "pages": (total + req.size - 1) // req.size,
        "page": req.page,
        "size": req.size,
        "list": [
            {
                "record_id": detail.id,
                "pres_no": detail.pres_no,
                "patient_name": patient_name,
                "cj_id": detail.cj_id,
                "drug_name": detail.drug_name,
                "spec": detail.spec,
                "scan_spec": detail.scan_spec,
                "pres_num": detail.pres_num,
                "scan_num": detail.scan_num,
                "scan_time": detail.scan_time.isoformat() if detail.scan_time else None,
                "check_by": check_by,
                "basket_no": detail.basket_no,
                "scan_result": detail.scan_result,
                "check_station": check_station
            } for detail, patient_name, check_by, check_station in records
        ]
    })

@app.get("/zyfh/api/v1/trace/video/query")
def query_video_link(pres_no: str, scan_time: str, check_station: str, 
                    db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询关联视频（基于时间戳精准匹配）"""
    scan_datetime = parse_datetime_value(scan_time)
    if not scan_datetime:
        return error_response("1000", "扫码时间格式错误")
    
    # 查询视频监控联动记录，时间匹配精度为±1秒
    query = db.query(models.VideoMonitorLink).filter(
        models.VideoMonitorLink.pres_no == pres_no,
        models.VideoMonitorLink.check_station == check_station,
        models.VideoMonitorLink.is_delete == 0,
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
def generate_trace_report(req: schemas.TraceReportGenerateRequest, db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    """生成溯源报告"""
    target_pres_no = req.pres_no
    if not target_pres_no and req.pres_no_list:
        target_pres_no = req.pres_no_list[0]

    if not target_pres_no:
        return error_response("1000", "处方号不能为空")

    # 查询该处方的所有操作记录
    records = db.query(models.CheckOperateRecord).filter(
        models.CheckOperateRecord.pres_no == target_pres_no
    ).order_by(models.CheckOperateRecord.operate_time).all()

    # 生成报告内容
    report_content = {
        "report_id": f"RPT{int(time.time())}",
        "pres_no": target_pres_no,
        "total_operations": len(records),
        "operations": [
            {
                "time": r.operate_time.isoformat() if r.operate_time else None,
                "type": r.operate_type,
                "user": r.operate_user,
                "content": r.operate_desc
            } for r in records
        ],
        "generated_by": current_user.user_account,
        "generated_time": datetime.utcnow().isoformat()
    }

    report_filename = f"{report_content['report_id']}.json"
    report_path = os.path.join(REPORT_DIR, report_filename)
    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report_content, file, ensure_ascii=False, indent=2)

    return success_response({
        "report_id": report_content["report_id"],
        "pres_no": target_pres_no,
        "operation_count": len(records),
        "download_url": f"http://localhost:8000/zyfh/reports/{report_filename}",
        "status": "generated"
    })

# ========== 工作量统计模块 ==========

def format_stat_time(value: Optional[datetime], time_type: str) -> str:
    if not value:
        return ""

    normalized = (time_type or "MONTH").upper()
    if normalized == "DAY":
        return value.strftime("%Y-%m-%d")
    if normalized == "WEEK":
        year, week, _ = value.isocalendar()
        return f"{year}-W{week:02d}"
    if normalized == "YEAR":
        return value.strftime("%Y")
    return value.strftime("%Y-%m")


def build_workload_rows(req: schemas.WorkloadStatQueryRequest, db: Session) -> List[Dict[str, Any]]:
    check_query = db.query(models.DrugCheckMain).filter(models.DrugCheckMain.is_delete == 0)

    if req.stat_type == "USER" and req.check_by:
        check_query = check_query.filter(models.DrugCheckMain.check_by == req.check_by)

    check_mains = check_query.all()
    grouped: Dict[str, Dict[str, Any]] = {}
    time_type = (req.time_type or "MONTH").upper()

    for check_main in check_mains:
        stat_dt = check_main.check_end_time or check_main.submit_time or check_main.check_start_time

        if req.stat_type == "TIME":
            stat_key = format_stat_time(stat_dt, time_type)
            if req.stat_time:
                target = req.stat_time
                if time_type == "DAY" and stat_key != target:
                    continue
                if time_type == "MONTH" and stat_key != target[:7]:
                    continue
                if time_type == "YEAR" and stat_key != target[:4]:
                    continue
                if time_type == "WEEK" and target not in stat_key:
                    continue
        elif req.stat_type == "PRES":
            stat_key = check_main.pres_no
        else:
            stat_key = check_main.check_by or "UNKNOWN"

        if not stat_key:
            continue

        detail_query = db.query(models.DrugCheckDetail).filter(
            models.DrugCheckDetail.check_main_id == check_main.id,
            models.DrugCheckDetail.is_delete == 0
        )
        qrcode_total = detail_query.count()
        drug_total = db.query(func.count(func.distinct(models.DrugCheckDetail.cj_id))).filter(
            models.DrugCheckDetail.check_main_id == check_main.id,
            models.DrugCheckDetail.is_delete == 0
        ).scalar() or 0
        error_total = db.query(func.count(models.CheckErrorRecord.id)).filter(
            models.CheckErrorRecord.pres_no == check_main.pres_no,
            models.CheckErrorRecord.is_delete == 0
        ).scalar() or 0

        check_hours = 0.0
        if check_main.check_start_time and check_main.check_end_time:
            check_hours = max((check_main.check_end_time - check_main.check_start_time).total_seconds() / 3600, 0)

        row = grouped.setdefault(stat_key, {
            "check_by": check_main.check_by,
            "stat_time_type": time_type if req.stat_type == "TIME" else None,
            "stat_time": stat_key if req.stat_type == "TIME" else None,
            "pres_no": stat_key if req.stat_type == "PRES" else None,
            "pres_total": 0,
            "drug_total": 0,
            "qrcode_total": 0,
            "qualified_pres": 0,
            "error_total": 0,
            "handle_error": 0,
            "check_hours": 0.0,
            "update_time": datetime.utcnow().isoformat()
        })

        row["pres_total"] += 1
        row["drug_total"] += int(drug_total)
        row["qrcode_total"] += int(qrcode_total)
        row["error_total"] += int(error_total)
        row["qualified_pres"] += 1 if check_main.check_qualified == 1 else 0
        row["check_hours"] += float(check_hours)

    row_list = list(grouped.values())
    if req.stat_type == "TIME":
        row_list.sort(key=lambda item: item.get("stat_time") or "", reverse=True)
    elif req.stat_type == "PRES":
        row_list.sort(key=lambda item: item.get("pres_no") or "", reverse=True)
    else:
        row_list.sort(key=lambda item: item.get("check_by") or "")

    return row_list

@app.get("/zyfh/api/v1/stat/workload/query")
def query_workload_stat(req: schemas.WorkloadStatQueryRequest = Depends(),
                       db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询工作量统计"""
    page = max(req.page, 1)
    size = min(max(req.size, 1), 200)
    rows = build_workload_rows(req, db)
    total = len(rows)
    start = (page - 1) * size
    paged_rows = rows[start:start + size]

    for index, row in enumerate(paged_rows, start=start + 1):
        row["id"] = index

    return success_response({
        "total": total,
        "pages": (total + size - 1) // size,
        "page": page,
        "size": size,
        "list": paged_rows
    })

@app.post("/zyfh/api/v1/stat/report/generate")
def generate_stat_report(req: schemas.StatReportGenerateRequest,
                        db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """生成统计报告（含图表数据）"""
    try:
        start_date = datetime.strptime(req.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(req.end_date, "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        return error_response("1000", "日期格式错误，应为 YYYY-MM-DD")

    checks = db.query(models.DrugCheckMain).filter(
        models.DrugCheckMain.is_delete == 0,
        models.DrugCheckMain.check_start_time >= start_date,
        models.DrugCheckMain.check_start_time < end_date
    ).all()

    total_pres = len(checks)
    total_drugs = 0
    total_qrcode = 0
    total_qualified = 0
    total_errors = 0

    for check_main in checks:
        total_qrcode += db.query(func.count(models.DrugCheckDetail.id)).filter(
            models.DrugCheckDetail.check_main_id == check_main.id,
            models.DrugCheckDetail.is_delete == 0
        ).scalar() or 0
        total_drugs += db.query(func.count(func.distinct(models.DrugCheckDetail.cj_id))).filter(
            models.DrugCheckDetail.check_main_id == check_main.id,
            models.DrugCheckDetail.is_delete == 0
        ).scalar() or 0
        total_errors += db.query(func.count(models.CheckErrorRecord.id)).filter(
            models.CheckErrorRecord.pres_no == check_main.pres_no,
            models.CheckErrorRecord.is_delete == 0
        ).scalar() or 0
        total_qualified += 1 if check_main.check_qualified == 1 else 0

    qualified_rate = (total_qualified / total_pres * 100) if total_pres > 0 else 0

    report_id = f"STAT{int(time.time())}"
    report_filename = f"{report_id}.json"
    report_path = os.path.join(REPORT_DIR, report_filename)
    report_content = {
        "report_id": report_id,
        "report_type": req.report_type,
        "period": f"{req.start_date} - {req.end_date}",
        "total_prescriptions": total_pres,
        "total_drugs": total_drugs,
        "total_qrcode": total_qrcode,
        "total_qualified": total_qualified,
        "total_errors": total_errors,
        "qualified_rate": round(qualified_rate, 2),
        "generated_by": current_user.user_account,
        "generated_time": datetime.utcnow().isoformat()
    }

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report_content, file, ensure_ascii=False, indent=2)

    return success_response({
        "report_id": report_id,
        "period": f"{req.start_date} - {req.end_date}",
        "total_prescriptions": total_pres,
        "total_drugs": total_drugs,
        "total_qrcode": total_qrcode,
        "total_qualified": total_qualified,
        "total_errors": total_errors,
        "qualified_rate": round(qualified_rate, 2),
        "download_url": f"http://localhost:8000/zyfh/reports/{report_filename}",
        "status": "generated"
    })

# ========== 系统管理模块 ==========

@app.get("/zyfh/api/v1/sys/user/profile/get")
def get_user_profile(current_user=Depends(get_current_user)):
    """获取当前登录用户个人信息"""
    return success_response({
        "id": current_user.id,
        "user_account": current_user.user_account,
        "user_name": current_user.user_name,
        "dept_name": current_user.dept_name,
        "post": current_user.post,
        "phone": current_user.phone,
        "status": current_user.status,
        "login_time": current_user.login_time.isoformat() if current_user.login_time else None
    })


@app.put("/zyfh/api/v1/sys/user/profile/update")
def update_user_profile(req: schemas.UserProfileUpdateRequest,
                        db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """更新当前登录用户个人信息"""
    current_user.user_name = req.user_name
    current_user.dept_name = req.dept_name
    current_user.post = req.post
    current_user.phone = req.phone
    current_user.update_by = current_user.user_account
    current_user.update_time = datetime.utcnow()
    db.commit()

    return success_response({
        "user_account": current_user.user_account,
        "status": "updated"
    })


@app.put("/zyfh/api/v1/sys/user/password/update")
def update_user_password(req: schemas.UserPasswordUpdateRequest,
                         db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """更新当前登录用户密码"""
    if current_user.user_pwd != hash_password(req.old_password):
        return error_response("2000", "原密码不正确")

    if req.old_password == req.new_password:
        return error_response("1000", "新密码不能与原密码相同")

    current_user.user_pwd = hash_password(req.new_password)
    current_user.update_by = current_user.user_account
    current_user.update_time = datetime.utcnow()
    db.commit()

    return success_response({"status": "updated"}, "密码更新成功")

@app.post("/zyfh/api/v1/sys/user/save")
def save_user(req: schemas.UserCreateRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """新增/编辑用户"""
    existing = db.query(models.SysUser).filter(
        models.SysUser.user_account == req.user_account,
        models.SysUser.is_delete == 0
    ).first()
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
    query = db.query(models.SysUser).filter(models.SysUser.is_delete == 0)
    
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
def delete_user(id: int, operate_by: str = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """系统用户删除（逻辑删除）"""
    user = db.query(models.SysUser).filter(
        models.SysUser.id == id,
        models.SysUser.is_delete == 0
    ).first()
    if not user:
        return error_response("5000", "用户不存在")
    
    user.is_delete = 1
    user.update_by = operate_by or current_user.user_account
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
    existing = db.query(models.SysRole).filter(
        models.SysRole.role_code == req.role_code,
        models.SysRole.is_delete == 0
    ).first()
    if existing:
        existing.role_name = req.role_name
        existing.role_permission = req.role_permission
        existing.role_desc = req.role_desc
        existing.status = req.status
        existing.update_time = datetime.utcnow()
    else:
        role = models.SysRole(
            role_code=req.role_code,
            role_name=req.role_name,
            role_permission=req.role_permission,
            role_desc=req.role_desc,
            status=req.status
        )
        db.add(role)
    
    db.commit()
    return success_response({"role_code": req.role_code, "status": "saved"})

@app.get("/zyfh/api/v1/sys/role/list")
def list_roles(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """查询角色列表"""
    roles = db.query(models.SysRole).filter(models.SysRole.is_delete == 0).order_by(desc(models.SysRole.create_time)).limit(100).all()
    
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


@app.delete("/zyfh/api/v1/sys/role/delete")
def delete_role(id: int, operate_by: str = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """系统角色删除（逻辑删除）"""
    role = db.query(models.SysRole).filter(
        models.SysRole.id == id,
        models.SysRole.is_delete == 0
    ).first()

    if not role:
        return error_response("5000", "角色不存在")

    role.is_delete = 1
    role.update_time = datetime.utcnow()

    user_roles = db.query(models.SysUserRole).filter(
        models.SysUserRole.role_id == id,
        models.SysUserRole.is_delete == 0
    ).all()
    for user_role in user_roles:
        user_role.is_delete = 1

    db.commit()
    return success_response({
        "role_id": id,
        "operate_by": operate_by or current_user.user_account,
        "status": "deleted"
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
            role_id=role_id
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
        existing.update_time = datetime.utcnow()
    else:
        device = models.SysDeviceManage(
            device_no=req.device_no,
            device_name=req.device_name,
            device_type=req.device_type,  # SCAN-扫码枪, PAD-平板, PRINT-打印机, CAM-摄像头
            bind_station=req.bind_station,
            bind_user=req.bind_user,
            device_status="ONLINE"
        )
        db.add(device)
    
    db.commit()
    return success_response({"device_no": req.device_no, "status": "saved"})

@app.post("/zyfh/api/v1/sys/base/drug/sync/his")
def sync_his_drug_base(req: schemas.DrugSyncHISRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """院内药品基础数据同步（从HIS）"""
    # Mock 实现，实际应调用HIS系统接口
    success_count = 0
    fail_count = 0

    if req.sync_type == "ALL":
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

    elif req.sync_type == "UPDATE":
        # 增量更新：仅同步HIS中新增/修改的药品数据
        # 在实际应用中，这里会调用HIS系统的接口获取增量数据
        success_count = 0  # Mock 没有增量数据
    else:
        return error_response("1000", "同步类型错误，应为ALL或UPDATE")

    db.commit()

    return success_response({
        "syncType": req.sync_type,
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
                "device_code": d.device_no,
                "device_name": d.device_name,
                "device_type": d.device_type,
                "bind_station": d.bind_station,
                "bind_user": d.bind_user,
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
                "operate_module": l.operate_module,
                "operate_type": l.operate_type,
                "operate_by": l.operate_user,
                "operate_time": l.operate_time.timestamp() if l.operate_time else None,
                "ip_address": l.operate_ip,
                "operate_content": l.operate_desc
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
    config = db.query(models.SysParamConfig).filter(models.SysParamConfig.param_key == req.param_key).first()
    if config:
        config.param_value = req.param_value
        config.param_desc = req.param_desc
        config.update_by = req.operate_by or current_user.user_account
        config.update_time = datetime.utcnow()
        config.is_delete = 0
    else:
        config = models.SysParamConfig(
            param_key=req.param_key,
            param_value=req.param_value,
            param_desc=req.param_desc,
            update_by=req.operate_by or current_user.user_account,
            update_time=datetime.utcnow()
        )
        db.add(config)

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
    predefined_params = {
        "offline_cache_time": {"value": "72", "desc": "离线缓存时长（小时）"},
        "auto_save_progress": {"value": "30", "desc": "自动保存进度时间（分钟）"},
        "qrcode_dpi": {"value": "300", "desc": "二维码生成分辨率（dpi）"},
        "token_expire_hour": {"value": "24", "desc": "Token有效期（小时）"},
        "video_valid_hour": {"value": "24", "desc": "视频地址有效时长（小时）"}
    }

    if db.query(models.SysParamConfig).count() == 0:
        for key, value in predefined_params.items():
            db.add(models.SysParamConfig(
                param_key=key,
                param_value=value["value"],
                param_desc=value["desc"],
                update_by=current_user.user_account,
                update_time=datetime.utcnow(),
                is_delete=0
            ))
        db.commit()

    query = db.query(models.SysParamConfig).filter(models.SysParamConfig.is_delete == 0)
    if param_key:
        query = query.filter(models.SysParamConfig.param_key == param_key)

    rows = query.order_by(models.SysParamConfig.param_key).all()
    result = [
        {
            "param_key": row.param_key,
            "param_value": row.param_value,
            "param_desc": row.param_desc,
            "update_by": row.update_by,
            "update_time": row.update_time.isoformat() if row.update_time else None
        }
        for row in rows
    ]
    
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

    backup_path = f"/data/backup/{datetime.utcnow().strftime('%Y/%m/%d')}/{req.backup_type.lower()}/"
    backup_status = "SUCCESS"

    record = models.SysDataBackup(
        backup_id=backup_id,
        backup_type=req.backup_type,
        backup_path=backup_path,
        backup_status=backup_status,
        trigger_by=req.operate_by or current_user.user_account,
        backup_time=datetime.utcnow(),
        backup_desc=req.backup_desc,
        backup_size="0MB",
        is_delete=0
    )
    db.add(record)

    backup_info = {
        "backup_id": backup_id,
        "backup_path": backup_path,
        "backup_time": datetime.utcnow().isoformat(),
        "backup_status": backup_status,  # RUNNING, SUCCESS, FAIL
        "backup_type": req.backup_type,
        "backup_desc": req.backup_desc
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
                       page: int = 1, size: int = 20,
                       db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """数据备份记录查询"""
    query = db.query(models.SysDataBackup).filter(models.SysDataBackup.is_delete == 0)

    if backup_type:
        query = query.filter(models.SysDataBackup.backup_type == backup_type)
    if backup_status:
        query = query.filter(models.SysDataBackup.backup_status == backup_status)
    if start_time and end_time:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        query = query.filter(models.SysDataBackup.backup_time.between(start_dt, end_dt))

    total = query.count()
    page = max(page, 1)
    size = min(max(size, 1), 200)
    rows = query.order_by(desc(models.SysDataBackup.backup_time)).offset((page - 1) * size).limit(size).all()

    return success_response({
        "total": total,
        "pages": (total + size - 1) // size,
        "page": page,
        "size": size,
        "list": [
            {
                "backup_id": item.backup_id,
                "backup_type": item.backup_type,
                "backup_path": item.backup_path,
                "backup_status": item.backup_status,
                "trigger_by": item.trigger_by,
                "backup_time": item.backup_time.isoformat() if item.backup_time else None,
                "backup_size": item.backup_size,
                "backup_desc": item.backup_desc
            }
            for item in rows
        ]
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
                current_basket = ""
                finished_count = 0
                unfinished_count = 0
                try:
                    progress_dict = json.loads(progress_json.replace("'", '"'))
                    current_basket = progress_dict.get("current_basket") or progress_dict.get("currentBasket") or ""
                    finished_list = progress_dict.get("finished_drugs") or progress_dict.get("finished") or []
                    unfinished_list = progress_dict.get("unfinished_drugs") or progress_dict.get("unfinished") or []
                    finished_count = len(finished_list)
                    unfinished_count = len(unfinished_list)
                except Exception:
                    pass

                # 创建新进度记录
                progress = models.DrugCheckProgress(
                    check_main_id=check_main.id,
                    pres_no=record[1],  # pres_no
                    finished_drug=finished_count,
                    unfinish_drug=unfinished_count,
                    current_basket=current_basket or "UNKNOWN",
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
