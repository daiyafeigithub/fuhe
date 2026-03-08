from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# ===== 基础配置表 =====

class Enterprise(Base):
    __tablename__ = "base_enterprise"
    id = Column(Integer, primary_key=True)
    enterprise_code = Column(Integer, unique=True, nullable=False)
    enterprise_name = Column(String(100), nullable=False)
    status = Column(Integer, default=1)
    create_by = Column(String(20), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_by = Column(String(20))
    update_time = Column(DateTime)
    is_delete = Column(Integer, default=0)

class DrugInfo(Base):
    __tablename__ = "base_drug_info"
    id = Column(Integer, primary_key=True)
    cj_id = Column(String(20), unique=True, nullable=False)
    drug_name = Column(String(50), nullable=False)
    drug_type = Column(String(30))
    spec_range = Column(String(50))
    his_sync_time = Column(DateTime, nullable=False)
    status = Column(Integer, default=1)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime)
    is_delete = Column(Integer, default=0)
    ext1 = Column(String(50))
    ext2 = Column(String(50))


class TCMMedicineDict(Base):
    __tablename__ = "tcm_medicine_dict"
    id = Column(Integer, primary_key=True)
    medicine_name = Column(String(100), nullable=False)
    cjid = Column(Integer, unique=True, nullable=False)
    product_code = Column(String(50))
    specification = Column(String(50))
    unit = Column(String(20), default="包")
    status = Column(Integer, default=1)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)

# ===== 二维码管理表 =====

class QRCodeGenerate(Base):
    __tablename__ = "qrcode_generate_record"
    id = Column(Integer, primary_key=True)
    qrcode_id = Column(String(30), unique=True, nullable=False)
    enterprise_code = Column(Integer, nullable=False)
    cj_id = Column(String(20), nullable=False)
    spec = Column(String(10), nullable=False)
    batch_no = Column(String(10), nullable=False)
    num = Column(Integer, default=7)
    weight = Column(Numeric(8, 4), nullable=False)
    qrcode_origin = Column(String(200), nullable=False)
    base64_str = Column(Text, nullable=False)
    trace_url = Column(String(500))
    qrcode_url = Column(String(255), nullable=False)
    generate_by = Column(String(20), nullable=False)
    generate_time = Column(DateTime, default=datetime.utcnow)
    is_delete = Column(Integer, default=0)

class QRCodeVerify(Base):
    __tablename__ = "qrcode_verify_record"
    id = Column(Integer, primary_key=True)
    qrcode_id = Column(String(30), nullable=False)
    verify_base64 = Column(Text, nullable=False)
    decrypt_origin = Column(String(200), nullable=False)
    verify_result = Column(String(10), nullable=False)
    verify_reason = Column(String(200))
    verify_by = Column(String(20), nullable=False)
    verify_time = Column(DateTime, default=datetime.utcnow)
    is_delete = Column(Integer, default=0)

# ===== 扫码复核表 =====

class HISPrescription(Base):
    __tablename__ = "his_prescription_sync"
    id = Column(Integer, primary_key=True)
    pres_no = Column(String(30), unique=True, nullable=False)
    patient_name = Column(String(20), nullable=False)
    patient_id = Column(String(30))
    dept_name = Column(String(30), nullable=False)
    doc_name = Column(String(20), nullable=False)
    pres_time = Column(DateTime, nullable=False)
    drug_total = Column(Integer, nullable=False)
    sync_time = Column(DateTime, default=datetime.utcnow)
    pres_status = Column(Integer, default=1)
    is_delete = Column(Integer, default=0)

class DrugCheckMain(Base):
    __tablename__ = "drug_check_main"
    id = Column(Integer, primary_key=True)
    pres_no = Column(String(30), unique=True, nullable=False)
    check_by = Column(String(20), nullable=False)
    check_station = Column(String(10), nullable=False)
    check_start_time = Column(DateTime, default=datetime.utcnow)
    check_end_time = Column(DateTime)
    check_status = Column(Integer, default=1)
    check_qualified = Column(Integer)
    error_total = Column(Integer, default=0)
    submit_by = Column(String(20))
    submit_time = Column(DateTime)
    is_delete = Column(Integer, default=0)

class DrugCheckDetail(Base):
    __tablename__ = "drug_check_detail"
    id = Column(Integer, primary_key=True)
    check_main_id = Column(Integer, nullable=False)
    pres_no = Column(String(30), nullable=False)
    cj_id = Column(String(20), nullable=False)
    drug_name = Column(String(50), nullable=False)
    spec = Column(String(10), nullable=False)
    pres_num = Column(Integer, nullable=False)
    qrcode_id = Column(String(30), nullable=False)
    scan_spec = Column(String(10), nullable=False)
    scan_num = Column(Integer, nullable=False)
    scan_time = Column(DateTime, default=datetime.utcnow)
    basket_no = Column(String(20), nullable=False)
    scan_result = Column(Integer, default=0)
    is_check = Column(Integer, default=0)
    is_delete = Column(Integer, default=0)

