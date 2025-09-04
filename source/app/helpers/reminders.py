from datetime import datetime, date
from app.helpers.rrule import get_next_occurrences_date_only
from app.helpers.logging import setup_logger
import requests


logger = setup_logger()


def get_reminder_next_occurrence(reminder_uuid, reminder_recurrence_type, reminder_recurrence_rrule, reminder_date_start, reminder_date_end):
    """
    Returns a tuple: (reminder_display_date_next_occurrence, reminder_sort_date_next_occurrence)
    based on recurrence type, recurrence rrule, and end date.

    - reminder_recurrence_type: string, e.g., "NONE", "DAILY", etc.
    - reminder_recurrence_rrule: string rrule, e.g., "FREQ=DAILY;INTERVAL=1"
    - reminder_date_end: date object or None
    """
    logger.info("get_reminder_next_occurrence() called")

    reminder_display_date_next_occurrence = None
    reminder_sort_date_next_occurrence = None

    if reminder_recurrence_type == "NONE":
        logger.debug("reminder_recurrence_type is NONE (Non-Recurring)")

        # Get Reminder Due Date/ End Date
        if reminder_date_end:
            reminder_display_date_next_occurrence = reminder_date_end
            reminder_sort_date_next_occurrence = reminder_date_end
            logger.debug(
                "reminder_display_date_next_occurrence is the end date due to non-recurring: %s",
                reminder_display_date_next_occurrence
            )
        else:
            # This is unlikely to happen since it's mandatory for non-recurring reminders to have an end date
            reminder_display_date_next_occurrence = "N/A"
            reminder_sort_date_next_occurrence = date.min
            logger.error(
                "ERROR: reminder_display_date_next_occurrence - unlikely scenario happened for reminder_uuid: %s | %s", 
                reminder_uuid,
                reminder_display_date_next_occurrence
            )
    else:
        logger.debug("reminder_recurrence_type is NOT NONE (Recurring)")

        # Get next 1 occurrence
        next_occurrence = get_next_occurrences_date_only(reminder_date_start, reminder_recurrence_rrule, count=1)

        if next_occurrence and next_occurrence[0]:
            display_date_next_occurrence_to_date = datetime.strptime(next_occurrence[0], "%Y-%m-%d").date()
            sort_date_next_occurrence_to_date = datetime.strptime(next_occurrence[0], "%Y-%m-%d").date()

            logger.debug("display_date_next_occurrence_to_date: %s", display_date_next_occurrence_to_date)
            logger.debug("sort_date_next_occurrence_to_date: %s", sort_date_next_occurrence_to_date)

            # Check if the next occurrence is not in the past
            if sort_date_next_occurrence_to_date < date.today():
                # If the next occurrence is in the past, set to "N/A"
                reminder_display_date_next_occurrence = "N/A"
                reminder_sort_date_next_occurrence = date.min
                logger.debug(
                    "reminder_display_date_next_occurrence is in the past: %s",
                    reminder_display_date_next_occurrence
                )
            else:
                # If the next occurrence is now or in the future, set to the date
                reminder_display_date_next_occurrence = display_date_next_occurrence_to_date
                reminder_sort_date_next_occurrence = sort_date_next_occurrence_to_date
                logger.debug(
                    "reminder_display_date_next_occurrence is now or in the future: %s",
                    reminder_display_date_next_occurrence
                )
        else:
            # In case there are no more occurrences - cases where recurrence type and end date leads to no occurrences
            reminder_display_date_next_occurrence = "N/A"
            reminder_sort_date_next_occurrence = date.min
            logger.debug(
                "reminder_display_date_next_occurrence has no more occurrences: %s",
                reminder_display_date_next_occurrence
            )

    return reminder_display_date_next_occurrence, reminder_sort_date_next_occurrence


# Function to send alert notification
def send_alert_notification(reminder_shared_type, user_alert_webhook_url, reminder_title, reminder_due_date):
    payload = {
        "text": f"Remindly Alert for {reminder_shared_type} Reminder : {reminder_title} - Due date {reminder_due_date} is approaching!"
    }
    response = requests.post(user_alert_webhook_url, json=payload)
    if response.status_code == 200:
        print("Notification sent successfully!")
        return True
    else:
        print("Error sending notification:", response.text)
        return False