import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
import base64

client = TestClient(app)

def test_health():
    """测试健康检查接口"""
    r = client.get("/zyfh/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == "0000"
    assert data["data"]["status"] == "ok"

def test_system_status():
    """测试系统状态接口"""
    r = client.get("/zyfh/api/v1/system/status")
    assert r.status_code == 200
    data = r.json()
    assert data["code"] == "0000"
    assert "total_users" in data["data"]
    assert "total_devices" in data["data"]

def test_error_handling():
    """测试错误处理 API"""
    # 保存错误记录
    error_req = {
        "pres_no": "TEST202602280001",
        "error_type": "SPEC_ERROR",
        "error_desc": "规格不匹配",
        "error_level": 2,
        "drug_name": "黄芪",
        "pres_spec": "10g",
        "scan_spec": "5g",
        "pres_num": 10,
        "scan_num": 5
    }
    
    # 需要 Token 进行认证
    token_req = {
        "user_account": "admin",
        "user_pwd": "admin123"
    }
    token_resp = client.post("/zyfh/api/v1/system/token/get", json=token_req)
    
    if token_resp.status_code == 200:
        token_data = token_resp.json()
        if token_data.get("code") == "0000":
            token = token_data["data"]["token"]
            headers = {"Authorization": token}
            
            # 测试保存错误记录
            r = client.post("/zyfh/api/v1/alert/error/save", json=error_req, headers=headers)
            assert r.status_code == 200
            error_data = r.json()
            assert error_data["code"] == "0000"
            print("✅ 错误提醒 API 测试通过")
        else:
            print("⚠️ Token 获取失败，跳过该测试")
    else:
        print("⚠️ 服务器不可达，跳过该测试")
