from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
import os

db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object('app.config.Config')  # Указываем путь к конфигурации

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    login_manager_view = 'auth.login'  # Указываем маршрут для перенаправления неавторизованных пользователей
    cache.init_app(app)

    # Регистрация функции загрузки пользователя
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User  # Импорт внутри функции, чтобы избежать циклического импорта
        return db.session.get(User, int(user_id))  # Загружаем пользователя по ID

    # Регистрация blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Создание таблиц
    with app.app_context():
        db.create_all()

    return app