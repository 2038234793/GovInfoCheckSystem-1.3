import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
# 初始化 SocketIO
socketio = SocketIO(async_mode='threading')

def create_app():
    base_dir = os.path.dirname(__file__)
    template_folder = os.path.join(base_dir, '..', 'templates')
    static_folder = os.path.join(base_dir, '..', 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    db_file = os.path.join(base_dir, '..', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_file}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # 绑定 SocketIO 到应用
    socketio.init_app(app, cors_allowed_origins='*')

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from .collect import bp as collect_bp
    app.register_blueprint(collect_bp, url_prefix='/collect')

    from .warehouse import bp as warehouse_bp
    app.register_blueprint(warehouse_bp, url_prefix='/warehouse')

    from .rules import bp as rules_bp
    app.register_blueprint(rules_bp, url_prefix='/rules')

    from .ai_engine import bp as ai_engine_bp
    app.register_blueprint(ai_engine_bp, url_prefix='/ai_engine')

    from .crawler_mgmt import bp as crawler_mgmt_bp
    app.register_blueprint(crawler_mgmt_bp, url_prefix='/crawler_mgmt')

    from .ai_analysis import bp as ai_analysis_bp
    app.register_blueprint(ai_analysis_bp, url_prefix='/ai_analysis')

    from .dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    # 注册聊天插件蓝图
    from .plugins.chatroom import chatroom_bp
    app.register_blueprint(chatroom_bp)

    # Register Data Dashboard Plugin Blueprint
    from .plugins.data_dashboard import dashboard_bp as data_dashboard_bp
    app.register_blueprint(data_dashboard_bp)

    # Register Report Management Plugin Blueprint
    from .plugins.report_mgmt import report_mgmt_bp
    app.register_blueprint(report_mgmt_bp)

    # Register Pachong Plugin Blueprint
    from .plugins.pachong.pachong import pachong_bp
    app.register_blueprint(pachong_bp)

    with app.app_context():
        from . import models
        # Create tables is handled by migrate, but for dev we can check
        pass

    return app
