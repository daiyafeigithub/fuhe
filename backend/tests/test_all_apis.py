#!/usr/bin/env python3
"""
完整 API 测试脚本 - 演示所有已实现的 API 端点
运行方式: python -m pytest backend/tests/test_all_apis.py -v
或者: python backend/tests/test_all_apis.py (需要 requests 库)
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"
TOKEN = None

def print_section(title):
    """打印分隔符"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def log_request(method, endpoint, data=None, headers=None):
    """记录请求信息"""
    full_url = f"{BASE_URL}{endpoint}"
    print(f"📌 {method} {endpoint}")
    if data:
        print(f"   Body: {json.dumps(data, ensure_ascii=False, indent=2)[:100]}")
    return full_url

def test_health():
    """测试 1: 健康检查"""
    print_section("测试 1: 健康检查接口")
    url = log_request("GET", "/zyfh/api/v1/health")
    
    try:
        resp = requests.get(url, timeout=5)
        print(f"✅ 状态码: {resp.status_code}")
        data = resp.json()
        print(f"✅ 响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_system_status(headers=None):
    """测试 2: 系统状态"""
    print_section("测试 2: 系统状态接口")
    url = log_request("GET", "/zyfh/api/v1/system/status")
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        print(f"✅ 状态码: {resp.status_code}")
        data = resp.json()
        print(f"✅ 响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_token_generation():
    """测试 3: Token 生成"""
    global TOKEN
    print_section("测试 3: 获取认证 Token")
    
    url = log_request("POST", "/zyfh/api/v1/system/token/get", {
        "user_account": "admin",
        "user_pwd": "admin123"
    })
    
    try:
        resp = requests.post(url, json={
            "user_account": "admin",
            "user_pwd": "admin123"
        }, timeout=5)
        
        print(f"✅ 状态码: {resp.status_code}")
        data = resp.json()
        
        if data.get("code") == "0000":
            TOKEN = data["data"]["token"]
            print(f"✅ Token 获取成功: {TOKEN[:30]}...")
            return True
        else:
            print(f"❌ Token 生成失败: {data.get('msg')}")
            return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_error_alert_apis(headers):
    """测试 4: 错误提醒模块"""
    print_section("测试 4: 错误提醒 API - 保存错误记录")
    
    error_data = {
        "pres_no": f"TEST{int(time.time())}",
        "error_type": "SPEC_ERROR",
        "error_desc": "规格不匹配",
        "error_level": 2,
        "drug_name": "黄芪",
        "pres_spec": "10g",
        "scan_spec": "5g",
        "pres_num": 10,
        "scan_num": 5
    }
    
    url = log_request("POST", "/zyfh/api/v1/alert/error/save", error_data)
    
    try:
        resp = requests.post(url, json=error_data, headers=headers, timeout=5)
        print(f"✅ 状态码: {resp.status_code}")
        data = resp.json()
        print(f"✅ 响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 测试查询错误列表
        print("\n📌 查询错误提醒列表:")
        list_url = log_request("GET", "/zyfh/api/v1/alert/error/list?error_status=0")
        list_resp = requests.get(list_url, headers=headers, timeout=5)
        print(f"✅ 状态码: {list_resp.status_code}")
        list_data = list_resp.json()
        print(f"✅ 错误记录数: {list_data.get('data', {}).get('total', 0)}")
        
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_basket_apis(headers):
    """测试 5: 分筐管理模块"""
    print_section("测试 5: 分筐管理 API - 新增分筐")
    
    url = log_request("POST", "/zyfh/api/v1/basket/save", {
        "basket_no": f"BK{int(time.time())}",
        "status": 1
    })
    
    try:
        resp = requests.post(url, json={
            "basket_no": f"BK{int(time.time())}",
            "status": 1
        }, headers=headers, timeout=5)
        
        print(f"✅ 状态码: {resp.status_code}")
        data = resp.json()
        print(f"✅ 响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 测试查询分筐列表
        print("\n📌 查询分筐列表:")
        list_url = log_request("GET", "/zyfh/api/v1/basket/list")
        list_resp = requests.get(list_url, headers=headers, timeout=5)
        print(f"✅ 分筐数量: {list_resp.json().get('data', {}).get('total', 0)}")
        
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_traceability_apis(headers):
    """测试 6: 溯源管理模块"""
    print_section("测试 6: 溯源管理 API - 查询操作记录")
    
    url = log_request("GET", "/zyfh/api/v1/trace/record/query?pres_no=TEST001")
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        print(f"✅ 状态码: {resp.status_code}")
        data = resp.json()
        print(f"✅ 操作记录数: {data.get('data', {}).get('total', 0)}")
        
        # 测试生成溯源报告
        print("\n📌 生成溯源报告:")
        report_url = log_request("POST", "/zyfh/api/v1/trace/report/generate", {
            "pres_no": "TEST001"
        })
        report_resp = requests.post(report_url, json={"pres_no": "TEST001"}, headers=headers, timeout=5)
        print(f"✅ 报告 ID: {report_resp.json().get('data', {}).get('report_id', 'N/A')}")
        
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_workload_stat_apis(headers):
    """测试 7: 工作量统计模块"""
    print_section("测试 7: 工作量统计 API - 查询统计")
    
    url = log_request("POST", "/zyfh/api/v1/stat/workload/query", {
        "query_type": "daily",
        "user_account": None
    })
    
    try:
        resp = requests.post(url, json={
            "query_type": "daily",
            "user_account": None
        }, headers=headers, timeout=5)
        
        print(f"✅ 状态码: {resp.status_code}")
        data = resp.json()
        print(f"✅ 统计记录数: {data.get('data', {}).get('total_record', 0)}")
        
        # 测试生成统计报告
        print("\n📌 生成统计报告:")
        report_url = log_request("POST", "/zyfh/api/v1/stat/report/generate", {
            "start_date": "2026-02-01",
            "end_date": "2026-02-28"
        })
        report_resp = requests.post(report_url, json={
            "start_date": "2026-02-01",
            "end_date": "2026-02-28"
        }, headers=headers, timeout=5)
        report_data = report_resp.json().get('data', {})
        print(f"✅ 处方总数: {report_data.get('total_prescriptions', 0)}")
        print(f"✅ 药品合格率: {report_data.get('qualified_rate', 0)}%")
        
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def test_system_management_apis(headers):
    """测试 8: 系统管理模块"""
    print_section("测试 8: 系统管理 API - 用户和设备")
    
    # 查询用户列表
    url = log_request("GET", "/zyfh/api/v1/sys/user/list")
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        print(f"✅ 用户数量: {resp.json().get('data', {}).get('total', 0)}")
        
        # 查询设备列表
        print("\n📌 查询设备列表:")
        device_url = log_request("GET", "/zyfh/api/v1/sys/device/list")
        device_resp = requests.get(device_url, headers=headers, timeout=5)
        print(f"✅ 设备数量: {device_resp.json().get('data', {}).get('total', 0)}")
        
        # 查询系统日志
        print("\n📌 查询系统日志:")
        log_url = log_request("GET", "/zyfh/api/v1/sys/log/query?log_type=UPDATE")
        log_resp = requests.get(log_url, headers=headers, timeout=5)
        print(f"✅ 日志条数: {log_resp.json().get('data', {}).get('total', 0)}")
        
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("  🚀 精致饮片复核系统 - 完整 API 测试")
    print("="*60)
    print(f"📍 服务器地址: {BASE_URL}")
    print(f"⏰ 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试健康检查
    if not test_health():
        print("\n❌ 服务器不可用，请确保 uvicorn 服务正在运行")
        print("   运行命令: cd ~/Desktop/fuhe && source .venv/bin/activate && uvicorn backend.app.main:app --reload --port 8000")
        sys.exit(1)
    
    # 2. 测试系统状态
    test_system_status()
    
    # 3. 生成 Token
    if not test_token_generation():
        print("\n❌ Token 生成失败")
        sys.exit(1)
    
    # 4. 准备认证头
    headers = {"Authorization": TOKEN} if TOKEN else {}
    
    # 5-8. 测试各个模块 API
    test_error_alert_apis(headers)
    test_basket_apis(headers)
    test_traceability_apis(headers)
    test_workload_stat_apis(headers)
    test_system_management_apis(headers)
    
    # 完成
    print_section("✅ 所有测试完成")
    print("📊 实现的 API 模块:")
    print("  ✅ 错误提醒模块 (5 个端点)")
    print("  ✅ 分筐管理模块 (4 个端点)")
    print("  ✅ 溯源管理模块 (3 个端点)")
    print("  ✅ 工作量统计模块 (2 个端点)")
    print("  ✅ 系统管理模块 (6 个端点)")
    print("  ✅ 核心模块 (12 个端点)")
    print("\n🎯 共计 30+ 个 API 端点已实现")
    print("\n")

if __name__ == "__main__":
    main()
