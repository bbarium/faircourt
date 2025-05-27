from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Court, TimeSlot, Application, Reservation, ApplicationStatus
from datetime import datetime, date, time, timedelta
from sqlalchemy import and_, or_

court_bp = Blueprint('court', __name__)

@court_bp.route('/courts', methods=['GET'])
def get_all_courts():
    """获取所有启用的场地信息"""
    courts = Court.query.filter_by(is_active=True).all()
    
    result = []
    for court in courts:
        result.append({
            'id': court.id,
            'name': court.name,
            'location': court.location,
            'capacity': court.capacity,
            'is_active': court.is_active
        })
    
    return jsonify({'courts': result}), 200

@court_bp.route('/timeslots/available', methods=['GET'])
def get_available_timeslots():
    """查询可申请的场次"""
    # 获取查询参数
    date_str = request.args.get('date')
    court_id = request.args.get('court_id')
    
    # 构建查询条件
    query = db.session.query(TimeSlot, Court).join(
        Court, TimeSlot.court_id == Court.id
    ).filter(
        Court.is_active == True
    )
    
    # 如果指定了日期
    if date_str:
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(TimeSlot.date == query_date)
        except ValueError:
            return jsonify({'error': '日期格式错误，请使用YYYY-MM-DD格式'}), 400
    
    # 如果指定了场地
    if court_id:
        try:
            court_id = int(court_id)
            query = query.filter(TimeSlot.court_id == court_id)
        except ValueError:
            return jsonify({'error': '场地ID必须是数字'}), 400
    
    # 只显示未来的时间段
    today = date.today()
    query = query.filter(TimeSlot.date >= today)
    
    # 执行查询
    timeslots = query.order_by(TimeSlot.date, TimeSlot.start_time).all()
    
    result = []
    for slot, court in timeslots:
        # 检查是否有待处理的申请
        pending_count = Application.query.filter_by(
            time_slot_id=slot.id,
            status=ApplicationStatus.PENDING
        ).count()
        
        # 检查是否已被预约
        reservation = Reservation.query.filter_by(
            time_slot_id=slot.id,
            is_cancelled=False
        ).first()
        
        # 确定状态
        if reservation or not slot.is_available:
            status = 'reserved'
        elif pending_count > 0:
            status = 'has_applications'
        else:
            status = 'available'
        
        result.append({
            'id': slot.id,
            'court_id': court.id,
            'court_name': court.name,
            'court_location': court.location,
            'court_capacity': court.capacity,
            'date': slot.date.isoformat(),
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'is_available': slot.is_available,
            'status': status,
            'applications_count': pending_count,
            'created_at': slot.created_at.isoformat()
        })
    
    return jsonify({'timeslots': result}), 200

@court_bp.route('/timeslots/reserve_status', methods=['GET'])
def get_reservation_status():
    """查询某天的预约状态"""
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': '请提供日期参数'}), 400
    
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误，请使用YYYY-MM-DD格式'}), 400
    
    # 获取该日期的所有时间段
    timeslots = db.session.query(TimeSlot, Court).join(
        Court, TimeSlot.court_id == Court.id
    ).filter(
        TimeSlot.date == query_date,
        Court.is_active == True
    ).order_by(TimeSlot.start_time).all()
    
    result = []
    for slot, court in timeslots:
        # 获取该时间段的申请统计
        pending_count = Application.query.filter_by(
            time_slot_id=slot.id,
            status=ApplicationStatus.PENDING
        ).count()
        
        approved_count = Application.query.filter_by(
            time_slot_id=slot.id,
            status=ApplicationStatus.APPROVED
        ).count()
        
        # 获取预约信息
        reservation = Reservation.query.filter_by(
            time_slot_id=slot.id,
            is_cancelled=False
        ).first()
        
        slot_info = {
            'id': slot.id,
            'court_id': court.id,
            'court_name': court.name,
            'court_location': court.location,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'is_available': slot.is_available,
            'pending_applications': pending_count,
            'approved_applications': approved_count,
            'is_reserved': reservation is not None,
            'reservation_info': None
        }
        
        if reservation:
            from models import Student
            student = Student.query.get(reservation.student_id)
            slot_info['reservation_info'] = {
                'student_name': student.name if student else '未知',
                'student_id': student.student_id if student else '未知',
                'reserved_at': reservation.created_at.isoformat()
            }
        
        result.append(slot_info)
    
    return jsonify({
        'date': query_date.isoformat(),
        'timeslots': result
    }), 200

# 管理员功能：创建时间段
@court_bp.route('/timeslots/create', methods=['POST'])
@jwt_required()
def create_timeslots():
    """创建新的时间段（管理员功能）"""
    data = request.get_json()
    
    required_fields = ['court_id', 'date', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    # 验证场地是否存在
    court = Court.query.get(data['court_id'])
    if not court:
        return jsonify({'error': '场地不存在'}), 404
    
    try:
        # 解析日期和时间
        slot_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # 验证时间逻辑
        if start_time >= end_time:
            return jsonify({'error': '开始时间必须早于结束时间'}), 400
        
        # 检查时间段是否冲突
        existing_slot = TimeSlot.query.filter(
            and_(
                TimeSlot.court_id == data['court_id'],
                TimeSlot.date == slot_date,
                or_(
                    and_(TimeSlot.start_time <= start_time, TimeSlot.end_time > start_time),
                    and_(TimeSlot.start_time < end_time, TimeSlot.end_time >= end_time),
                    and_(TimeSlot.start_time >= start_time, TimeSlot.end_time <= end_time)
                )
            )
        ).first()
        
        if existing_slot:
            return jsonify({'error': '该时间段与现有时间段冲突'}), 400
        
        # 创建新时间段
        new_slot = TimeSlot(
            court_id=data['court_id'],
            date=slot_date,
            start_time=start_time,
            end_time=end_time
        )
        
        db.session.add(new_slot)
        db.session.commit()
        
        return jsonify({
            'message': '时间段创建成功',
            'timeslot_id': new_slot.id
        }), 201
        
    except ValueError as e:
        return jsonify({'error': '日期或时间格式错误'}), 400

# 批量创建时间段
@court_bp.route('/timeslots/batch_create', methods=['POST'])
@jwt_required()
def batch_create_timeslots():
    """批量创建时间段"""
    data = request.get_json()
    
    required_fields = ['court_id', 'start_date', 'end_date', 'time_slots']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    court = Court.query.get(data['court_id'])
    if not court:
        return jsonify({'error': '场地不存在'}), 404
    
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        if start_date > end_date:
            return jsonify({'error': '开始日期不能晚于结束日期'}), 400
        
        created_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            for time_slot in data['time_slots']:
                start_time = datetime.strptime(time_slot['start_time'], '%H:%M').time()
                end_time = datetime.strptime(time_slot['end_time'], '%H:%M').time()
                
                # 检查是否已存在
                existing = TimeSlot.query.filter_by(
                    court_id=data['court_id'],
                    date=current_date,
                    start_time=start_time,
                    end_time=end_time
                ).first()
                
                if not existing:
                    new_slot = TimeSlot(
                        court_id=data['court_id'],
                        date=current_date,
                        start_time=start_time,
                        end_time=end_time
                    )
                    db.session.add(new_slot)
                    created_slots.append({
                        'date': current_date.isoformat(),
                        'start_time': start_time.strftime('%H:%M'),
                        'end_time': end_time.strftime('%H:%M')
                    })
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        
        return jsonify({
            'message': f'成功创建{len(created_slots)}个时间段',
            'created_slots': created_slots
        }), 201
        
    except ValueError:
        return jsonify({'error': '日期或时间格式错误'}), 400 