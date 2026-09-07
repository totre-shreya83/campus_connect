from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

from config import config_by_name


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app(config_name="development"):
    app = Flask(__name__)

    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
   # login_manager.init_app(app)
    bcrypt.init_app(app)

    #login_manager.login_view = "auth.login"

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app