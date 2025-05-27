from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from models import db, Application, Reservation, TimeSlot, Student, ApplicationStatus, WeeklyStats
from datetime import datetime, date, timedelta
import random
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fair_allocation_algorithm():
    """公平分配算法 - 每日22:00执行"""
    logger.info("开始执行公平分配算法...")
    
    try:
        # 获取所有待处理的申请
        pending_applications = Application.query.filter_by(
            status=ApplicationStatus.PENDING
        ).all()
        
        if not pending_applications:
            logger.info("没有待处理的申请")
            return
        
        # 按时间段分组申请
        timeslot_applications = {}
        for app in pending_applications:
            if app.time_slot_id not in timeslot_applications:
                timeslot_applications[app.time_slot_id] = []
            timeslot_applications[app.time_slot_id].append(app)
        
        allocated_count = 0
        rejected_count = 0
        
        # 对每个时间段进行分配
        for time_slot_id, applications in timeslot_applications.items():
            time_slot = TimeSlot.query.get(time_slot_id)
            
            if not time_slot or not time_slot.is_available:
                # 时间段不可用，拒绝所有申请
                for app in applications:
                    app.status = ApplicationStatus.REJECTED
                    app.processed_at = datetime.utcnow()
                    rejected_count += 1
                continue
            
            # 按优先级权重排序（权重高的优先）
            applications.sort(key=lambda x: x.priority_weight, reverse=True)
            
            # 如果只有一个申请者，直接分配
            if len(applications) == 1:
                selected_app = applications[0]
            else:
                # 多个申请者时，使用加权随机选择
                # 权重越高，被选中的概率越大
                weights = [app.priority_weight for app in applications]
                selected_app = random.choices(applications, weights=weights)[0]
            
            # 分配给选中的申请者
            selected_app.status = ApplicationStatus.APPROVED
            selected_app.processed_at = datetime.utcnow()
            
            # 创建预约记录
            reservation = Reservation(
                student_id=selected_app.student_id,
                time_slot_id=time_slot_id,
                application_id=selected_app.id
            )
            db.session.add(reservation)
            
            # 更新时间段状态
            time_slot.is_available = False
            
            # 更新学生统计
            student = Student.query.get(selected_app.student_id)
            student.successful_applications += 1
            
            # 更新周统计
            week_start = date.today() - timedelta(days=date.today().weekday())
            weekly_stat = WeeklyStats.query.filter_by(
                student_id=selected_app.student_id,
                week_start=week_start
            ).first()
            
            if not weekly_stat:
                weekly_stat = WeeklyStats(
                    student_id=selected_app.student_id,
                    week_start=week_start
                )
                db.session.add(weekly_stat)
            
            weekly_stat.reservations_count += 1
            allocated_count += 1
            
            # 拒绝其他申请者，并设置队列位置
            queue_position = 1
            for app in applications:
                if app.id != selected_app.id:
                    app.status = ApplicationStatus.REJECTED
                    app.processed_at = datetime.utcnow()
                    app.queue_position = queue_position
                    queue_position += 1
                    rejected_count += 1
        
        # 提交所有更改
        db.session.commit()
        
        logger.info(f"分配完成: 成功分配 {allocated_count} 个，拒绝 {rejected_count} 个")
        
    except Exception as e:
        logger.error(f"分配算法执行失败: {str(e)}")
        db.session.rollback()

def update_credit_scores():
    """更新信用评分 - 检查爽约情况"""
    logger.info("开始更新信用评分...")
    
    try:
        # 获取昨天的预约记录
        yesterday = date.today() - timedelta(days=1)
        
        reservations = db.session.query(Reservation, TimeSlot).join(
            TimeSlot, Reservation.time_slot_id == TimeSlot.id
        ).filter(
            TimeSlot.date == yesterday,
            Reservation.is_cancelled == False,
            Reservation.is_completed == False,
            Reservation.no_show == False
        ).all()
        
        no_show_count = 0
        
        for reservation, time_slot in reservations:
            # 假设如果预约时间已过且未标记为完成，则视为爽约
            reservation_datetime = datetime.combine(
                time_slot.date, 
                time_slot.end_time
            )
            
            if datetime.now() > reservation_datetime:
                # 标记为爽约
                reservation.no_show = True
                
                # 更新学生信用分
                student = Student.query.get(reservation.student_id)
                if student:
                    student.no_show_count += 1
                    # 每次爽约扣10分，最低不低于0分
                    student.credit_score = max(0, student.credit_score - 10)
                    no_show_count += 1
        
        db.session.commit()
        logger.info(f"信用评分更新完成: 发现 {no_show_count} 次爽约")
        
    except Exception as e:
        logger.error(f"信用评分更新失败: {str(e)}")
        db.session.rollback()

