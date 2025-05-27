from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes.student_routes import student_bp
from routes.court_routes import court_bp
from scheduler import init_scheduler
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    CORS(app)
    jwt = JWTManager(app)
    
    # 注册蓝图
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(court_bp, url_prefix='/api')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 初始化一些基础数据
        from models import Court, TimeSlot
        if Court.query.count() == 0:
            # 创建示例场地
            courts = [
                Court(name='羽毛球场1号', location='体育馆一层', capacity=2),
                Court(name='羽毛球场2号', location='体育馆一层', capacity=2),
                Court(name='羽毛球场3号', location='体育馆二层', capacity=2),
                Court(name='羽毛球场4号', location='体育馆二层', capacity=2),
            ]
            for court in courts:
                db.session.add(court)
            db.session.commit()
    
    # 初始化调度器
    init_scheduler(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000) 