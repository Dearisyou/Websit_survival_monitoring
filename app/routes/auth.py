from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.forms import LoginForm, UserForm, ChangePasswordForm
from app import db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    from app.security import rate_limit, audit_log
    import os
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # 检查密码文件是否存在
    admin_password_exists = os.path.exists('admin_password.txt')
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            audit_log('LOGIN_SUCCESS', f'User: {user.username}')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        audit_log('LOGIN_FAILED', f'Username: {form.username.data}')
        flash('用户名或密码错误')
    
    return render_template('auth/login.html', form=form, admin_password_exists=admin_password_exists)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/users')
@login_required
def users():
    if not current_user.is_admin():
        flash('权限不足')
        return redirect(url_for('main.dashboard'))
    
    users = User.query.all()
    return render_template('auth/users.html', users=users)

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin():
        flash('权限不足')
        return redirect(url_for('main.dashboard'))
    
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('用户创建成功')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/create_user.html', form=form)

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        flash('权限不足')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能删除自己的账号')
        return redirect(url_for('auth.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功')
    return redirect(url_for('auth.users'))

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash('当前密码错误')
            return render_template('auth/change_password.html', form=form)
        
        if form.new_password.data != form.confirm_password.data:
            flash('两次输入的新密码不一致')
            return render_template('auth/change_password.html', form=form)
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('密码修改成功')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/change_password.html', form=form)