from .. import db

# Import each model so it's registered with SQLAlchemy
from app.models.user import User
from app.models.reminder import Reminder
from app.models.shared_reminder import SharedReminder
