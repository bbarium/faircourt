import os
from datetime import timedelta

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///faircourt.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    
    # 预约系统配置
    MAX_WEEKLY_RESERVATIONS = 3  # 每周最大预约次数
    ALLOCATION_TIME = "22:00"    # 每日分配时间
    ADVANCE_DAYS = 2             # 提前预约天数 