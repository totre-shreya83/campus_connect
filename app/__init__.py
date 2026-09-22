
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from config import config_by_name

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def create_app(config_name="development"):
    app = Flask(__name__)

    app.config.from_object(
        config_by_name[config_name]
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"

    
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.notes import notes_bp
    app.register_blueprint(notes_bp)

    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    from app.routes.requests import requests_bp
    app.register_blueprint(requests_bp)

    from app.routes.notifications import notifications_bp
    app.register_blueprint(notifications_bp)

    from app.routes.placement import placement_bp
    app.register_blueprint(placement_bp)

    from app.routes.quiz import quiz_bp
    app.register_blueprint(quiz_bp)

    @app.context_processor
    def inject_unread_count():
        from flask_login import current_user

        if current_user.is_authenticated:
            from app.services.notification_service import get_unread_count

            return {
                "unread_count": get_unread_count(current_user.id)
            }

        return {
            "unread_count": 0
        }

    return app


