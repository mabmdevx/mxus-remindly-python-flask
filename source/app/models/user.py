from datetime import datetime
import uuid
from .. import db
from app.helpers.logging import setup_logger


logger = setup_logger()


class User(db.Model):
    logger.debug("User Model class initialized")

    __tablename__ = "users"

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_uuid = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_username = db.Column(db.String(255), nullable=False)
    user_password = db.Column(db.String(255), nullable=False)
    user_email = db.Column(db.String(255), nullable=False)
    user_alert_webhook_url = db.Column(db.String(500), nullable=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_on = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=db.func.current_timestamp(), nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<User {self.user_username}>"
