import requests
import json
from datetime import datetime
from app import db, scheduler
from app.models import Website, MonitorLog, AlertConfig

def check_website(website_id):
    """检查单个网站状态"""
    with scheduler.app.app_context():
        # 重新查询防止会话分离
        website = Website.query.get(website_id)
        if not website:
            return
        
        try:
            start_time = datetime.now()
            # SSRF防护
            from urllib.parse import urlparse
            parsed = urlparse(website.url)
            if parsed.hostname in ['localhost', '127.0.0.1'] or parsed.hostname.startswith('192.168.') or parsed.hostname.startswith('10.') or parsed.hostname.startswith('172.'):
                raise Exception('不允许访问内网地址')
            
            response = requests.get(website.url, timeout=website.timeout)
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            status = 'up' if response.status_code == 200 else 'down'
            error_message = None if status == 'up' else f'HTTP {response.status_code}'
            
        except requests.exceptions.RequestException as e:
            status = 'down'
            response_time = None
            error_message = str(e)
        except Exception as e:
            status = 'down'
            response_time = None
            error_message = str(e)
        
        # 更新网站状态
        try:
            # 重新查询获取最新状态
            website = Website.query.get(website_id)
            old_status = website.status
            website.status = status
            website.last_check = datetime.utcnow()
            website.response_time = response_time
            
            # 记录日志
            log = MonitorLog(
                website_id=website_id,
                status=status,
                response_time=response_time,
                error_message=error_message
            )
            
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f'数据库更新失败: {e}')
            return
        
        # 发送告警：故障或恢复
        if old_status != status and old_status is not None:
            if status == 'down':
                send_alert(website_id, 'down', error_message)
            elif status == 'up' and old_status == 'down':
                send_alert(website_id, 'up', None)

def send_alert(website_id, status, error_message):
    """发送钉钉告警"""
    from app.models import AlertLog, GlobalConfig, Website
    
    # 重新查询网站对象防止会话分离
    website = Website.query.get(website_id)
    if not website:
        return
    
    # 检查全局配置
    global_webhook = GlobalConfig.query.filter_by(key='global_dingtalk_webhook').first()
    global_enabled = GlobalConfig.query.filter_by(key='global_alert_enabled').first()
    global_secret = GlobalConfig.query.filter_by(key='global_dingtalk_secret').first()
    
    # 全局告警未启用则直接返回
    if not global_webhook or not global_enabled or global_enabled.value == 'false':
        return
    
    # 检查单个网站是否开启告警（默认开启）
    alert_config = AlertConfig.query.filter_by(website_id=website.id).first()
    if alert_config and not alert_config.alert_enabled:
        return
    
    status_text = '故障' if status == 'down' else '恢复'
    
    # 使用默认模板
    template = '网站监控告警\n\n网站名称: {name}\nURL: {url}\n状态: {status}\n时间: {time}\n错误信息: {error}'
    
    content = template.format(
        name=website.name,
        url=website.url,
        status=status_text,
        time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        error=error_message or '无'
    )
    
    message = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    # 发送告警并记录日志
    alert_status = 'failed'
    alert_error = None
    
    # 构建请求URL
    url = global_webhook.value
    if global_secret and global_secret.value:
        from app.security import decrypt_sensitive_data
        decrypted_secret = decrypt_sensitive_data(global_secret.value)
        if decrypted_secret:
            import time
            import hmac
            import hashlib
            import base64
            import urllib.parse
            
            timestamp = str(round(time.time() * 1000))
            secret_enc = decrypted_secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(timestamp, decrypted_secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            url = f"{global_webhook.value}&timestamp={timestamp}&sign={sign}"
    
    try:
        response = requests.post(url, json=message, timeout=10)
        if response.status_code == 200:
            alert_status = 'success'
        else:
            alert_error = f'HTTP {response.status_code}: {response.text}'
    except Exception as e:
        alert_error = str(e)
    
    # 记录告警日志
    alert_log = AlertLog(
        website_id=website.id,
        alert_type=status,
        message=content,
        status=alert_status,
        error_message=alert_error
    )
    
    db.session.add(alert_log)
    db.session.commit()

def add_monitor_job(website_id):
    """添加监控任务"""
    website = Website.query.get(website_id)
    if website:
        job_id = f'monitor_{website_id}'
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        
        scheduler.add_job(
            func=check_website,
            args=[website_id],
            trigger='interval',
            seconds=website.check_interval,
            id=job_id,
            replace_existing=True
        )

def remove_monitor_job(website_id):
    """移除监控任务"""
    job_id = f'monitor_{website_id}'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)