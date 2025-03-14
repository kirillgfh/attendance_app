from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user  # Импортируем current_user

def role_required(role_list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.role not in role_list:
                flash('Вы не имеете доступа к этой странице.', 'danger')
                return redirect(url_for('logout'))
            return func(*args, **kwargs)
        return wrapper
    return decorator