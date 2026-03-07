from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# ====== Token & Auth ======
class TokenRequest(BaseModel):
    user_account: str
    user_pwd: str

class TokenResponse(BaseModel):
    token: str
    expire_time: int
    user_info: Dict

# ====== QR Code Management ======
class QRGenerateRequest(BaseModel):
    enterprise_code: int
    cj_id: str
    spec: str
    batch_no: str
    num: int = 7
    weight: float

class QRGenerateResponse(BaseModel):
    qrcode_id: str
    qrcode_content: str
    base64_str: str
    qrcode_url: str

class QRParseResponse(BaseModel):
    qrcode_id: str
    enterprise_code: int
    cj_id: str
    spec: str
    batch_no: str
    num: int
    weight: float

class QRVerifyResponse(BaseModel):
    decrypt_content: str
    verify_result: str  # SUCCESS, FAIL, NOT_FOUND, OFFLINE
    verify_reason: Optional[str] = None

# ====== HIS Integration ======
class DrugItem(BaseModel):
    cj_id: str
    drug_name: str
    spec: str
    num: int
    usage: str

class HISPrescriptionSyncRequest(BaseModel):
    pres_no: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class HISPrescriptionResponse(BaseModel):
    pres_no: str
    patient_name: str
    patient_id: Optional[str] = None
    dept_name: str
    doc_name: str
    pres_time: str
    drugs: List[DrugItem]
    status: str

# ====== Check Workflow ======
class CheckInitRequest(BaseModel):
    pres_no: str
    check_by: str
    check_station: str

class ScanCheckRequest(BaseModel):
    pres_no: str
    basket_no: str
    qrcode_content: str
    check_by: str

class CheckProgressSaveRequest(BaseModel):
    pres_no: str
    check_by: str
    finished_drugs: List[str]
    unfinished_drugs: List[str]
    current_basket: str

class CheckSubmitRequest(BaseModel):
    pres_no: str
    check_by: str

# ====== Basket Management ======
class BasketCreateRequest(BaseModel):
    basket_no: str
    basket_name: Optional[str] = None
    create_by: str
    status: Optional[int] = 1

class BasketDisableRequest(BaseModel):
    basket_no: str
    operate_by: Optional[str] = None

class BasketDrugRelationRequest(BaseModel):
    pres_no: str
    basket_no: str
    cj_id_list: List[str]
    create_by: Optional[str] = None
    check_main_id: Optional[int] = None

class BasketCheckConfirmRequest(BaseModel):
    pres_no: str
    basket_no: str
    confirm_by: str

# ====== Error Alert ======
class ErrorHandleRequest(BaseModel):
    error_id: str
    handle_by: str
    handle_result: str  # REPLACE, ADD, CANCEL
    handle_desc: Optional[str] = None

# ====== Traceability ======
class TraceRecordQueryRequest(BaseModel):
    pres_no: Optional[str] = None
    basket_no: Optional[str] = None
    cj_id: Optional[str] = None
    batch_no: Optional[str] = None
    check_by: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    page: int = 1
    size: int = 20

# ====== Workload Statistics ======
class WorkloadStatQueryRequest(BaseModel):
    stat_type: str  # USER, TIME, PRES
    check_by: Optional[str] = None
    time_type: Optional[str] = None
    stat_time: Optional[str] = None
    page: int = 1
    size: int = 20

# ====== System Management ======
class UserCreateRequest(BaseModel):
    user_account: str
    user_pwd: str
    user_name: str
    dept_name: str
    post: str
    phone: Optional[str] = None
    status: int = 1

class RoleCreateRequest(BaseModel):
    role_code: str
    role_name: str
    role_permission: str
    role_desc: Optional[str] = None
    status: int = 1

class UserRoleBindRequest(BaseModel):
    user_id: int
    role_id_list: List[int]
    operate_by: str

class DeviceRegisterRequest(BaseModel):
    device_no: str
    device_type: str
    device_name: str
    bind_station: Optional[str] = None
    bind_user: Optional[str] = None


class UserProfileUpdateRequest(BaseModel):
    user_name: str
    dept_name: str
    post: str
    phone: Optional[str] = None


class UserPasswordUpdateRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=32)

# ====== Enterprise Management ======
class EnterpriseSaveRequest(BaseModel):
    code: int
    name: str
    status: int = 1

# ====== Trace Report ======
class TraceReportGenerateRequest(BaseModel):
    pres_no: Optional[str] = None
    pres_no_list: Optional[List[str]] = None

# ====== Stat Report ======
class StatReportGenerateRequest(BaseModel):
    start_date: str
    end_date: str
    report_type: str = "detailed"

# ====== Drug Sync ======
class DrugSyncHISRequest(BaseModel):
    sync_type: str
    operate_by: str

# ====== Universal Response ======
class ApiResponse(BaseModel):
    code: str
    msg: str
    data: Optional[Dict] = None
    timestamp: int
    requestId: str

class PageResponse(BaseModel):
    total: int
    pages: int
    page: int
    size: int
    list: List[Dict]
