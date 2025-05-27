#!/usr/bin/env python3
"""
FairCourt 启动脚本
包含环境检查、数据库初始化等功能
"""

import os
import sys
from datetime import datetime, date, time, timedelta

def check_dependencies():
    """检查依赖包"""
    print("检查依赖包...")
    
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_cors', 
        'flask_jwt_extended', 'apscheduler', 'bcrypt'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package}")
    
    if missing_packages:
        print(f"\n缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✓ 所有依赖包已安装")
    return True

def init_database():
    """初始化数据库"""
    print("\n初始化数据库...")
    
    from app import create_app
    from models import db, Court, TimeSlot
    
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✓ 数据库表已创建")
        
        # 检查是否需要初始化示例数据
        if Court.query.count() == 0:
            print("初始化示例场地数据...")
            
            courts = [
                Court(name='羽毛球场1号', location='体育馆一层', capacity=2),
                Court(name='羽毛球场2号', location='体育馆一层', capacity=2),
                Court(name='羽毛球场3号', location='体育馆二层', capacity=2),
                Court(name='羽毛球场4号', location='体育馆二层', capacity=2),
            ]
            
            for court in courts:
                db.session.add(court)
            
            db.session.commit()
            print(f"✓ 已创建 {len(courts)} 个示例场地")
        
        # 创建示例时间段
        create_sample_timeslots()

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
                # 检查是否已存在
                existing = TimeSlot.query.filter_by(
                    court_id=court.id,
                    date=current_date,
                    start_time=start_time,
                    end_time=end_time
                ).first()
                
                if not existing:
                    new_slot = TimeSlot(
                        court_id=court.id,
                        date=current_date,
                        start_time=start_time,
                        end_time=end_time
                    )
                    db.session.add(new_slot)
                    created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"✓ 已创建 {created_count} 个示例时间段")
    else:
        print("✓ 时间段数据已存在")

def show_system_info():
    """显示系统信息"""
    print("\n" + "="*50)
    print("FairCourt - 校园场地公平预约系统")
    print("="*50)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    # 显示配置信息
    from config import Config
    print(f"数据库: {Config.SQLALCHEMY_DATABASE_URI}")
    print(f"每周最大预约次数: {Config.MAX_WEEKLY_RESERVATIONS}")
    print(f"每日分配时间: {Config.ALLOCATION_TIME}")
    print(f"提前预约天数: {Config.ADVANCE_DAYS}")
    
    print("\n核心功能:")
    print("✓ 公平预约池 - 避免抢订模式")
    print("✓ 智能权重算法 - 动态调整优先级")
    print("✓ 信用评分系统 - 防止恶意爽约")
    print("✓ 候补队列机制 - 自动递补空缺")
    print("✓ 预约次数限制 - 防止资源霸占")
    
    print("\nAPI接口:")
    print("- 学生模块: /api/student/*")
    print("- 场地模块: /api/courts")
    print("- 时间段模块: /api/timeslots/*")
    
    print("\n调度任务:")
    print("- 22:00 公平分配算法")
    print("- 01:00 更新信用评分")
    print("- 02:00 清理过期数据")
    print("- 每10分钟 处理候补队列")

def main():
    """主函数"""
    print("FairCourt 系统启动检查")
    print("="*30)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 初始化数据库
    try:
        init_database()
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        sys.exit(1)
    
    # 显示系统信息
    show_system_info()
    
    print("\n" + "="*50)
    print("🚀 系统准备就绪！")
    print("\n启动命令:")
    print("  python app.py")
    print("\n测试命令:")
    print("  python test_api.py")
    print("\n访问地址:")
    print("  http://localhost:5000")
    print("="*50)

if __name__ == "__main__":
    main() 