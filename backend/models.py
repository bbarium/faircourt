from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from enum import Enum
import bcrypt

db = SQLAlchemy()

class ApplicationStatus(Enum):
    PENDING = "pending"      # 待分配
    APPROVED = "approved"    # 已分配
    REJECTED = "rejected"    # 未分配
    CANCELLED = "cancelled"  # 已取消
    COMPLETED = "completed"  # 已完成

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # 学号
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20))
    
    # 信用评分系统
    credit_score = db.Column(db.Integer, default=100)  # 初始信用分100
    total_applications = db.Column(db.Integer, default=0)  # 总申请次数
    successful_applications = db.Column(db.Integer, default=0)  # 成功申请次数
    no_show_count = db.Column(db.Integer, default=0)  # 爽约次数
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    applications = db.relationship('Application', backref='student', lazy=True)
    reservations = db.relationship('Reservation', backref='student', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_success_rate(self):
        if self.total_applications == 0:
            return 0.5  # 新用户默认成功率
        return self.successful_applications / self.total_applications
    
    def get_priority_weight(self):
        """计算优先级权重，成功率低的用户优先级更高"""
        success_rate = self.get_success_rate()
        credit_factor = self.credit_score / 100
        return (1 - success_rate) * credit_factor

class Court(db.Model):
    __tablename__ = 'courts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, default=2)  # 场地容量
    is_active = db.Column(db.Boolean, default=True)
    
    # 关系
    time_slots = db.relationship('TimeSlot', backref='court', lazy=True)

class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    applications = db.relationship('Application', backref='time_slot', lazy=True)
    reservations = db.relationship('Reservation', backref='time_slot', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'), nullable=False)
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    priority_weight = db.Column(db.Float, default=0.5)  # 优先级权重
    
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # 候补队列相关
    queue_position = db.Column(db.Integer)  # 队列位置

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))
    
    # 预约状态
    is_confirmed = db.Column(db.Boolean, default=True)
    is_cancelled = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)
    no_show = db.Column(db.Boolean, default=False)  # 是否爽约
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime)
    
    # 评分反馈
    rating = db.Column(db.Integer)  # 1-5分评分
    feedback = db.Column(db.Text)

class WeeklyStats(db.Model):
    __tablename__ = 'weekly_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    week_start = db.Column(db.Date, nullable=False)  # 周开始日期
    reservations_count = db.Column(db.Integer, default=0)  # 本周预约次数
    
    student = db.relationship('Student', backref='weekly_stats')

class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text) 