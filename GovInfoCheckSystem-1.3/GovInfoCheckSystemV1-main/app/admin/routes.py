from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Role, SystemSetting
from . import bp
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('需要管理员权限')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html')

@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin/users.html', users=users, roles=roles)

@bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role_id = request.form.get('role_id')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('admin.users')) # Redirect to list for modal add
            
        user = User(username=username)
        user.password = password
        user.role_id = role_id
        
        db.session.add(user)
        db.session.commit()
        flash('用户添加成功')
        return redirect(url_for('admin.users'))
        
    roles = Role.query.all()
    return render_template('admin/user_form.html', roles=roles, title='添加用户')

@bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role_id = request.form.get('role_id')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('用户名已存在')
            return redirect(url_for('admin.edit_user', user_id=user.id))
            
        user.username = username
        if password:
            user.password = password
        user.role_id = role_id
        
        db.session.commit()
        flash('用户更新成功')
        return redirect(url_for('admin.users'))
        
    roles = Role.query.all()
    return render_template('admin/user_form.html', user=user, roles=roles, title='编辑用户')

@bp.route('/users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能删除自己')
        return redirect(url_for('admin.users'))
        
    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功')
    return redirect(url_for('admin.users'))

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        app_name = request.form.get('app_name')
        # app_logo = request.form.get('app_logo') # File upload logic can be added later
        
        setting_name = SystemSetting.query.filter_by(key='app_name').first()
        if not setting_name:
            setting_name = SystemSetting(key='app_name')
            db.session.add(setting_name)
        setting_name.value = app_name
        db.session.commit()
        flash('设置已更新')
        
    app_name = SystemSetting.get_value('app_name', '政企智能舆情分析报告生成智能体应用系统')
    return render_template('admin/settings.html', app_name=app_name)