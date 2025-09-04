from datetime import date, datetime
from flask import session
from .. import db
from sqlalchemy.orm import aliased
#from sqlalchemy.dialects import mysql # For debugging only
from app.models.reminder import Reminder
from app.models.shared_reminder import SharedReminder
from app.models.user import User
from app.helpers.reminders import get_reminder_next_occurrence
from app.helpers.logging import setup_logger


logger = setup_logger()


def get_my_total_reminders_count():
    logger.info("my_total_reminders_count() called")
    session_user_uuid = session.get("user_uuid")
    count = Reminder.query.filter_by(reminder_user_uuid=session_user_uuid, is_deleted=False).count()
    logger.debug("my_total_reminders_count: %s", count)
    return count


def get_my_total_shared_reminders_count():
    logger.info("my_total_shared_reminders_count() called")
    session_user_uuid = session.get("user_uuid")
    
    # Join the share_reminders table with reminders table to get reminders that are shared with the logged-in user
    count = ( db.session.query(SharedReminder, User, Reminder)
                .join(Reminder, SharedReminder.shared_reminder_reminder_uuid == Reminder.reminder_uuid)
                .join(User, SharedReminder.shared_reminder_user_uuid == User.user_uuid)
                .filter(
                    SharedReminder.shared_reminder_user_uuid == session_user_uuid,
                    SharedReminder.is_deleted == False,
                    Reminder.is_deleted == False,
                    User.is_deleted == False
                )
                .count()
            )

    logger.debug("my_total_shared_reminders_count: %s", count)
    return count


def get_upcoming_my_non_recurring_reminders_list():
    logger.info("get_upcoming_my_non_recurring_reminders_list() called")
    session_user_uuid = session.get("user_uuid")

    upcoming_my_non_recurring_reminders_list = ( db.session.query(Reminder)
        .filter(
            Reminder.reminder_user_uuid == session_user_uuid,
            Reminder.reminder_recurrence_type == "NONE",
            Reminder.reminder_is_completed == False,
            Reminder.is_deleted == False,
            Reminder.reminder_date_end >= datetime.utcnow()
        )
        .order_by(Reminder.reminder_date_end)
        .limit(5)
        .all()
    )

    logger.debug("upcoming_my_non_recurring_reminders_list: %s", upcoming_my_non_recurring_reminders_list)
    return upcoming_my_non_recurring_reminders_list


def get_upcoming_my_recurring_reminders_list():
    logger.info("get_upcoming_my_recurring_reminders_list() called")
    session_user_uuid = session.get("user_uuid")

    # Note: If recurring, no filtering on end date as end date is not mandatory

    upcoming_my_recurring_reminders_query = (
        Reminder.query
        .filter(
            Reminder.reminder_user_uuid == session_user_uuid,
            Reminder.reminder_recurrence_type != "NONE",
            Reminder.reminder_is_completed == False,
            Reminder.is_deleted == False,
        )
        .order_by(Reminder.reminder_date_start)
    )
    #TODO: Consider storing the next one occurrence in the database else this query needs to pull all reminders from the database for that user each time.

    upcoming_my_recurring_reminders_list = upcoming_my_recurring_reminders_query.all()

    # Get next 1 occurence for each reminder
    for reminder in upcoming_my_recurring_reminders_list:
        # Dynamically add 'Reminder Next Occurrence' property - next 1 occurrence
        # Property to only use for display
        reminder.reminder_display_date_next_occurrence = None

        # Property to only use for sorting
        reminder.reminder_sort_date_next_occurrence = None

        # Calculate next occurrence
        reminder_display_date_next_occurrence, reminder_sort_date_next_occurrence = get_reminder_next_occurrence(
            reminder.reminder_uuid,
            reminder.reminder_recurrence_type,
            reminder.reminder_recurrence_rrule,
            reminder.reminder_date_start,
            reminder.reminder_date_end
        )

        logger.debug("reminder_display_date_next_occurrence: %s", reminder_display_date_next_occurrence)
        logger.debug("reminder_sort_date_next_occurrence: %s", reminder_sort_date_next_occurrence)

        reminder.reminder_display_date_next_occurrence = reminder_display_date_next_occurrence
        reminder.reminder_sort_date_next_occurrence = reminder_sort_date_next_occurrence


    # Order reminders by next occurrence date and limit 5
    upcoming_my_recurring_reminders_list.sort(key=lambda x: x.reminder_sort_date_next_occurrence)
    upcoming_my_recurring_reminders_list = upcoming_my_recurring_reminders_list[:5]

    logger.debug("upcoming_my_recurring_reminders_list: %s", upcoming_my_recurring_reminders_list)
    return upcoming_my_recurring_reminders_list


