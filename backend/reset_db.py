#!/usr/bin/env python3
"""
数据库重置脚本
用于清空并重新初始化数据库
"""

import os
import sys
from datetime import datetime, date, time, timedelta

def reset_database():
    """重置数据库"""
    print("开始重置数据库...")
    
    try:
        from app import create_app
        from models import db, Court, TimeSlot, Student, Application, Reservation, WeeklyStats
        
        app = create_app()
        
        with app.app_context():
            # 删除所有表
            print("删除现有数据表...")
            db.drop_all()
            
            # 重新创建所有表
            print("创建数据表...")
            db.create_all()
            
            # 初始化场地数据
            print("初始化场地数据...")
            courts = [
                Court(name='羽毛球场1号', location='体育馆一层', capacity=2),
                Court(name='羽毛球场2号', location='体育馆一层', capacity=2),
                Court(name='羽毛球场3号', location='体育馆二层', capacity=2),
                Court(name='羽毛球场4号', location='体育馆二层', capacity=2),
            ]
            
            for court in courts:
                db.session.add(court)
            
            db.session.commit()
            print(f"✓ 已创建 {len(courts)} 个场地")
            
            # 创建示例时间段
            create_sample_timeslots()
            
            print("✅ 数据库重置完成！")
            
    except Exception as e:
        print(f"❌ 数据库重置失败: {e}")
        sys.exit(1)

def create_sample_timeslots():
    """创建示例时间段"""
    from models import db, Court, TimeSlot
    
    courts = Court.query.all()
    if not courts:
        return
    
    # 为未来7天创建时间段
    start_date = date.today() + timedelta(days=1)
    
    time_slots = [
        (time(8, 0), time(9, 0)),   # 8:00-9:00
        (time(9, 0), time(10, 0)),  # 9:00-10:00
        (time(10, 0), time(11, 0)), # 10:00-11:00
        (time(14, 0), time(15, 0)), # 14:00-15:00
        (time(15, 0), time(16, 0)), # 15:00-16:00
        (time(16, 0), time(17, 0)), # 16:00-17:00
        (time(19, 0), time(20, 0)), # 19:00-20:00
        (time(20, 0), time(21, 0)), # 20:00-21:00
    ]
    
    created_count = 0
    
    for day_offset in range(7):  # 未来7天
        current_date = start_date + timedelta(days=day_offset)
        
        for court in courts:
            for start_time, end_time in time_slots:
                new_slot = TimeSlot(
                    court_id=court.id,
                    date=current_date,
                    start_time=start_time,
                    end_time=end_time
                )
                db.session.add(new_slot)
                created_count += 1
    
    db.session.commit()
    print(f"✓ 已创建 {created_count} 个时间段")

def create_test_data():
    """创建测试数据"""
    print("\n是否创建测试数据？(y/n): ", end="")
    choice = input().lower().strip()
    
    if choice == 'y':
        from models import db, Student
        from app import create_app
        
        app = create_app()
        with app.app_context():
            # 创建测试学生
            test_students = [
                {'student_id': 'test001', 'name': '张三', 'email': 'zhangsan@test.com', 'password': 'password123'},
                {'student_id': 'test002', 'name': '李四', 'email': 'lisi@test.com', 'password': 'password123'},
                {'student_id': 'test003', 'name': '王五', 'email': 'wangwu@test.com', 'password': 'password123'},
            ]
            
            for student_data in test_students:
                student = Student(
                    student_id=student_data['student_id'],
                    name=student_data['name'],
                    email=student_data['email']
                )
                student.set_password(student_data['password'])
                db.session.add(student)
            
            db.session.commit()
            print(f"✓ 已创建 {len(test_students)} 个测试学生")
            
            for student_data in test_students:
                print(f"  - 学号: {student_data['student_id']}, 密码: {student_data['password']}")

def main():
    """主函数"""
    print("FairCourt 数据库重置工具")
    print("=" * 30)
    print("⚠️  警告：此操作将删除所有现有数据！")
    print("确认要重置数据库吗？(y/n): ", end="")
    
    choice = input().lower().strip()
    
    if choice != 'y':
        print("操作已取消")
        return
    
    reset_database()
    create_test_data()
    
    print("\n" + "=" * 50)
    print("🎉 数据库重置完成！")
    print("\n现在可以:")
    print("1. 启动服务器: python app.py")
    print("2. 运行测试: python test_api.py")
    print("=" * 50)

if __name__ == "__main__":
    main() 