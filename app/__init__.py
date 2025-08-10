from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
import os

db = SQLAlchemy()
login_manager = LoginManager()
scheduler = BackgroundScheduler()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monitor.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # 根据环境设置安全配置
    is_production = os.environ.get('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_SECURE'] = is_production  # 只在HTTPS时启用
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    
    # 配置审计日志
    import logging
    audit_logger = logging.getLogger('audit')
    audit_handler = logging.FileHandler('audit.log')
    audit_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from app.routes import main, auth, settings
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(settings.bp)
    
    with app.app_context():
        db.create_all()
        
        # 检查并添加新列和新表
        try:
            with db.engine.connect() as conn:
                conn.execute(text('SELECT alert_template FROM alert_config LIMIT 1'))
        except:
            # 添加新列
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE alert_config ADD COLUMN alert_template TEXT DEFAULT "网站监控告警\n网站名称: {name}\nURL: {url}\n状态: {status}\n时间: {time}\n错误信息: {error}"'))
                conn.commit()
        
        # 检查并创建GlobalConfig表
        try:
            with db.engine.connect() as conn:
                conn.execute(text('SELECT * FROM global_config LIMIT 1'))
        except:
            # 创建GlobalConfig表
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE TABLE global_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                '''))
                conn.commit()
        
        # 创建默认管理员账号
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            import secrets
            default_password = os.environ.get('ADMIN_PASSWORD') or secrets.token_urlsafe(12)
            admin = User(username='admin', role='admin')
            admin.set_password(default_password)
            db.session.add(admin)
            db.session.commit()
            
            # 将默认密码写入文件
            with open('admin_password.txt', 'w') as f:
                f.write(f'默认管理员密码: {default_password}\n')
                f.write('首次登录后请立即修改密码！\n')
            print('默认管理员密码已保存到 admin_password.txt 文件')
    
    # 启动监控调度器
    if not scheduler.running:
        scheduler.start()
    
    # 为调度器设置应用上下文
    scheduler.app = app
    
    return app