def get_upcoming_shared_non_recurring_reminders_list():
    logger.info("get_upcoming_shared_non_recurring_reminders_list() called")
    session_user_uuid = session.get("user_uuid")

     # Aliases for User table
    user_reminder_shared_with = aliased(User)
    user_reminder_owner = aliased(User)

    upcoming_shared_non_recurring_reminders_list = (
        db.session.query(Reminder, SharedReminder, user_reminder_shared_with, user_reminder_owner)
        # Join shared reminder
        .join(SharedReminder, SharedReminder.shared_reminder_reminder_uuid == Reminder.reminder_uuid)
        # Join the user the reminder is shared with
        .join(user_reminder_shared_with, SharedReminder.shared_reminder_user_uuid == user_reminder_shared_with.user_uuid)
        # Join the owner of the reminder
        .join(user_reminder_owner, Reminder.reminder_user_uuid == user_reminder_owner.user_uuid)
        .filter(
            SharedReminder.shared_reminder_user_uuid == session_user_uuid,
            SharedReminder.is_deleted == False,
            Reminder.is_deleted == False,
            user_reminder_shared_with.is_deleted == False,
            user_reminder_owner.is_deleted == False,
            Reminder.reminder_recurrence_type == "NONE",
            Reminder.reminder_is_completed == False,
            Reminder.reminder_date_end >= datetime.utcnow(),
        )
        .order_by(Reminder.reminder_date_end)
        .limit(5)
        .all()
    )

    logger.debug("upcoming_shared_non_recurring_reminders_list: %s", upcoming_shared_non_recurring_reminders_list)
    return upcoming_shared_non_recurring_reminders_list


def get_upcoming_shared_recurring_reminders_list():
    logger.info("get_upcoming_shared_recurring_reminders_list() called")
    session_user_uuid = session.get("user_uuid")

     # Aliases for User table
    user_reminder_shared_with = aliased(User)
    user_reminder_owner = aliased(User)

    # Note: If recurring, no filtering on end date as end date is not mandatory

    upcoming_shared_recurring_reminders_list = (
        db.session.query(Reminder, SharedReminder, user_reminder_shared_with, user_reminder_owner)
        # Join shared reminder
        .join(SharedReminder, SharedReminder.shared_reminder_reminder_uuid == Reminder.reminder_uuid)
        # Join the user the reminder is shared with
        .join(user_reminder_shared_with, SharedReminder.shared_reminder_user_uuid == user_reminder_shared_with.user_uuid)
        # Join the owner of the reminder
        .join(user_reminder_owner, Reminder.reminder_user_uuid == user_reminder_owner.user_uuid)
        .filter(
            SharedReminder.shared_reminder_user_uuid == session_user_uuid,
            SharedReminder.is_deleted == False,
            Reminder.is_deleted == False,
            user_reminder_shared_with.is_deleted == False,
            user_reminder_owner.is_deleted == False,
            Reminder.reminder_recurrence_type != "NONE",
            Reminder.reminder_is_completed == False
        )
        .order_by(Reminder.reminder_date_start)
        .all()
    )

    #TODO: Consider storing the next one occurrence in the database

    # Get next 1 occurence for each reminder
    for reminder, shared_reminder, user_reminder_shared_with, user_reminder_owner in upcoming_shared_recurring_reminders_list:
        # Dynamically add 'Reminder Next Occurrence' property - next 1 occurrence
        # Property to only use for display
        reminder.reminder_display_date_next_occurrence = None

        # Property to only use for sorting
        reminder.reminder_sort_date_next_occurrence = None

        # Calculate next occurrence
        reminder_display_date_next_occurrence, reminder_sort_date_next_occurrence = get_reminder_next_occurrence(
            reminder.reminder_uuid,
            reminder.reminder_recurrence_type,
            reminder.reminder_recurrence_rrule,
            reminder.reminder_date_start,
            reminder.reminder_date_end
        )

        logger.debug("reminder_display_date_next_occurrence: %s", reminder_display_date_next_occurrence)
        logger.debug("reminder_sort_date_next_occurrence: %s", reminder_sort_date_next_occurrence)

        reminder.reminder_display_date_next_occurrence = reminder_display_date_next_occurrence
        reminder.reminder_sort_date_next_occurrence = reminder_sort_date_next_occurrence


    # Order reminders by next occurrence date
    upcoming_shared_recurring_reminders_list.sort(key=lambda x: x[0].reminder_sort_date_next_occurrence)

    # Limit to 5 records
    upcoming_shared_recurring_reminders_list = upcoming_shared_recurring_reminders_list[:5]

    logger.debug("upcoming_shared_recurring_reminders_list: %s", upcoming_shared_recurring_reminders_list)
    return upcoming_shared_recurring_reminders_list