def cleanup_old_data():
    """清理过期数据"""
    logger.info("开始清理过期数据...")
    
    try:
        # 删除30天前的申请记录
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        old_applications = Application.query.filter(
            Application.applied_at < thirty_days_ago
        ).delete()
        
        # 删除30天前的预约记录
        old_reservations = Reservation.query.filter(
            Reservation.created_at < thirty_days_ago
        ).delete()
        
        db.session.commit()
        logger.info(f"清理完成: 删除 {old_applications} 个申请记录，{old_reservations} 个预约记录")
        
    except Exception as e:
        logger.error(f"数据清理失败: {str(e)}")
        db.session.rollback()

def handle_cancellation_queue():
    """处理取消预约后的候补队列"""
    logger.info("处理候补队列...")
    
    try:
        # 查找被取消的预约
        cancelled_reservations = Reservation.query.filter_by(
            is_cancelled=True
        ).all()
        
        for reservation in cancelled_reservations:
            time_slot = TimeSlot.query.get(reservation.time_slot_id)
            if time_slot and not time_slot.is_available:
                # 查找该时间段的候补申请（按队列位置排序）
                queue_applications = Application.query.filter_by(
                    time_slot_id=reservation.time_slot_id,
                    status=ApplicationStatus.REJECTED
                ).filter(
                    Application.queue_position.isnot(None)
                ).order_by(Application.queue_position).all()
                
                if queue_applications:
                    # 分配给队列中的第一个
                    next_app = queue_applications[0]
                    next_app.status = ApplicationStatus.APPROVED
                    next_app.processed_at = datetime.utcnow()
                    
                    # 创建新的预约
                    new_reservation = Reservation(
                        student_id=next_app.student_id,
                        time_slot_id=reservation.time_slot_id,
                        application_id=next_app.id
                    )
                    db.session.add(new_reservation)
                    
                    # 更新学生统计
                    student = Student.query.get(next_app.student_id)
                    student.successful_applications += 1
                    
                    logger.info(f"候补成功: 学生 {student.student_id} 获得时间段 {reservation.time_slot_id}")
                else:
                    # 没有候补，释放时间段
                    time_slot.is_available = True
                    logger.info(f"时间段 {reservation.time_slot_id} 已释放")
            
            # 删除已处理的取消记录
            db.session.delete(reservation)
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"候补队列处理失败: {str(e)}")
        db.session.rollback()

def init_scheduler(app):
    """初始化调度器"""
    scheduler = BackgroundScheduler()
    
    # 每日22:00执行公平分配算法
    scheduler.add_job(
        func=fair_allocation_algorithm,
        trigger=CronTrigger(hour=22, minute=0),
        id='fair_allocation',
        name='公平分配算法',
        replace_existing=True
    )
    
    # 每日凌晨1:00更新信用评分
    scheduler.add_job(
        func=update_credit_scores,
        trigger=CronTrigger(hour=1, minute=0),
        id='update_credit_scores',
        name='更新信用评分',
        replace_existing=True
    )
    
    # 每日凌晨2:00清理过期数据
    scheduler.add_job(
        func=cleanup_old_data,
        trigger=CronTrigger(hour=2, minute=0),
        id='cleanup_old_data',
        name='清理过期数据',
        replace_existing=True
    )
    
    # 每10分钟处理一次候补队列
    scheduler.add_job(
        func=handle_cancellation_queue,
        trigger=CronTrigger(minute='*/10'),
        id='handle_queue',
        name='处理候补队列',
        replace_existing=True
    )
    
    # 在应用上下文中启动调度器
    with app.app_context():
        scheduler.start()
    
    logger.info("调度器已启动")
    
    return scheduler 