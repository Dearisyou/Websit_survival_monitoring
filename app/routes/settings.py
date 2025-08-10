from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app.models import GlobalConfig
from app.forms import GlobalAlertForm
from app import db
from datetime import datetime
import requests
import time
import hmac
import hashlib
import base64
import urllib.parse

bp = Blueprint('settings', __name__, url_prefix='/settings')

def generate_dingtalk_sign(secret):
    """生成钉钉签名"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign

@bp.route('/global-alert', methods=['GET', 'POST'])
@login_required
def global_alert():
    if not current_user.is_admin():
        flash('权限不足')
        return redirect(url_for('main.dashboard'))
    
    webhook_config = GlobalConfig.query.filter_by(key='global_dingtalk_webhook').first()
    secret_config = GlobalConfig.query.filter_by(key='global_dingtalk_secret').first()
    enabled_config = GlobalConfig.query.filter_by(key='global_alert_enabled').first()
    
    form = GlobalAlertForm()
    
    # 只在GET请求时设置表单数据
    if request.method == 'GET':
        if webhook_config:
            form.global_dingtalk_webhook.data = webhook_config.value
        if secret_config:
            from app.security import decrypt_sensitive_data
            form.global_dingtalk_secret.data = decrypt_sensitive_data(secret_config.value)
        if enabled_config:
            form.global_alert_enabled.data = enabled_config.value == 'true'
        else:
            form.global_alert_enabled.data = True  # 默认启用
    
    if form.validate_on_submit():
        if webhook_config:
            webhook_config.value = form.global_dingtalk_webhook.data
        else:
            webhook_config = GlobalConfig(key='global_dingtalk_webhook', value=form.global_dingtalk_webhook.data)
            db.session.add(webhook_config)
        
        if secret_config:
            from app.security import encrypt_sensitive_data
            secret_config.value = encrypt_sensitive_data(form.global_dingtalk_secret.data or '')
        else:
            from app.security import encrypt_sensitive_data
            secret_config = GlobalConfig(key='global_dingtalk_secret', value=encrypt_sensitive_data(form.global_dingtalk_secret.data or ''))
            db.session.add(secret_config)
        
        if enabled_config:
            enabled_config.value = 'true' if form.global_alert_enabled.data else 'false'
        else:
            enabled_config = GlobalConfig(key='global_alert_enabled', value='true' if form.global_alert_enabled.data else 'false')
            db.session.add(enabled_config)
        
        db.session.commit()
        flash('全局告警配置保存成功')
        return redirect(url_for('settings.global_alert'))
    
    return render_template('settings/global_alert.html', form=form)

@bp.route('/test-alert', methods=['POST'])
@login_required
def test_alert():
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': '权限不足'})
    
    # 检查速率限制
    from app.security import rate_limit_storage
    key = f"test_alert_{current_user.id}"
    now = time.time()
    rate_limit_storage[key] = [req_time for req_time in rate_limit_storage[key] if now - req_time < 60]
    if len(rate_limit_storage[key]) >= 3:
        return jsonify({'success': False, 'message': '请求过于频繁，请稍后再试'})
    rate_limit_storage[key].append(now)
    
    webhook_config = GlobalConfig.query.filter_by(key='global_dingtalk_webhook').first()
    secret_config = GlobalConfig.query.filter_by(key='global_dingtalk_secret').first()
    
    if not webhook_config:
        return jsonify({'success': False, 'message': '请先配置全局Webhook地址'})
    
    test_message = {
        "msgtype": "text",
        "text": {
            "content": f"网站监控告警\n\n📢 测试消息\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n如果您收到此消息，说明告警配置正常！"
        }
    }
    
    # 构建请求URL
    url = webhook_config.value
    if secret_config and secret_config.value:
        from app.security import decrypt_sensitive_data
        decrypted_secret = decrypt_sensitive_data(secret_config.value)
        if decrypted_secret:
            timestamp, sign = generate_dingtalk_sign(decrypted_secret)
            url = f"{webhook_config.value}&timestamp={timestamp}&sign={sign}"
    
    try:
        response = requests.post(url, json=test_message, timeout=10)
        if response.status_code == 200:
            response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            if isinstance(response_data, dict) and response_data.get('errcode') == 0:
                return jsonify({'success': True, 'message': '测试消息发送成功，请检查钉钉群消息'})
            else:
                return jsonify({'success': False, 'message': f'钉钉返回错误: {response_data}'})
        else:
            return jsonify({'success': False, 'message': f'HTTP {response.status_code}: {response.text}'})
    except Exception as e:
        import logging
        logging.error(f'DingTalk test error: {str(e)}')
        return jsonify({'success': False, 'message': '发送失败，请检查配置'})