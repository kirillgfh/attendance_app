from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from app.repositories.user_repository import UserRepository

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'moderator':
            return redirect(url_for('dashboard.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.admin'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = UserRepository.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            flash('Вы успешно вошли в систему!', 'success')
            if user.role == 'moderator':
                return redirect(url_for('dashboard.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.admin'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'moderator':
            return redirect(url_for('dashboard.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.admin'))
    return redirect(url_for('auth.login'))