#!/usr/bin/env python3
"""
FairCourt API测试脚本
用于测试系统的各个接口功能
"""

import requests
import json
from datetime import datetime, date, timedelta

# 配置
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

class FairCourtTester:
    def __init__(self):
        self.access_token = None
        self.student_id = None
        
    def test_student_register(self):
        """测试学生注册"""
        print("=== 测试学生注册 ===")
        
        data = {
            "student_id": "2021001",
            "name": "测试学生",
            "email": "test@example.com",
            "password": "password123",
            "phone": "13800138000"
        }
        
        response = requests.post(f"{API_BASE}/student/register", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        return response.status_code == 201
    
    def test_student_login(self):
        """测试学生登录"""
        print("\n=== 测试学生登录 ===")
        
        data = {
            "student_id": "2021001",
            "password": "password123"
        }
        
        response = requests.post(f"{API_BASE}/student/login", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if response.status_code == 200:
            self.access_token = result.get('access_token')
            self.student_id = result.get('student', {}).get('id')
            print(f"获取到访问令牌: {self.access_token[:20]}...")
            return True
        
        return False
    
    def get_headers(self):
        """获取带认证的请求头"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_courts(self):
        """测试获取场地信息"""
        print("\n=== 测试获取场地信息 ===")
        
        response = requests.get(f"{API_BASE}/courts")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"场地数量: {len(result.get('courts', []))}")
        
        for court in result.get('courts', []):
            print(f"- {court['name']} ({court['location']})")
        
        return response.status_code == 200
    
    def test_create_timeslots(self):
        """测试创建时间段"""
        print("\n=== 测试创建时间段 ===")
        
        # 创建明天和后天的时间段
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        day_after = (date.today() + timedelta(days=2)).isoformat()
        
        time_slots = [
            {"court_id": 1, "date": tomorrow, "start_time": "08:00", "end_time": "09:00"},
            {"court_id": 1, "date": tomorrow, "start_time": "09:00", "end_time": "10:00"},
            {"court_id": 1, "date": day_after, "start_time": "08:00", "end_time": "09:00"},
            {"court_id": 2, "date": tomorrow, "start_time": "08:00", "end_time": "09:00"},
        ]
        
        created_count = 0
        for slot_data in time_slots:
            response = requests.post(
                f"{API_BASE}/timeslots/create", 
                json=slot_data, 
                headers=self.get_headers()
            )
            if response.status_code == 201:
                created_count += 1
                print(f"✓ 创建时间段: {slot_data['date']} {slot_data['start_time']}-{slot_data['end_time']}")
            else:
                print(f"✗ 创建失败: {response.json()}")
        
        print(f"成功创建 {created_count} 个时间段")
        return created_count > 0
    
    def test_get_available_timeslots(self):
        """测试查询可用时间段"""
        print("\n=== 测试查询可用时间段 ===")
        
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        response = requests.get(f"{API_BASE}/timeslots/available?date={tomorrow}")
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        timeslots = result.get('timeslots', [])
        print(f"可用时间段数量: {len(timeslots)}")
        
        for slot in timeslots:
            print(f"- ID:{slot['id']} {slot['court_name']} {slot['start_time']}-{slot['end_time']}")
        
        return response.status_code == 200 and len(timeslots) > 0
    
    def test_apply_for_timeslot(self):
        """测试提交预约申请"""
        print("\n=== 测试提交预约申请 ===")
        
        # 先获取可用时间段
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        response = requests.get(f"{API_BASE}/timeslots/available?date={tomorrow}")
        
        if response.status_code != 200:
            print("无法获取可用时间段")
            return False
        
        timeslots = response.json().get('timeslots', [])
        if not timeslots:
            print("没有可用时间段")
            return False
        
        # 申请第一个时间段
        time_slot_id = timeslots[0]['id']
        data = {"time_slot_id": time_slot_id}
        
        response = requests.post(
            f"{API_BASE}/student/apply", 
            json=data, 
            headers=self.get_headers()
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        return response.status_code == 201
    
    def test_get_application_status(self):
        """测试获取申请状态"""
        print("\n=== 测试获取申请状态 ===")
        
        response = requests.get(
            f"{API_BASE}/student/status", 
            headers=self.get_headers()
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        applications = result.get('applications', [])
        print(f"申请数量: {len(applications)}")
        
        for app in applications:
            print(f"- 申请ID:{app['application_id']} 状态:{app['status']} "
                  f"{app['court_name']} {app['date']} {app['start_time']}-{app['end_time']}")
        
        return response.status_code == 200
    
    def test_get_credit_score(self):
        """测试获取信用评分"""
        print("\n=== 测试获取信用评分 ===")
        
        response = requests.get(
            f"{API_BASE}/student/credit", 
            headers=self.get_headers()
        )
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"信用评分: {result.get('credit_score')}")
        print(f"成功率: {result.get('success_rate'):.2%}")
        print(f"优先级权重: {result.get('priority_weight'):.3f}")
        
        return response.status_code == 200
    
    def test_reservation_status(self):
        """测试查询预约状态"""
        print("\n=== 测试查询预约状态 ===")
        
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        response = requests.get(f"{API_BASE}/timeslots/reserve_status?date={tomorrow}")
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        timeslots = result.get('timeslots', [])
        print(f"日期: {result.get('date')}")
        print(f"时间段数量: {len(timeslots)}")
        
        for slot in timeslots:
            status = "已预约" if slot['is_reserved'] else "可用"
            pending = slot['pending_applications']
            print(f"- {slot['court_name']} {slot['start_time']}-{slot['end_time']} "
                  f"状态:{status} 待处理申请:{pending}")
        
        return response.status_code == 200
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始FairCourt API测试...")
        print("=" * 50)
        
        tests = [
            ("学生注册", self.test_student_register),
            ("学生登录", self.test_student_login),
            ("获取场地信息", self.test_get_courts),
            ("创建时间段", self.test_create_timeslots),
            ("查询可用时间段", self.test_get_available_timeslots),
            ("提交预约申请", self.test_apply_for_timeslot),
            ("获取申请状态", self.test_get_application_status),
            ("获取信用评分", self.test_get_credit_score),
            ("查询预约状态", self.test_reservation_status),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    print(f"✓ {test_name} - 通过")
                    passed += 1
                else:
                    print(f"✗ {test_name} - 失败")
            except Exception as e:
                print(f"✗ {test_name} - 异常: {str(e)}")
        
        print("\n" + "=" * 50)
        print(f"测试完成: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败，请检查系统状态")

def main():
    """主函数"""
    print("FairCourt API 测试工具")
    print("请确保后端服务已启动 (python app.py)")
    print()
    
    # 检查服务是否可用
    try:
        response = requests.get(f"{BASE_URL}/api/courts", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务不可用，请先启动服务")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到后端服务，请检查服务是否启动")
        return
    
    print("✅ 后端服务可用，开始测试...")
    print()
    
    tester = FairCourtTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 