class DrugCheckProgress(Base):
    __tablename__ = "drug_check_progress"
    id = Column(Integer, primary_key=True)
    check_main_id = Column(Integer, unique=True, nullable=False)
    pres_no = Column(String(30), nullable=False)
    finished_drug = Column(Integer, default=0)
    unfinish_drug = Column(Integer, default=0)
    current_basket = Column(String(20), nullable=False)
    progress_json = Column(Text, nullable=False)
    save_by = Column(String(20), nullable=False)
    save_time = Column(DateTime, default=datetime.utcnow)
    is_delete = Column(Integer, default=0)

# ===== 分筐复核表 =====

class BasketManage(Base):
    __tablename__ = "basket_manage"
    id = Column(Integer, primary_key=True)
    basket_no = Column(String(20), unique=True, nullable=False)
    basket_name = Column(String(50))
    create_type = Column(Integer, default=1)
    status = Column(Integer, default=1)
    create_by = Column(String(20), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    is_delete = Column(Integer, default=0)

class PresBasketRelation(Base):
    __tablename__ = "pres_basket_relation"
    id = Column(Integer, primary_key=True)
    pres_no = Column(String(30), nullable=False)
    check_main_id = Column(Integer, nullable=False)
    basket_no = Column(String(20), nullable=False)
    cj_id = Column(String(20), nullable=False)
    drug_name = Column(String(50))
    basket_drug_num = Column(Integer, nullable=False)
    basket_status = Column(Integer, default=1)
    create_by = Column(String(20), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    is_delete = Column(Integer, default=0)

# ===== 错误提醒表 =====

class CheckErrorRecord(Base):
    __tablename__ = "check_error_record"
    id = Column(Integer, primary_key=True)
    check_detail_id = Column(Integer, unique=True, nullable=False)
    check_main_id = Column(Integer, nullable=False)
    pres_no = Column(String(30), nullable=False)
    cj_id = Column(String(20), nullable=False)
    error_type = Column(String(20), nullable=False)  # DRUG_ERROR-药品错误, NUM_ERROR-数量错误
    error_desc = Column(String(200), nullable=False)
    pres_standard = Column(String(50), nullable=False)
    scan_actual = Column(String(50), nullable=False)
    error_time = Column(DateTime, default=datetime.utcnow)
    error_status = Column(Integer, default=1)  # 1-未处理 2-已处理
    is_delete = Column(Integer, default=0)
    drug_name = Column(String(50))  # 药品名称（冗余）
    pres_spec = Column(String(10))  # 处方规格（冗余）
    scan_spec = Column(String(10))  # 扫码规格（冗余）
    pres_num = Column(Integer)  # 处方数量（冗余）
    scan_num = Column(Integer)  # 扫码数量（冗余）
    error_by = Column(String(20))  # 错误人账号
    handle_type = Column(String(20))  # 处理类型
    handle_by = Column(String(20))  # 处理人账号
    __table_args__ = (
        Index('idx_pres_no', 'pres_no'),
        Index('idx_error_type', 'error_type'),
        Index('idx_error_status', 'error_status'),
    )

class CheckErrorHandle(Base):
    __tablename__ = "check_error_handle"
    id = Column(Integer, primary_key=True)
    error_id = Column(Integer, unique=True, nullable=False)  # 根据文档应该是外键关联错误记录
    check_detail_id = Column(Integer, nullable=False)
    pres_no = Column(String(30), nullable=False)
    handle_type = Column(String(20), nullable=False)  # 根据文档是 VARCHAR(20)
    handle_desc = Column(String(200), nullable=False)
    handle_by = Column(String(20), nullable=False)
    handle_time = Column(DateTime, default=datetime.utcnow)
    is_delete = Column(Integer, default=0)

# ===== 溯源管理表 =====

class CheckOperateRecord(Base):
    __tablename__ = "check_operate_record"
    id = Column(Integer, primary_key=True)
    pres_no = Column(String(30))  # 可以为 NULL
    check_main_id = Column(Integer)  # 可以为 NULL
    operate_user = Column(String(20), nullable=False)
    operate_module = Column(String(20), nullable=False)  # 根据文档是 VARCHAR(20)
    operate_type = Column(String(20), nullable=False)  # 根据文档是 VARCHAR(20)
    operate_desc = Column(String(200), nullable=False)  # 根据文档是 VARCHAR(200)
    operate_time = Column(DateTime, default=datetime.utcnow)
    operate_ip = Column(String(20))  # 可以为 NULL
    is_delete = Column(Integer, default=0)

class VideoMonitorLink(Base):
    __tablename__ = "video_monitor_link"
    id = Column(Integer, primary_key=True)
    check_detail_id = Column(Integer, unique=True, nullable=False)
    pres_no = Column(String(30), nullable=False)
    scan_time = Column(DateTime, nullable=False)  # 根据文档是 DATETIME
    check_station = Column(String(10), nullable=False)  # 根据文档是 VARCHAR(10)
    camera_no = Column(String(20), nullable=False)  # 根据文档是 VARCHAR(20)
    video_url = Column(String(255), nullable=False)  # 根据文档是 VARCHAR(255)
    video_download = Column(String(255), nullable=False)  # 根据文档是 VARCHAR(255)
    video_snapshot = Column(String(255), nullable=False)  # 根据文档是 VARCHAR(255)
    video_valid_time = Column(DateTime, nullable=False)  # 根据文档是 DATETIME
    is_delete = Column(Integer, default=0)

# ===== 工作量统计表 =====

class CheckWorkloadStat(Base):
    __tablename__ = "check_workload_stat"
    id = Column(Integer, primary_key=True)
    check_by = Column(String(20), nullable=False)  # 复核人员账号
    stat_time_type = Column(String(10), nullable=False)  # DAY/WEEK/MONTH/YEAR
    stat_time = Column(String(20), nullable=False)  # 如 2026-02-28
    stat_date = Column(DateTime, default=datetime.utcnow)  # 统计时间
    pres_total = Column(Integer, default=0)  # 复核处方总数
    drug_total = Column(Integer, default=0)  # 复核饮片总品种数
    qrcode_total = Column(Integer, default=0)  # 扫码总次数
    qualified_pres = Column(Integer, default=0)  # 合格处方数
    error_total = Column(Integer, default=0)  # 复核错误总数
    handle_error = Column(Integer, default=0)  # 处理错误总数
    qualified_total = Column(Integer, default=0)  # 合格总数（冗余字段）
    check_hours = Column(Numeric(5, 2))  # 复核总时长（小时）
    update_time = Column(DateTime, default=datetime.utcnow)
    is_delete = Column(Integer, default=0)
    __table_args__ = (
        Index('idx_user_stat', 'check_by', 'stat_time_type', 'stat_time'),
        Index('idx_stat_time', 'stat_time'),
    )

# ===== 系统基础表 =====

class SysUser(Base):
    __tablename__ = "sys_user"
    id = Column(Integer, primary_key=True)
    user_account = Column(String(20), unique=True, nullable=False)
    user_pwd = Column(String(64), nullable=False)  # MD5加密存储
    user_name = Column(String(20), nullable=False)
    dept_name = Column(String(30), nullable=False)
    post = Column(String(20), nullable=False)  # 岗位
    phone = Column(String(11))  # 联系电话
    status = Column(Integer, default=1)  # 状态：1-启用 0-禁用
    login_time = Column(DateTime)  # 最后登录时间
    login_ip = Column(String(20))  # 最后登录IP
    create_by = Column(String(20), nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_by = Column(String(20))  # 根据文档应该有更新人
    update_time = Column(DateTime)  # 根据文档应该有更新时间
    is_delete = Column(Integer, default=0)

class SysRole(Base):
    __tablename__ = "sys_role"
    id = Column(Integer, primary_key=True)
    role_code = Column(String(20), unique=True, nullable=False)  # 角色编码，唯一
    role_name = Column(String(20), nullable=False)  # 角色名称
    role_permission = Column(Text, nullable=False)  # 权限标识集合，逗号分隔
    role_desc = Column(String(100))  # 角色描述
    status = Column(Integer, default=1)  # 状态：1-启用 0-禁用
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime)  # 根据文档应该有更新时间
    is_delete = Column(Integer, default=0)

class SysUserRole(Base):
    __tablename__ = "sys_user_role"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    role_id = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    is_delete = Column(Integer, default=0)

class SysDeviceManage(Base):
    __tablename__ = "sys_device_manage"
    id = Column(Integer, primary_key=True)
    device_no = Column(String(30), unique=True, nullable=False)  # 设备编号，唯一
    device_type = Column(String(20), nullable=False)  # 设备类型：SCAN-扫码枪 PAD-平板 PRINT-打印机 CAM-摄像头
    device_name = Column(String(50), nullable=False)  # 设备名称/型号
    bind_station = Column(String(10))  # 绑定复核台编号
    bind_user = Column(String(20))  # 绑定人员账号
    device_status = Column(String(10), default='ONLINE')  # 设备状态：ONLINE-在线 OFFLINE-离线 FAULT-故障
    last_use_time = Column(DateTime)  # 最后使用时间
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime)  # 根据文档应该有更新时间
    is_delete = Column(Integer, default=0)

class SysParamConfig(Base):
    __tablename__ = "sys_param_config"
    id = Column(Integer, primary_key=True)
    param_key = Column(String(50), unique=True, nullable=False)
    param_value = Column(String(200), nullable=False)
    param_desc = Column(String(200))
    update_by = Column(String(20), nullable=False)
    update_time = Column(DateTime, default=datetime.utcnow)
    is_delete = Column(Integer, default=0)

class SysDataBackup(Base):
    __tablename__ = "sys_data_backup"
    id = Column(Integer, primary_key=True)
    backup_id = Column(String(50), unique=True, nullable=False)
    backup_type = Column(String(20), nullable=False)
    backup_path = Column(String(255), nullable=False)
    backup_status = Column(String(20), nullable=False)
    trigger_by = Column(String(20), nullable=False)
    backup_time = Column(DateTime, default=datetime.utcnow)
    backup_desc = Column(String(200))
    backup_size = Column(String(50))
    is_delete = Column(Integer, default=0)
