from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models import db, Student, Application, Reservation, TimeSlot, Court, ApplicationStatus, WeeklyStats
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_
import random

student_bp = Blueprint('student', __name__)

@student_bp.route('/register', methods=['POST'])
def register():
    """学生注册"""
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['student_id', 'name', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    # 检查学号和邮箱是否已存在
    if Student.query.filter_by(student_id=data['student_id']).first():
        return jsonify({'error': '学号已存在'}), 400
    
    if Student.query.filter_by(email=data['email']).first():
        return jsonify({'error': '邮箱已存在'}), 400
    
    # 创建新学生
    student = Student(
        student_id=data['student_id'],
        name=data['name'],
        email=data['email'],
        phone=data.get('phone', '')
    )
    student.set_password(data['password'])
    
    db.session.add(student)
    db.session.commit()
    
    return jsonify({'message': '注册成功', 'student_id': student.id}), 201

@student_bp.route('/login', methods=['POST'])
def login():
    """学生登录"""
    data = request.get_json()
    
    if 'student_id' not in data or 'password' not in data:
        return jsonify({'error': '学号和密码不能为空'}), 400
    
    student = Student.query.filter_by(student_id=data['student_id']).first()
    
    if student and student.check_password(data['password']):
        access_token = create_access_token(identity=student.id)
        return jsonify({
            'token': access_token,
            'student': {
                'id': student.id,
                'student_id': student.student_id,
                'name': student.name,
                'email': student.email,
                'phone': student.phone,
                'credit_score': student.credit_score,
                'created_at': student.created_at.isoformat()
            }
        }), 200
    
    return jsonify({'error': '学号或密码错误'}), 401

@student_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_for_timeslot():
    """提交预约申请"""
    try:
        student_id = get_jwt_identity()
        data = request.get_json()
        
        if 'timeslot_id' not in data:
            return jsonify({'error': '缺少时间段ID'}), 400
        
        time_slot_id = data['timeslot_id']
        
        # 检查时间段是否存在且可用
        time_slot = TimeSlot.query.get(time_slot_id)
        if not time_slot:
            return jsonify({'error': '时间段不存在'}), 404
        
        if not time_slot.is_available:
            return jsonify({'error': '该时间段不可预约'}), 400
        
        # 检查是否已经申请过该时间段
        existing_application = Application.query.filter_by(
            student_id=student_id,
            time_slot_id=time_slot_id
        ).first()
        
        if existing_application:
            return jsonify({'error': '您已经申请过该时间段'}), 400
        
        # 检查本周预约次数限制
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': '学生不存在'}), 404
            
        week_start = date.today() - timedelta(days=date.today().weekday())
        
        weekly_stat = WeeklyStats.query.filter_by(
            student_id=student_id,
            week_start=week_start
        ).first()
        
        if not weekly_stat:
            weekly_stat = WeeklyStats(student_id=student_id, week_start=week_start)
            db.session.add(weekly_stat)
        
        # 确保reservations_count不为None
        if weekly_stat.reservations_count is None:
            weekly_stat.reservations_count = 0
        
        if weekly_stat.reservations_count >= 3:  # 每周最多3次
            return jsonify({'error': '本周预约次数已达上限'}), 400
        
        # 创建申请
        application = Application(
            student_id=student_id,
            time_slot_id=time_slot_id,
            priority_weight=student.get_priority_weight()
        )
        
        db.session.add(application)
        student.total_applications += 1
        db.session.commit()
        
        return jsonify({
            'message': '申请提交成功',
            'application_id': application.id,
            'priority_weight': application.priority_weight
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'服务器内部错误: {str(e)}'}), 500

@student_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_application():
    """取消预约申请"""
    student_id = get_jwt_identity()
    data = request.get_json()
    
    # 支持通过application_id或timeslot_id取消
    application = None
    if 'application_id' in data:
        application = Application.query.filter_by(
            id=data['application_id'],
            student_id=student_id
        ).first()
    elif 'timeslot_id' in data:
        application = Application.query.filter_by(
            time_slot_id=data['timeslot_id'],
            student_id=student_id,
            status=ApplicationStatus.PENDING
        ).first()
    else:
        return jsonify({'error': '缺少申请ID或时间段ID'}), 400
    
    if not application:
        return jsonify({'error': '申请不存在'}), 404
    
    if application.status == ApplicationStatus.CANCELLED:
        return jsonify({'error': '申请已取消'}), 400
    
    # 如果已经分配成功，需要取消预约
    if application.status == ApplicationStatus.APPROVED:
        reservation = Reservation.query.filter_by(application_id=application.id).first()
        if reservation:
            reservation.is_cancelled = True
            reservation.cancelled_at = datetime.utcnow()
            
            # 更新周统计
            week_start = date.today() - timedelta(days=date.today().weekday())
            weekly_stat = WeeklyStats.query.filter_by(
                student_id=student_id,
                week_start=week_start
            ).first()
            if weekly_stat and weekly_stat.reservations_count > 0:
                weekly_stat.reservations_count -= 1
    
    application.status = ApplicationStatus.CANCELLED
    application.processed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': '取消成功'}), 200

@student_bp.route('/reserve_direct', methods=['POST'])
@jwt_required()
def reserve_direct():
    """直接预约未申请的预约会场地"""
    student_id = get_jwt_identity()
    data = request.get_json()
    
    if 'time_slot_id' not in data:
        return jsonify({'error': '缺少时间段ID'}), 400
    
    time_slot_id = data['time_slot_id']
    
    # 检查时间段是否存在且可用
    time_slot = TimeSlot.query.get(time_slot_id)
    if not time_slot:
        return jsonify({'error': '时间段不存在'}), 404
    
    if not time_slot.is_available:
        return jsonify({'error': '该时间段不可预约'}), 400
    
    # 检查是否有待处理的申请
    pending_applications = Application.query.filter_by(
        time_slot_id=time_slot_id,
        status=ApplicationStatus.PENDING
    ).count()
    
    if pending_applications > 0:
        return jsonify({'error': '该时间段有待处理的申请，无法直接预约'}), 400
    
    # 检查本周预约次数限制
    week_start = date.today() - timedelta(days=date.today().weekday())
    weekly_stat = WeeklyStats.query.filter_by(
        student_id=student_id,
        week_start=week_start
    ).first()
    
    if not weekly_stat:
        weekly_stat = WeeklyStats(student_id=student_id, week_start=week_start)
        db.session.add(weekly_stat)
    
    # 确保reservations_count不为None
    if weekly_stat.reservations_count is None:
        weekly_stat.reservations_count = 0
    
    if weekly_stat.reservations_count >= 3:
        return jsonify({'error': '本周预约次数已达上限'}), 400
    
    # 创建预约
    reservation = Reservation(
        student_id=student_id,
        time_slot_id=time_slot_id
    )
    
    time_slot.is_available = False
    weekly_stat.reservations_count += 1
    
    db.session.add(reservation)
    db.session.commit()
    
    return jsonify({
        'message': '预约成功',
        'reservation_id': reservation.id
    }), 201

@student_bp.route('/status', methods=['GET'])
@jwt_required()
def get_application_status():
    """获取申请状态"""
    student_id = get_jwt_identity()
    
    # 获取所有申请
    applications = db.session.query(Application, TimeSlot, Court).join(
        TimeSlot, Application.time_slot_id == TimeSlot.id
    ).join(
        Court, TimeSlot.court_id == Court.id
    ).filter(
        Application.student_id == student_id
    ).order_by(Application.applied_at.desc()).all()
    
    result = []
    for app, slot, court in applications:
        result.append({
            'id': app.id,
            'application_id': app.id,
            'timeslot_id': app.time_slot_id,
            'status': app.status.value,
            'court_id': court.id,
            'court_name': court.name,
            'court_location': court.location,
            'date': slot.date.isoformat(),
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'applied_at': app.applied_at.isoformat(),
            'processed_at': app.processed_at.isoformat() if app.processed_at else None,
            'priority_weight': app.priority_weight,
            'queue_position': app.queue_position
        })
    
    return jsonify({'applications': result}), 200

@student_bp.route('/records', methods=['GET'])
@jwt_required()
def get_reservation_records():
    """查看历史预约与违约记录"""
    student_id = get_jwt_identity()
    
    # 获取所有预约记录
    reservations = db.session.query(Reservation, TimeSlot, Court).join(
        TimeSlot, Reservation.time_slot_id == TimeSlot.id
    ).join(
        Court, TimeSlot.court_id == Court.id
    ).filter(
        Reservation.student_id == student_id
    ).order_by(Reservation.created_at.desc()).all()
    
    result = []
    for res, slot, court in reservations:
        # 确定预约状态
        if res.is_cancelled:
            status = 'cancelled'
        elif res.no_show:
            status = 'no_show'
        elif res.is_completed:
            status = 'completed'
        else:
            status = 'confirmed'
            
        result.append({
            'id': res.id,
            'reservation_id': res.id,
            'timeslot_id': res.time_slot_id,
            'court_id': court.id,
            'court_name': court.name,
            'court_location': court.location,
            'date': slot.date.isoformat(),
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'status': status,
            'is_confirmed': res.is_confirmed,
            'is_cancelled': res.is_cancelled,
            'is_completed': res.is_completed,
            'no_show': res.no_show,
            'created_at': res.created_at.isoformat(),
            'cancelled_at': res.cancelled_at.isoformat() if res.cancelled_at else None,
            'rating': res.rating,
            'feedback': res.feedback
        })
    
    # 获取学生统计信息
    student = Student.query.get(student_id)
    stats = {
        'credit_score': student.credit_score,
        'total_applications': student.total_applications,
        'successful_applications': student.successful_applications,
        'no_show_count': student.no_show_count,
        'success_rate': student.get_success_rate()
    }
    
    return jsonify({
        'records': result,
        'stats': stats
    }), 200

@student_bp.route('/credit', methods=['GET'])
@jwt_required()
def get_credit_score():
    """获取信用评分"""
    student_id = get_jwt_identity()
    student = Student.query.get(student_id)
    
    if not student:
        return jsonify({'error': '学生不存在'}), 404
    
    return jsonify({
        'credit_score': student.credit_score,
        'total_applications': student.total_applications,
        'successful_applications': student.successful_applications,
        'no_show_count': student.no_show_count,
        'success_rate': student.get_success_rate(),
        'priority_weight': student.get_priority_weight()
    }), 200 