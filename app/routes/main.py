from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Website, MonitorLog, AlertConfig, AlertLog
from app.forms import WebsiteForm, AlertForm, ImportExcelForm
from app.monitor import add_monitor_job, remove_monitor_job
from app import db
from datetime import datetime, timedelta
import pandas as pd
import os
from werkzeug.utils import secure_filename

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        websites = Website.query.all()
    else:
        websites = Website.query.filter_by(created_by=current_user.id).all()
    
    total_sites = len(websites)
    up_sites = len([w for w in websites if w.status == 'up'])
    down_sites = len([w for w in websites if w.status == 'down'])
    
    stats = {
        'total': total_sites,
        'up': up_sites,
        'down': down_sites,
        'uptime': round((up_sites / total_sites * 100) if total_sites > 0 else 0, 1)
    }
    
    return render_template('main/dashboard.html', websites=websites, stats=stats)

@bp.route('/websites')
@login_required
def websites():
    if current_user.is_admin():
        websites = Website.query.all()
    else:
        websites = Website.query.filter_by(created_by=current_user.id).all()
    return render_template('main/websites.html', websites=websites)

@bp.route('/websites/create', methods=['GET', 'POST'])
@login_required
def create_website():
    form = WebsiteForm()
    if form.validate_on_submit():
        website = Website(
            name=form.name.data,
            url=form.url.data,
            check_interval=form.check_interval.data,
            timeout=form.timeout.data,
            created_by=current_user.id
        )
        db.session.add(website)
        db.session.commit()
        
        # 添加监控任务
        add_monitor_job(website.id)
        
        # 立即执行一次检测
        from app.monitor import check_website
        check_website(website.id)
        
        flash('网站添加成功，已开始监控')
        return redirect(url_for('main.websites'))
    
    return render_template('main/create_website.html', form=form)

