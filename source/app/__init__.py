from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from datetime import datetime
from flask_bcrypt import Bcrypt
from app.helpers.logging import setup_logger
from app.helpers.db import get_db_connection_string

db = SQLAlchemy()
bcrypt = Bcrypt()

logger = setup_logger()

def init_app():
    logger.info("Initializing app...")
    load_dotenv()

    app = Flask(__name__)

    # App Config
    logger.info("Loading environment variables...")
    app.config["SITE_NAME"] = os.getenv("APP_NAME", "Remindly")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret")  # for sessions
    app.config["SQLALCHEMY_DATABASE_URI"] = get_db_connection_string()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["STATCOUNTER_PROJECT"] = os.getenv("STATCOUNTER_PROJECT")
    app.config["STATCOUNTER_SECURITY"] = os.getenv("STATCOUNTER_SECURITY")

    # Initialize extensions
    logger.info("Initializing extensions...")
    db.init_app(app)
    bcrypt.init_app(app)

    # Make values globally available in Jinja templates
    @app.context_processor
    def inject_globals():
        logger.info("Injecting globals...")
        return {
            "site_name": app.config["SITE_NAME"],
            "current_year": datetime.now().year,
            "statcounter_project": app.config["STATCOUNTER_PROJECT"],
            "statcounter_security": app.config["STATCOUNTER_SECURITY"],
        }

    # Register blueprints
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    logger.info("Registered auth blueprint.")

    from .routes.reminders import reminders_bp
    app.register_blueprint(reminders_bp)
    logger.info("Registered reminders blueprint.")

    logger.info("App initialized.")
    return app
