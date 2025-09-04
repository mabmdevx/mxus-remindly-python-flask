from datetime import datetime
import uuid
from .. import db
from app.models.shared_reminder import SharedReminder
from app.models.user import User
from dateutil.rrule import rrulestr
from app.helpers.logging import setup_logger


logger = setup_logger()


class Reminder(db.Model):
    logger.debug("Reminder Model class initialized")

    __tablename__ = "reminders"

    reminder_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    reminder_uuid = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    reminder_url_slug = db.Column(db.String(255), unique=True, nullable=False)
    reminder_title = db.Column(db.String(255), nullable=False)
    reminder_desc = db.Column(db.String(1000), nullable=True)
    reminder_link = db.Column(db.String(1000), nullable=True)
    reminder_type = db.Column(db.String(255), nullable=False)

    # Reminder recurrence type
    # Values = NONE (one-time), DAILY, WEEKLY, MONTHLY, YEARLY, CUSTOM)
    reminder_recurrence_type = db.Column(
        db.String(20), nullable=False, default="NONE"
    )

    # Reminder recurrence RRULE
    # Full iCal RRULE string
    reminder_recurrence_rrule = db.Column(db.Text, nullable=True)

    reminder_date_start = db.Column(db.Date, nullable=True)
    reminder_date_end = db.Column(db.Date, nullable=False)
    reminder_is_completed = db.Column(db.Boolean, nullable=False, default=False)
    reminder_user_uuid = db.Column(db.String(255), nullable=False)
    
    created_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_on = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=db.func.current_timestamp(), nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Reminder {self.reminder_title}>"


    # Not a DB foreign key, just a convenience property
    @property
    def reminder_shared_with(self):
        """
        Returns a list of (SharedReminder, User) tuples
        for all users this reminder is shared with.
        """
        logger.debug("reminder_shared_with property called")

        return (
            db.session.query(SharedReminder, User, Reminder)
            .join(Reminder, SharedReminder.shared_reminder_reminder_uuid == Reminder.reminder_uuid)
            .join(User, SharedReminder.shared_reminder_user_uuid == User.user_uuid)
            .filter(
                SharedReminder.shared_reminder_reminder_uuid == self.reminder_uuid,
                SharedReminder.is_deleted == False,
                Reminder.is_deleted == False,
                User.is_deleted == False
            )
            .all()
        )
