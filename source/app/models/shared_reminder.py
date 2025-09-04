from datetime import datetime
import uuid
from .. import db
from app.helpers.logging import setup_logger


logger = setup_logger()


class SharedReminder(db.Model):
    logger.debug("SharedReminder Model class initialized")

    __tablename__ = "shared_reminders"

    shared_reminder_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    shared_reminder_uuid = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    shared_reminder_reminder_uuid = db.Column(db.String(255), nullable=False)
    shared_reminder_user_uuid = db.Column(db.String(255), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_on = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=db.func.current_timestamp(), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return "<SharedReminder {}>".format(self.shared_reminder_uuid)