def get_overdue_my_non_recurring_reminders_list():
    logger.info("get_overdue_my_non_recurring_reminders_list() called")
    session_user_uuid = session.get("user_uuid")

    overdue_my_non_recurring_reminders_list = ( db.session.query(Reminder)
        .filter(
            Reminder.reminder_user_uuid == session_user_uuid,
            Reminder.reminder_recurrence_type == "NONE",
            Reminder.reminder_is_completed == False,
            Reminder.is_deleted == False,
            Reminder.reminder_date_end < datetime.utcnow(),
        )
        .order_by(Reminder.reminder_date_end)
        .limit(5)
        .all()
    )

    logger.debug("overdue_my_non_recurring_reminders_list: %s", overdue_my_non_recurring_reminders_list)
    return overdue_my_non_recurring_reminders_list


def get_overdue_shared_non_recurring_reminders_list():
    logger.info("get_overdue_shared_non_recurring_reminders_list() called")
    session_user_uuid = session.get("user_uuid")

    # Aliases for User table
    user_reminder_shared_with = aliased(User)
    user_reminder_owner = aliased(User)

    overdue_shared_non_recurring_reminders_list = (
        db.session.query(Reminder, SharedReminder, user_reminder_shared_with, user_reminder_owner)
        # Join shared reminder
        .join(SharedReminder, SharedReminder.shared_reminder_reminder_uuid == Reminder.reminder_uuid)
        # Join the user the reminder is shared with
        .join(user_reminder_shared_with, SharedReminder.shared_reminder_user_uuid == user_reminder_shared_with.user_uuid)
        # Join the owner of the reminder
        .join(user_reminder_owner, Reminder.reminder_user_uuid == user_reminder_owner.user_uuid)
        .filter(
            SharedReminder.shared_reminder_user_uuid == session_user_uuid,
            SharedReminder.is_deleted == False,
            Reminder.is_deleted == False,
            user_reminder_shared_with.is_deleted == False,
            user_reminder_owner.is_deleted == False,
            Reminder.reminder_recurrence_type == "NONE",
            Reminder.reminder_is_completed == False,
            Reminder.reminder_date_end < datetime.utcnow(),
        )
        .order_by(Reminder.reminder_date_end)
        .limit(5)
        .all()
    )

    logger.debug("overdue_shared_non_recurring_reminders_list: %s", overdue_shared_non_recurring_reminders_list)
    return overdue_shared_non_recurring_reminders_list