#!/usr/bin/env python3
"""
API_GUIDE.md 完整接口测试脚本
测试所有接口是否能正确通过
"""

import requests
import json
import sys
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/zyfh/api/v1"

# 测试数据
TEST_DATA = {
    "user_account": "admin",
    "user_pwd": "admin123",
    "enterprise_code": 99,
    "enterprise_name": "测试企业",
    "pres_no": "CF20260303001",
    "basket_no": "K20260303001",
    "cj_id": "13310",
    "device_no": "TEST_DEVICE_001",
    "role_code": "TEST_ROLE",
}

class APITester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_data = {}  # 存储创建的数据ID

    def log(self, message, level="INFO"):
        """打印日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def make_request(self, method, endpoint, data=None, params=None, auth=True):
        """发送HTTP请求"""
        url = f"{BASE_URL}{API_PREFIX}{endpoint}"
        headers = self.headers.copy() if auth else {}

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=10)
            else:
                return None, f"不支持的HTTP方法: {method}"

            return response, None
        except requests.exceptions.ConnectionError:
            return None, "连接失败，请检查服务器是否运行"
        except requests.exceptions.Timeout:
            return None, "请求超时"
        except Exception as e:
            return None, f"请求异常: {str(e)}"

    def test_api(self, name, method, endpoint, data=None, params=None, auth=True, expected_code="0000"):
        """测试单个API"""
        self.log(f"测试: {name}")
        response, error = self.make_request(method, endpoint, data, params, auth)

        if error:
            self.log(f"  ❌ 失败: {error}", "ERROR")
            self.test_results.append({"name": name, "status": "FAILED", "error": error})
            return False, None

        try:
            result = response.json()
            actual_code = result.get("code", "")

            if actual_code == expected_code:
                self.log(f"  ✅ 通过 (HTTP {response.status_code})", "SUCCESS")
                self.test_results.append({"name": name, "status": "PASSED", "code": actual_code})
                return True, result
            else:
                error_msg = result.get("msg", "未知错误")
                self.log(f"  ❌ 失败: 返回码 {actual_code}, 消息: {error_msg}", "ERROR")
                self.test_results.append({"name": name, "status": "FAILED", "error": f"返回码 {actual_code}: {error_msg}"})
                return False, result
        except json.JSONDecodeError:
            self.log(f"  ❌ 失败: 无法解析JSON响应", "ERROR")
            self.test_results.append({"name": name, "status": "FAILED", "error": "JSON解析失败"})
            return False, None

    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 60)
        self.log("开始 API_GUIDE.md 完整接口测试")
        self.log("=" * 60)

        # ========== 1. 系统认证接口 ==========
        self.log("\n【一、系统认证接口】")

        # 1.1 健康检查 (不需要认证)
        self.test_api("健康检查", "GET", "/health", auth=False)

        # 1.2 获取Token
        success, result = self.test_api(
            "获取访问Token",
            "POST",
            "/system/token/get",
            {"user_account": TEST_DATA["user_account"], "user_pwd": TEST_DATA["user_pwd"]},
            auth=False
        )
        if success and result:
            self.token = result["data"].get("token", "")
            self.headers["Authorization"] = f"Bearer {self.token}"
            self.log(f"  获取到Token: {self.token[:30]}...")
        else:
            self.log("无法获取Token，终止测试", "ERROR")
            return

        # ========== 2. 二维码管理模块 ==========
        self.log("\n【二、二维码管理模块】")

        # 2.1 企业保存
        self.test_api(
            "新增/维护企业标志",
            "POST",
            "/qrcode/enterprise/save",
            {
                "code": TEST_DATA["enterprise_code"],
                "name": TEST_DATA["enterprise_name"],
                "status": 1
            }
        )

        # 2.2 二维码单条生成
        success, result = self.test_api(
            "二维码单条生成",
            "POST",
            "/qrcode/generate/single",
            {
                "enterprise_code": TEST_DATA["enterprise_code"],
                "cj_id": TEST_DATA["cj_id"],
                "spec": "5g",
                "batch_no": "2503050001",
                "num": 7,
                "weight": 0.035
            }
        )
        if success and result:
            self.created_data["qrcode_content"] = result["data"].get("qrcode_content", "")
            self.created_data["qrcode_base64"] = result["data"].get("base64_str", "")

        # 2.3 二维码解析
        if self.created_data.get("qrcode_base64"):
            self.test_api(
                "二维码解析",
                "POST",
                "/qrcode/parse",
                {"qrcode_string": self.created_data["qrcode_base64"]}
            )

        # 2.4 二维码校验
        if self.created_data.get("qrcode_base64"):
            self.test_api(
                "二维码校验",
                "POST",
                "/qrcode/verify",
                {
                    "qrcode_content": self.created_data["qrcode_base64"],
                    "verifyBy": TEST_DATA["user_account"]
                }
            )

        # 2.5 二维码历史记录查询
        self.test_api(
            "二维码历史记录查询",
            "GET",
            "/qrcode/record/query",
            params={"page": 1, "size": 10}
        )

        # ========== 3. 扫码复核模块 ==========
        self.log("\n【三、扫码复核模块】")

        # 3.1 HIS处方信息同步
        self.test_api(
            "HIS处方信息同步",
            "POST",
            "/check/his/sync",
            {"pres_no": TEST_DATA["pres_no"]}
        )

        # 3.2 扫码复核初始化
        self.test_api(
            "扫码复核初始化",
            "POST",
            "/check/init",
            {
                "pres_no": TEST_DATA["pres_no"],
                "check_by": TEST_DATA["user_account"],
                "check_station": "STATION_01"
            }
        )

        # 3.3 实时扫码复核
        if self.created_data.get("qrcode_base64"):
            self.test_api(
                "实时扫码复核",
                "POST",
                "/check/scan",
                {
                    "pres_no": TEST_DATA["pres_no"],
                    "basket_no": TEST_DATA["basket_no"],
                    "qrcode_content": self.created_data["qrcode_base64"],
                    "check_by": TEST_DATA["user_account"]
                }
            )

        # 3.4 复核进度保存
        self.test_api(
            "复核进度保存",
            "POST",
            "/check/progress/save",
            {
                "pres_no": TEST_DATA["pres_no"],
                "check_by": TEST_DATA["user_account"],
                "finished_drugs": [TEST_DATA["cj_id"]],
                "unfinished_drugs": [],
                "current_basket": TEST_DATA["basket_no"]
            }
        )

        # 3.5 复核完成提交
        self.test_api(
            "复核完成提交",
            "POST",
            "/check/submit",
            {
                "pres_no": TEST_DATA["pres_no"],
                "check_by": TEST_DATA["user_account"]
            }
        )

        # ========== 4. 错误提醒模块 ==========
        self.log("\n【四、错误提醒模块】")

        # 4.1 错误记录查询
        self.test_api(
            "错误记录查询",
            "GET",
            "/alert/error/list",
            params={"pres_no": TEST_DATA["pres_no"]}
        )

        # ========== 5. 分筐管理模块 ==========
        self.log("\n【五、分筐管理模块】")

        # 5.1 筐号新增/维护
        self.test_api(
            "筐号新增/维护",
            "POST",
            "/basket/save",
            {
                "basket_no": TEST_DATA["basket_no"],
                "basket_name": "测试筐",
                "status": 1,
                "create_by": TEST_DATA["user_account"]
            }
        )

        # 5.2 筐号列表查询
        self.test_api(
            "筐号列表查询",
            "GET",
            "/basket/list"
        )

        # 5.3 饮片分筐关联
        self.test_api(
            "饮片分筐关联",
            "POST",
            "/basket/relation/save",
            {
                "pres_no": TEST_DATA["pres_no"],
                "basket_no": TEST_DATA["basket_no"],
                "cj_id_list": [TEST_DATA["cj_id"]],
                "create_by": TEST_DATA["user_account"]
            }
        )

        # 5.4 分筐复核确认
        self.test_api(
            "分筐复核确认",
            "POST",
            "/basket/check/confirm",
            {
                "pres_no": TEST_DATA["pres_no"],
                "basket_no": TEST_DATA["basket_no"],
                "confirm_by": TEST_DATA["user_account"]
            }
        )

        # ========== 6. 溯源管理模块 ==========
        self.log("\n【六、溯源管理模块】")

        # 6.1 复核溯源记录查询
        self.test_api(
            "复核溯源记录查询",
            "GET",
            "/trace/record/query",
            params={"pres_no": TEST_DATA["pres_no"], "page": 1, "size": 10}
        )

        # 6.2 溯源报告生成
        self.test_api(
            "溯源报告生成",
            "POST",
            "/trace/report/generate",
            {"pres_no": TEST_DATA["pres_no"]}
        )

        # ========== 7. 工作量统计模块 ==========
        self.log("\n【七、工作量统计模块】")

        # 7.1 复核工作量统计
        self.test_api(
            "复核工作量统计",
            "GET",
            "/stat/workload/query",
            params={"stat_type": "USER", "page": 1, "size": 10}
        )

        # 7.2 统计报告生成
        self.test_api(
            "统计报告生成",
            "POST",
            "/stat/report/generate",
            {
                "start_date": "2026-03-01",
                "end_date": "2026-03-03",
                "report_type": "detailed"
            }
        )

        # ========== 8. 系统管理模块 ==========
        self.log("\n【八、系统管理模块】")

        # 8.1 系统用户查询
        self.test_api(
            "系统用户查询",
            "GET",
            "/sys/user/list",
            params={"page": 1, "size": 10}
        )

        # 8.2 系统用户新增/编辑
        success, result = self.test_api(
            "系统用户新增/编辑",
            "POST",
            "/sys/user/save",
            {
                "user_account": "testuser_api",
                "user_pwd": "test123",
                "user_name": "测试用户API",
                "dept_name": "测试科",
                "post": "测试员",
                "phone": "13800138000",
                "status": 1
            }
        )

        # 8.3 角色列表查询
        self.test_api(
            "角色列表查询",
            "GET",
            "/sys/role/list"
        )

        # 8.4 角色新增/编辑
        self.test_api(
            "角色新增/编辑",
            "POST",
            "/sys/role/save",
            {
                "role_code": TEST_DATA["role_code"],
                "role_name": "测试角色API",
                "role_permission": "TEST:*",
                "role_desc": "用于API测试的角色",
                "status": 1
            }
        )

        # 8.5 设备列表查询
        self.test_api(
            "设备列表查询",
            "GET",
            "/sys/device/list"
        )

        # 8.6 设备注册/更新
        self.test_api(
            "设备注册/更新",
            "POST",
            "/sys/device/save",
            {
                "device_no": TEST_DATA["device_no"],
                "device_type": "SCAN",
                "device_name": "测试扫码枪",
                "bind_station": "STATION_01",
                "bind_user": TEST_DATA["user_account"]
            }
        )

        # 8.7 院内药品基础数据同步
        self.test_api(
            "院内药品基础数据同步",
            "POST",
            "/sys/base/drug/sync/his",
            {
                "sync_type": "UPDATE",
                "operate_by": TEST_DATA["user_account"]
            }
        )

        # 8.8 系统日志查询
        self.test_api(
            "系统日志查询",
            "GET",
            "/sys/log/query"
        )

        # 8.9 系统参数查询
        self.test_api(
            "系统参数查询",
            "GET",
            "/sys/param/config/query"
        )

        # 8.10 系统参数配置
        self.test_api(
            "系统参数配置",
            "POST",
            "/sys/param/config/save",
            {
                "param_key": "test_param",
                "param_value": "test_value",
                "param_desc": "测试参数",
                "operate_by": TEST_DATA["user_account"]
            }
        )

        # 8.11 数据备份记录查询
        self.test_api(
            "数据备份记录查询",
            "GET",
            "/sys/data/backup/record/query"
        )

        # 8.12 数据备份手动触发
        self.test_api(
            "数据备份手动触发",
            "POST",
            "/sys/data/backup/trigger",
            {
                "backup_type": "FULL",
                "backup_desc": "API测试备份",
                "operate_by": TEST_DATA["user_account"]
            }
        )

        # ========== 9. 离线数据同步 ==========
        self.log("\n【九、离线数据同步】")

        # 9.1 离线数据同步
        self.test_api(
            "离线数据同步",
            "POST",
            "/system/offline/sync",
            {
                "scan_records": [],
                "progress_records": [],
                "submit_records": []
            }
        )

        # ========== 测试报告 ==========
        self.print_report()

    def print_report(self):
        """打印测试报告"""
        self.log("\n" + "=" * 60)
        self.log("测试报告")
        self.log("=" * 60)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results if r["status"] == "FAILED")

        self.log(f"\n总计: {total} 个接口")
        self.log(f"通过: {passed} 个")
        self.log(f"失败: {failed} 个")
        self.log(f"通过率: {passed/total*100:.1f}%" if total > 0 else "N/A")

        if failed > 0:
            self.log("\n失败的接口:")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    self.log(f"  - {result['name']}: {result.get('error', '')}", "ERROR")

        self.log("\n" + "=" * 60)
        if failed == 0:
            self.log("🎉 所有接口测试通过！", "SUCCESS")
        else:
            self.log("⚠️  部分接口测试失败，请检查", "WARNING")
        self.log("=" * 60)

        return failed == 0


def main():
    tester = APITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