@bp.route('/websites/<int:website_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_website(website_id):
    website = Website.query.get_or_404(website_id)
    
    if not current_user.is_admin() and website.created_by != current_user.id:
        flash('权限不足')
        return redirect(url_for('main.websites'))
    
    form = WebsiteForm(obj=website)
    if form.validate_on_submit():
        website.name = form.name.data
        website.url = form.url.data
        website.check_interval = form.check_interval.data
        website.timeout = form.timeout.data
        db.session.commit()
        
        # 更新监控任务
        remove_monitor_job(website.id)
        add_monitor_job(website.id)
        
        # 立即执行一次检测
        from app.monitor import check_website
        check_website(website.id)
        
        flash('网站更新成功')
        return redirect(url_for('main.websites'))
    
    return render_template('main/edit_website.html', form=form, website=website)

@bp.route('/websites/<int:website_id>/delete', methods=['POST'])
@login_required
def delete_website(website_id):
    website = Website.query.get_or_404(website_id)
    
    if not current_user.is_admin() and website.created_by != current_user.id:
        flash('权限不足')
        return redirect(url_for('main.websites'))
    
    # 移除监控任务
    remove_monitor_job(website.id)
    
    db.session.delete(website)
    db.session.commit()
    flash('网站删除成功')
    return redirect(url_for('main.websites'))

@bp.route('/websites/<int:website_id>/alert', methods=['GET', 'POST'])
@login_required
def website_alert(website_id):
    website = Website.query.get_or_404(website_id)
    
    if not current_user.is_admin() and website.created_by != current_user.id:
        flash('权限不足')
        return redirect(url_for('main.websites'))
    
    alert_config = AlertConfig.query.filter_by(website_id=website_id).first()
    form = AlertForm(obj=alert_config)
    
    if form.validate_on_submit():
        if alert_config:
            alert_config.alert_enabled = form.alert_enabled.data
        else:
            alert_config = AlertConfig(
                website_id=website_id,
                alert_enabled=form.alert_enabled.data
            )
            db.session.add(alert_config)
        
        db.session.commit()
        flash('告警配置保存成功')
        return redirect(url_for('main.websites'))
    
    return render_template('main/website_alert.html', form=form, website=website)

@bp.route('/websites/<int:website_id>/logs')
@login_required
def website_logs(website_id):
    website = Website.query.get_or_404(website_id)
    
    if not current_user.is_admin() and website.created_by != current_user.id:
        flash('权限不足')
        return redirect(url_for('main.websites'))
    
    logs = MonitorLog.query.filter_by(website_id=website_id).order_by(MonitorLog.check_time.desc()).limit(100).all()
    return render_template('main/website_logs.html', website=website, logs=logs)

@bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    if current_user.is_admin():
        websites = Website.query.all()
    else:
        websites = Website.query.filter_by(created_by=current_user.id).all()
    
    total_sites = len(websites)
    up_sites = len([w for w in websites if w.status == 'up'])
    down_sites = len([w for w in websites if w.status == 'down'])
    
    return jsonify({
        'total': total_sites,
        'up': up_sites,
        'down': down_sites,
        'uptime': round((up_sites / total_sites * 100) if total_sites > 0 else 0, 1)
    })

@bp.route('/api/websites')
@login_required
def api_websites():
    if current_user.is_admin():
        websites = Website.query.all()
    else:
        websites = Website.query.filter_by(created_by=current_user.id).all()
    
    websites_data = []
    for website in websites:
        websites_data.append({
            'id': website.id,
            'name': website.name,
            'url': website.url,
            'status': website.status,
            'response_time': website.response_time,
            'last_check': website.last_check.strftime('%Y-%m-%d %H:%M') if website.last_check else '从未检查',
            'check_interval': website.check_interval
        })
    
    return jsonify(websites_data)

@bp.route('/websites/<int:website_id>/check-now')
@login_required
def check_now(website_id):
    website = Website.query.get_or_404(website_id)
    
    if not current_user.is_admin() and website.created_by != current_user.id:
        flash('权限不足')
        return redirect(url_for('main.websites'))
    
    # 预先获取名称防止会话分离
    website_name = website.name
    
    # 立即执行检测
    from app.monitor import check_website
    check_website(website_id)
    
    flash(f'已对 {website_name} 执行立即检测')
    return redirect(url_for('main.websites'))

@bp.route('/websites/import', methods=['GET', 'POST'])
@login_required
def import_websites():
    form = ImportExcelForm()
    if form.validate_on_submit():
        file = form.excel_file.data
        filename = secure_filename(file.filename)
        
        try:
            # 文件安全检查
            if file.content_length and file.content_length > 5 * 1024 * 1024:  # 5MB
                flash('文件大小不能超过5MB')
                return render_template('main/import_websites.html', form=form)
            
            # 读取Excel文件（限制行数防止Excel炸弹）
            df = pd.read_excel(file, nrows=1000)  # 最多1000行
            
            # 检查必需列
            required_columns = ['网站名称', 'URL']
            if not all(col in df.columns for col in required_columns):
                flash(f'Excel文件必须包含以下列: {", ".join(required_columns)}')
                return render_template('main/import_websites.html', form=form)
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # 获取数据，使用默认值如果缺失
                    name = str(row['网站名称']).strip()
                    url = str(row['URL']).strip()
                    # URL安全检查
                    if not url.startswith(('http://', 'https://')):
                        error_count += 1
                        continue
                    check_interval = int(row.get('检查间隔', form.check_interval.data))
                    timeout = int(row.get('超时时间', form.timeout.data))
                    
                    # 验证数据
                    if not name or not url:
                        error_count += 1
                        continue
                    
                    # 检查是否已存在
                    existing = Website.query.filter_by(url=url, created_by=current_user.id).first()
                    if existing:
                        error_count += 1
                        continue
                    
                    # 创建网站
                    website = Website(
                        name=name,
                        url=url,
                        check_interval=check_interval,
                        timeout=timeout,
                        created_by=current_user.id
                    )
                    
                    db.session.add(website)
                    db.session.commit()
                    
                    # 添加监控任务
                    add_monitor_job(website.id)
                    
                    # 立即执行一次检测
                    from app.monitor import check_website
                    check_website(website.id)
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    continue
            
            flash(f'导入完成！成功: {success_count} 个，失败: {error_count} 个')
            return redirect(url_for('main.websites'))
            
        except Exception as e:
            flash('文件读取失败，请检查文件格式')
            # 记录详细错误信息到日志
            import logging
            logging.error(f'Excel import error: {str(e)}')
    
    return render_template('main/import_websites.html', form=form)

@bp.route('/websites/download-template')
@login_required
def download_template():
    # 创建模板数据
    template_data = {
        '网站名称': ['示例网站1', '示例网站2'],
        'URL': ['https://example1.com', 'https://example2.com'],
        '检查间隔': [300, 600],
        '超时时间': [10, 15]
    }
    
    df = pd.DataFrame(template_data)
    
    # 保存为临时文件
    from flask import send_file
    import io
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='网站列表')
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='网站导入模板.xlsx'
    )

@bp.route('/websites/<int:website_id>/alerts')
@login_required
def website_alerts(website_id):
    website = Website.query.get_or_404(website_id)
    
    if not current_user.is_admin() and website.created_by != current_user.id:
        flash('权限不足')
        return redirect(url_for('main.websites'))
    
    alerts = AlertLog.query.filter_by(website_id=website_id).order_by(AlertLog.sent_at.desc()).limit(100).all()
    return render_template('main/website_alerts.html', website=website, alerts=alerts)