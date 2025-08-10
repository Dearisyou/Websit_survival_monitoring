from functools import wraps
from flask import request, jsonify, g
from flask_login import current_user
import time
import hashlib
from collections import defaultdict

# 速率限制存储
rate_limit_storage = defaultdict(list)

def rate_limit(max_requests=5, window=60):
    """速率限制装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取客户端标识
            if current_user.is_authenticated:
                key = f"user_{current_user.id}"
            else:
                key = f"ip_{request.remote_addr}"
            
            now = time.time()
            # 清理过期记录
            rate_limit_storage[key] = [req_time for req_time in rate_limit_storage[key] if now - req_time < window]
            
            # 检查是否超过限制
            if len(rate_limit_storage[key]) >= max_requests:
                return jsonify({'error': '请求过于频繁，请稍后再试'}), 429
            
            # 记录当前请求
            rate_limit_storage[key].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def encrypt_sensitive_data(data):
    """加密敏感数据"""
    if not data:
        return data
    # 简单的混淆加密（生产环境应使用更强的加密）
    import base64
    return base64.b64encode(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data):
    """解密敏感数据"""
    if not encrypted_data:
        return encrypted_data
    try:
        import base64
        return base64.b64decode(encrypted_data.encode()).decode()
    except:
        return encrypted_data

def audit_log(action, details=None):
    """审计日志"""
    import logging
    logger = logging.getLogger('audit')
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    logger.info(f"User {user_id}: {action} - {details or ''}")