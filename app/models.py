from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    check_interval = db.Column(db.Integer, default=300)  # 检查间隔(秒)
    timeout = db.Column(db.Integer, default=10)  # 超时时间(秒)
    status = db.Column(db.String(20), default='unknown')  # up, down, unknown
    last_check = db.Column(db.DateTime)
    response_time = db.Column(db.Float)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='websites')

class MonitorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    status = db.Column(db.String(20))
    response_time = db.Column(db.Float)
    error_message = db.Column(db.Text)
    check_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    website = db.relationship('Website', backref='logs')

class AlertConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    dingtalk_webhook = db.Column(db.String(500))
    alert_enabled = db.Column(db.Boolean, default=True)
    alert_template = db.Column(db.Text, default='网站监控告警\n网站名称: {name}\nURL: {url}\n状态: {status}\n时间: {time}\n错误信息: {error}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    website = db.relationship('Website', backref='alert_config')

class AlertLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    alert_type = db.Column(db.String(20))  # down, up
    message = db.Column(db.Text)
    status = db.Column(db.String(20))  # success, failed
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    website = db.relationship('Website', backref='alert_logs')

class GlobalConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)