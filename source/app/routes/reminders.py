# routes/reminder_routes.py
from flask import Blueprint, abort, jsonify, render_template, request, redirect, url_for, flash
import random
import string
from .. import db
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta
import uuid
from app.models.user import User
from app.models.reminder import Reminder
from app.models.shared_reminder import SharedReminder
from app.helpers.reminders import get_reminder_next_occurrence, send_alert_notification
from app.helpers.auth import check_login_for_page, check_login_for_api
from app.helpers.rrule import build_rrule_string, parse_rrule, get_next_occurrences_date_only
from app.helpers.stats import (
    get_my_total_reminders_count,
    get_my_total_shared_reminders_count,
    get_upcoming_my_non_recurring_reminders_list,
    get_upcoming_my_recurring_reminders_list,
    get_upcoming_shared_non_recurring_reminders_list,
    get_upcoming_shared_recurring_reminders_list,
    get_overdue_my_non_recurring_reminders_list,
    get_overdue_shared_non_recurring_reminders_list
)
from app.helpers.logging import setup_logger


logger = setup_logger()
reminders_bp = Blueprint("reminders", __name__)


# Dashboard
@reminders_bp.route("/dashboard")
def dashboard():
    logger.info("/dashboard route called")

     # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    
    # Get stats
    my_total_reminders_count = get_my_total_reminders_count()
    my_total_shared_reminders_count = get_my_total_shared_reminders_count()
    upcoming_my_non_recurring_reminders_list = get_upcoming_my_non_recurring_reminders_list()
    upcoming_my_recurring_reminders_list = get_upcoming_my_recurring_reminders_list()
    upcoming_shared_non_recurring_reminders_list = get_upcoming_shared_non_recurring_reminders_list()
    upcoming_shared_recurring_reminders_list = get_upcoming_shared_recurring_reminders_list()
    overdue_my_non_recurring_reminders_list = get_overdue_my_non_recurring_reminders_list()
    overdue_shared_non_recurring_reminders_list = get_overdue_shared_non_recurring_reminders_list()

    return render_template("auth_pages/dashboard.html", 
        my_total_reminders_count=my_total_reminders_count,
        my_total_shared_reminders_count=my_total_shared_reminders_count,
        upcoming_my_non_recurring_reminders_list=upcoming_my_non_recurring_reminders_list,
        upcoming_my_recurring_reminders_list=upcoming_my_recurring_reminders_list,
        upcoming_shared_non_recurring_reminders_list=upcoming_shared_non_recurring_reminders_list,
        upcoming_shared_recurring_reminders_list=upcoming_shared_recurring_reminders_list,
        overdue_my_non_recurring_reminders_list=overdue_my_non_recurring_reminders_list,
        overdue_shared_non_recurring_reminders_list=overdue_shared_non_recurring_reminders_list
    )


# My Reminders - List all reminders
@reminders_bp.route("/my-reminders")
def my_reminders():
    logger.info("/my-reminders route called")

    # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    else:
        session_user_uuid = check_login_result
    
    # Get reminders that belong to the logged-in user
    my_reminders = Reminder.query.filter_by(
        reminder_user_uuid=session_user_uuid,
        is_deleted=False
    ).order_by(Reminder.reminder_date_start).all()


    # Add dynamic properties
    for reminder in my_reminders:
        # Dynamically add 'reminder_is_shared' property
        reminder.reminder_is_shared = len(reminder.reminder_shared_with) > 0

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
    

    # Sort by next occurrence
    my_reminders = sorted(my_reminders, key=lambda x: x.reminder_sort_date_next_occurrence)

    return render_template(
        "auth_pages/reminder_list_mine.html",
        my_reminders=my_reminders
    )


@reminders_bp.route("/reminders-shared-with-me")
def reminders_shared_with_me():
    logger.info("/reminders-shared-with-me route called")

    # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    else:
        session_user_uuid = check_login_result

    # Aliases for User table
    user_reminder_shared_with = aliased(User)
    user_reminder_owner = aliased(User)
    
    # Get reminders that are shared with the logged-in user
    my_shared_reminders = (
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
                user_reminder_owner.is_deleted == False
            )
            .order_by(Reminder.reminder_date_start)
            .all()
    )

    # For debugging only, hence commented out
    """
    for reminder, shared, user_reminder_shared_with, user_reminder_owner in my_shared_reminders:
        logger.debug(reminder.reminder_title)
        logger.debug(shared.shared_reminder_user_uuid)
        logger.debug(user_reminder_shared_with.user_username)
        logger.debug(user_reminder_owner.user_username)
        logger.debug("---\n")
    """


    # Add dynamic properties
    for reminder, shared, user_reminder_shared_with, user_reminder_owner in my_shared_reminders:
        
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
    

    # Sort by next occurrence
    my_shared_reminders = sorted(my_shared_reminders, key=lambda x: x[0].reminder_sort_date_next_occurrence)

    return render_template("auth_pages/reminder_list_shared.html", my_shared_reminders=my_shared_reminders)


# Create Reminder
@reminders_bp.route("/create-reminder", methods=["GET", "POST"])
def create_reminder():
    logger.info("/create-reminder route called")

    # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    else:
        session_user_uuid = check_login_result

    if request.method == "POST":
        logger.info("Creating Reminder...")

        reminder_title = request.form.get("reminder_title")
        reminder_desc = request.form.get("reminder_desc")
        reminder_link = request.form.get("reminder_link")
        reminder_type = request.form.get("reminder_type")

        # Dates
        reminder_date_start = request.form.get("reminder_date_start")
        reminder_date_end = request.form.get("reminder_date_end")

        # Dates Processed
        reminder_date_start_processed = datetime.strptime(reminder_date_start, "%Y-%m-%d").date() if reminder_date_start else None
        reminder_date_end_processed = datetime.strptime(reminder_date_end, "%Y-%m-%d").date() if reminder_date_end else None

        # Recurrence
        reminder_recurrence_type = request.form.get("reminder_recurrence_type", "NONE")

         # Is Completed
        reminder_is_completed = bool(request.form.get("reminder_is_completed"))


        # Validations
        # Check if reminder_date_start is before reminder_date_end
        if reminder_date_start_processed and reminder_date_end_processed and reminder_date_start_processed > reminder_date_end_processed:
            logger.info("Validation: Reminder Date End must be after Reminder Date Start")
            flash("Reminder Date End must be after Reminder Date Start", "error")
            msg_error = "Reminder Date End must be after Reminder Date Start"
            return render_template("auth_pages/reminder_form.html", reminder=None, form_mode="ADD", msg_error=msg_error)

        # Check Date Mandatory Behavior
        # If reminder recurrence type is "NONE", "Start Date" is optional, "End Date" is mandatory
        # If reminder recurrence type is not "NONE", "Start Date" is mandatory, "End Date" is optional
        if reminder_recurrence_type == "NONE":
            if reminder_date_start_processed and not reminder_date_end_processed:
                logger.info("Validation: Reminder Date End is mandatory when Reminder Recurrence Type is NONE")
                flash("Reminder Date End is mandatory when Reminder Recurrence Type is NONE", "error")
                msg_error = "Reminder Date End is mandatory when Reminder Recurrence Type is NONE"
                return render_template("auth_pages/reminder_form.html", reminder=None, form_mode="ADD", msg_error=msg_error)
        else:
            if not reminder_date_start_processed and reminder_date_end_processed:
                logger.info("Validation: Reminder Date Start is mandatory when Reminder Recurrence Type is not NONE")
                flash("Reminder Date Start is mandatory when Reminder Recurrence Type is not NONE", "error")
                msg_error = "Reminder Date Start is mandatory when Reminder Recurrence Type is not NONE"
                return render_template("auth_pages/reminder_form.html", reminder=None, form_mode="ADD", msg_error=msg_error)


        # For debugging only, hence commented out
        """
        logger.debug(f"Reminder Title: {reminder_title}")
        logger.debug(f"Reminder Description: {reminder_desc}")
        logger.debug(f"Reminder Link: {reminder_link}")
        logger.debug(f"Reminder Type: {reminder_type}")
        logger.debug(f"Reminder Date Start: {reminder_date_start}")
        logger.debug(f"Reminder Date End: {reminder_date_end}")
        logger.debug(f"Reminder Date Start Processed: {reminder_date_start_processed}")
        logger.debug(f"Reminder Date End Processed: {reminder_date_end_processed}")
        logger.debug(f"Reminder Recurrence Type: {reminder_recurrence_type}")
        logger.debug(f"Reminder Is Completed: {reminder_is_completed}")
        """


        # Build RRULE
        rrule_str = build_rrule_string(reminder_recurrence_type, reminder_date_start, reminder_date_end, interval=1, byweekday=[], bymonthday=None)
        logger.info(f"RRULE: {rrule_str}")

        # Generate a unique reminder_url_slug - 8 character alphanumeric string
        reminder_url_slug = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        logger.info(f"Reminder URL Slug: {reminder_url_slug}")

        reminder = Reminder(
            reminder_url_slug=reminder_url_slug,
            reminder_title=reminder_title,
            reminder_desc=reminder_desc,
            reminder_link=reminder_link,
            reminder_type=reminder_type,
            reminder_recurrence_type=reminder_recurrence_type,
            reminder_recurrence_rrule=rrule_str,
            reminder_date_start=reminder_date_start_processed,
            reminder_date_end=reminder_date_end_processed,
            reminder_is_completed=reminder_is_completed,
            reminder_user_uuid=session_user_uuid
        )

        db.session.add(reminder)
        db.session.commit()
        logger.info("Reminder created successfully!, Reminder UUID: %s", reminder.reminder_uuid)
        flash("Reminder created successfully!", "success")
        return redirect(url_for("reminders.my_reminders"))

    return render_template("auth_pages/reminder_form.html", reminder=None, form_mode="Add", msg_error=None)


# Update Reminder by reminder_uuid
@reminders_bp.route("/update-reminder/<string:reminder_uuid>", methods=["GET", "POST"])
def update_reminder(reminder_uuid):
    logger.info("/update-reminder route called")

    # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    else:
        session_user_uuid = check_login_result

    # Fetch the reminder by Reminder UUID
    reminder = Reminder.query.filter_by(reminder_uuid=reminder_uuid, is_deleted=False).first_or_404()

    # Ensure reminder exists
    if not reminder:
        logger.error("Reminder not found")
        abort(404, description="Reminder not found")

    # Check if the reminder belongs to the user
    if reminder.reminder_user_uuid != session_user_uuid:
        logger.error("You are not authorized to update this reminder")
        abort(403, description="You are not authorized to update this reminder")

    parsed_rrule = None
    next_occurrences = []

    # If recurring, Get the Parsed RRULE and next 5 occurrences
    if reminder.reminder_recurrence_type != "NONE" and reminder.reminder_recurrence_rrule:
        parsed_rrule = parse_rrule(reminder.reminder_recurrence_rrule)
        next_occurrences = get_next_occurrences_date_only(reminder.reminder_date_start, reminder.reminder_recurrence_rrule, count=5)

    if request.method == "POST":
        logger.info("Updating Reminder...")

        reminder_title = request.form.get("reminder_title")
        reminder_desc = request.form.get("reminder_desc")
        reminder_link = request.form.get("reminder_link")
        reminder_type = request.form.get("reminder_type")

        # Dates
        reminder_date_start = request.form.get("reminder_date_start")
        reminder_date_end = request.form.get("reminder_date_end")
        
        # Dates Processed
        reminder_date_start_processed = datetime.strptime(reminder_date_start, "%Y-%m-%d").date() if reminder_date_start else None
        reminder_date_end_processed = datetime.strptime(reminder_date_end, "%Y-%m-%d").date() if reminder_date_end else None

        # Recurrence
        reminder_recurrence_type = request.form.get("reminder_recurrence_type", "NONE")

        # Is Completed
        reminder_is_completed = bool(request.form.get("reminder_is_completed"))
    

        # Validations
        # Check if reminder_date_start is before reminder_date_end
        if reminder_date_start_processed and reminder_date_end_processed and reminder_date_start_processed > reminder_date_end_processed:
            logger.info("Validation: Reminder Date End must be after Reminder Date Start")
            flash("Reminder Date End must be after Reminder Date Start", "error")
            msg_error = "Reminder Date End must be after Reminder Date Start"
            return render_template("auth_pages/reminder_form.html", reminder=reminder, form_mode="EDIT", msg_error=msg_error)

        # Check Date Mandatory Behavior
        # If reminder recurrence type is "NONE", "Start Date" is optional, "End Date" is mandatory
        # If reminder recurrence type is not "NONE", "Start Date" is mandatory, "End Date" is optional
        if reminder_recurrence_type == "NONE":
            if reminder_date_start_processed and not reminder_date_end_processed:
                logger.info("Validation: Reminder Date End is mandatory when Reminder Recurrence Type is NONE")
                flash("Reminder Date End is mandatory when Reminder Recurrence Type is NONE", "error")
                msg_error = "Reminder Date End is mandatory when Reminder Recurrence Type is NONE"
                return render_template("auth_pages/reminder_form.html", reminder=reminder, form_mode="EDIT", msg_error=msg_error)
        else:
            if not reminder_date_start_processed and reminder_date_end_processed:
                logger.info("Validation: Reminder Date Start is mandatory when Reminder Recurrence Type is not NONE")
                flash("Reminder Date Start is mandatory when Reminder Recurrence Type is not NONE", "error")
                msg_error = "Reminder Date Start is mandatory when Reminder Recurrence Type is not NONE"
                return render_template("auth_pages/reminder_form.html", reminder=reminder, form_mode="EDIT", msg_error=msg_error)


        # For debugging only, hence commented out
        """
        logger.debug(f"Reminder Title: {reminder_title}")
        logger.debug(f"Reminder Description: {reminder_desc}")
        logger.debug(f"Reminder Link: {reminder_link}")
        logger.debug(f"Reminder Type: {reminder_type}")
        logger.debug(f"Reminder Date Start: {reminder_date_start}")
        logger.debug(f"Reminder Date End: {reminder_date_end}")
        logger.debug(f"Reminder Date Start Processed: {reminder_date_start_processed}")
        logger.debug(f"Reminder Date End Processed: {reminder_date_end_processed}")
        logger.debug(f"Reminder Recurrence Type: {reminder_recurrence_type}")
        logger.debug(f"Reminder Is Completed: {reminder_is_completed}")
        """


        # Build RRULE
        rrule_str = build_rrule_string(reminder_recurrence_type, reminder_date_start, reminder_date_end, interval=1, byweekday=[], bymonthday=None)
        logger.info(f"RRULE: {rrule_str}")

        # Update the reminder
        reminder.reminder_title = reminder_title
        reminder.reminder_desc = reminder_desc
        reminder.reminder_link = reminder_link
        reminder.reminder_type = reminder_type
        reminder.reminder_recurrence_type = reminder_recurrence_type
        reminder.reminder_recurrence_rrule = rrule_str
        reminder.reminder_date_start = reminder_date_start_processed
        reminder.reminder_date_end = reminder_date_end_processed
        reminder.reminder_is_completed = reminder_is_completed
        
        db.session.commit()
        logger.info("Reminder updated successfully!, Reminder UUID: %s", reminder.reminder_uuid)
        flash("Reminder updated successfully!", "success")
        return redirect(url_for("reminders.my_reminders"))

    return render_template("auth_pages/reminder_form.html", reminder=reminder, form_mode="EDIT", msg_error=None)


# Delete Reminder by reminder_uuid
@reminders_bp.route("/delete-reminder/<string:reminder_uuid>", methods=["GET"])
def delete_reminder(reminder_uuid):
    logger.info("/delete-reminder route called")

    # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    else:
        session_user_uuid = check_login_result

    # Fetch the reminder by UUID
    reminder = Reminder.query.filter_by(reminder_uuid=reminder_uuid, is_deleted=False).first_or_404()

    # Ensure reminder exists
    if not reminder:
        logger.error("Reminder not found")
        abort(404, description="Reminder not found")

    # Check if the reminder belongs to the user
    if reminder.reminder_user_uuid != session_user_uuid:
        logger.error("You are not authorized to delete this reminder")
        abort(403, description="You are not authorized to delete this reminder")

    reminder.is_deleted = True
    db.session.commit()
    logger.info("Reminder deleted successfully!, Reminder UUID: %s", reminder.reminder_uuid)
    flash("Reminder deleted successfully!", "danger")
    return redirect(url_for("reminders.my_reminders"))


# View Reminder by reminder_uuid
@reminders_bp.route("/view-reminder/<string:reminder_uuid>")
def view_reminder(reminder_uuid):
    logger.info("/view-reminder route called")

    # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    else:
        session_user_uuid = check_login_result

    # Fetch the reminder by UUID, ensure it is not deleted
    reminder = Reminder.query.filter_by(reminder_uuid=reminder_uuid, is_deleted=False).first()

    logger.debug(f"Reminder: {reminder}")
    logger.debug(f"Reminder Shared With: {reminder.reminder_shared_with}")

    shared_reminder_user_uuid_exists = False
    for shared_reminder, user, reminder in reminder.reminder_shared_with:
        logger.debug(f"Shared Reminder UUID: {shared_reminder.shared_reminder_uuid}")
        logger.debug(f"Shared Reminder User UUID: {shared_reminder.shared_reminder_user_uuid}")
        if shared_reminder.shared_reminder_user_uuid == session_user_uuid:
            shared_reminder_user_uuid_exists = True
            break

    logger.debug(f"Share Reminder User UUID Exists: {shared_reminder_user_uuid_exists}")

    # Ensure reminder exists
    if not reminder:
        logger.error("Reminder not found")
        abort(404, description="Reminder not found")

    # Check if the reminder belongs to the user OR is shared with the user
    if not reminder or (reminder.reminder_user_uuid != session_user_uuid) and (not shared_reminder_user_uuid_exists):
        logger.error("You are not authorized to view this reminder")
        abort(403, description="You are not authorized to view this reminder")


    # Add dynamic properties
    # Dynamically add 'reminder_is_shared' property
    reminder.reminder_is_shared = len(reminder.reminder_shared_with) > 0

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


    # Optional: determine if this is a share URL (unauthenticated) or normal view
    # For now, we assume authenticated user
    share_url = False

    return render_template(
        "auth_pages/reminder_view.html",
        reminder=reminder,
        share_url=share_url
    )


# Share Reminder by reminder_url_slug
@reminders_bp.route("/share/<string:reminder_url_slug>")
def share_reminder_url(reminder_url_slug):
    logger.info("/share/<reminder_url_slug> route called")

    # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    else:
        session_user_uuid = check_login_result

    # Fetch the reminder by reminder_url_slug, ensure it is not deleted
    reminder = Reminder.query.filter_by(reminder_url_slug=reminder_url_slug, is_deleted=False).first()

    # Ensure reminder exists
    if not reminder:
        logger.error("Reminder not found")
        abort(404, description="Reminder not found")

    # Check if the reminder belongs to the user OR is shared with the user
    if (reminder.reminder_user_uuid != session_user_uuid and session_user_uuid not in reminder.reminder_shared_with):
        logger.error("You are not authorized to view this reminder")
        abort(403, description="You are not authorized to view this reminder")

    # Set flag to determine if this is a share URL or normal view
    # Note: Share URL feature is authenticated page
    share_url = True

    return render_template(
        "auth_pages/reminder_view.html",
        reminder=reminder,
        share_url=share_url
    )


# Alert Webhook Settings
@reminders_bp.route("/alert-webhook", methods=["GET", "POST"])
def slack_settings():
    logger.info("/alert-webhook route called")

    # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    else:
        session_user_uuid = check_login_result

    # Fetch the user object by User UUID
    user = User.query.filter_by(user_uuid=session_user_uuid, is_deleted=False).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    msg_success, msg_error = None, None

    if request.method == "POST":
        user_alert_webhook_url = request.form.get("user_alert_webhook_url", "").strip()

       # Save the user_alert_webhook_url
        user.user_alert_webhook_url = user_alert_webhook_url
        db.session.commit()
        msg_success = "Alert Webhook URL updated successfully."

    return render_template(
        "auth_pages/alert_webhook.html",
        user=user,
        msg_success=msg_success,
        msg_error=msg_error
    )


# API endpoints
# API to Share Reminder
@reminders_bp.route("/api/reminder/share", methods=["POST"])
def share_reminder():
    logger.info("/api/reminder/share route called")

    # Check if user is logged in and return User UUID if authenticated, else throw error
    check_login_result = check_login_for_api()
    if isinstance(check_login_result, str):  # means it's an UUID string
        session_user_uuid = check_login_result

    # Validations-1
    if not check_login_result:
        logger.info("User not logged in, returning error")
        return jsonify({"success": False, "message": "User not logged in."}), 401

    data = request.get_json()
    share_reminder_uuid = data.get("share_reminder_uuid")
    share_user_id = data.get("share_user_id")

    logger.debug("share_reminder_uuid: %s", share_reminder_uuid)
    logger.debug("share_user_id: %s", share_user_id)

    # Validations-2
    if not share_reminder_uuid:
        logger.info("Validation: Missing Reminder UUID.")
        return jsonify({"success": False, "message": "Missing Reminder UUID."}), 400
    
    if not share_user_id:
        logger.info("Validation: Missing User ID.")
        return jsonify({"success": False, "message": "Missing User ID."}), 400
    
    # Check if the logged in user owns the reminder
    reminder = Reminder.query.filter_by(reminder_uuid=share_reminder_uuid, is_deleted=False).first()

    if not reminder:
        logger.info("Validation: Reminder not found.")
        return jsonify({"success": False, "message": "Reminder not found."}), 400

    if reminder.reminder_user_uuid != session_user_uuid:
        logger.info("Validation: You are not authorized to share this reminder.")
        return jsonify({"success": False, "message": "You are not authorized to share this reminder."}), 403

    # Check if already shared
    # share_user_id can be username or email
    shared_user_obj = User.query.filter_by(user_username=share_user_id, is_deleted=False).first()

    if not shared_user_obj:
        shared_user_obj = User.query.filter_by(user_email=share_user_id, is_deleted=False).first()

    # Validations-3
    if not shared_user_obj:
        logger.info("Validation: User not found.")
        return jsonify({"success": False, "message": "User not found."}), 400

    if shared_user_obj.user_uuid == session_user_uuid:
        logger.info("Validation: Cannot share with yourself.")
        return jsonify({"success": False, "message": "Cannot share with yourself."}), 400

    existing = SharedReminder.query.filter_by(
        shared_reminder_reminder_uuid=share_reminder_uuid,
        shared_reminder_user_uuid=shared_user_obj.user_uuid,
        is_deleted=False
    ).first()

    # Validations-4
    if existing:
        logger.info("Validation: Already shared with this user.")
        return jsonify({"success": False, "message": "Already shared with this user."}), 400

    shared_reminder_record = SharedReminder(
        shared_reminder_uuid=str(uuid.uuid4()),
        shared_reminder_reminder_uuid=share_reminder_uuid,
        shared_reminder_user_uuid=shared_user_obj.user_uuid,
        is_deleted=False
    )
    db.session.add(shared_reminder_record)
    db.session.commit()

    logger.info("Reminder shared successfully!, Reminder UUID: %s", share_reminder_uuid)
    return jsonify({"success": True, "message": "Reminder shared successfully."})


# API to Unshare Reminder
@reminders_bp.route("/api/reminder/unshare", methods=["POST"])
def unshare_reminder():
    logger.info("/api/reminder/unshare route called")

    # Check if user is logged in and return User UUID if authenticated, else throw error
    check_login_result = check_login_for_api()
    if isinstance(check_login_result, str):  # means it's an UUID string
        session_user_uuid = check_login_result

    # Validations-1
    if not check_login_result:
        logger.info("User not logged in, returning error")
        return jsonify({"success": False, "message": "User not logged in."}), 401

    data = request.get_json()
    share_reminder_uuid = data.get("share_reminder_uuid")
    unshare_user_id = data.get("unshare_user_id")

    logger.debug("share_reminder_uuid: %s", share_reminder_uuid)
    logger.debug("unshare_user_id: %s", unshare_user_id)

    # Validations-2
    if not share_reminder_uuid:
        logger.info("Validation: Missing Reminder UUID.")
        return jsonify({"success": False, "message": "Missing Reminder UUID."}), 400
    
    if not unshare_user_id:
        logger.info("Validation: Missing User ID.")
        return jsonify({"success": False, "message": "Missing User ID."}), 400
    
    # Check if the logged in user owns the reminder
    reminder = Reminder.query.filter_by(reminder_uuid=share_reminder_uuid, is_deleted=False).first()

    if not reminder:
        logger.info("Validation: Reminder not found.")
        return jsonify({"success": False, "message": "Reminder not found."}), 400

    if reminder.reminder_user_uuid != session_user_uuid:
        logger.info("Validation: You are not authorized to unshare this reminder.")
        return jsonify({"success": False, "message": "You are not authorized to unshare this reminder."}), 403

    shared_reminder_record = SharedReminder.query.filter_by(
        shared_reminder_reminder_uuid=share_reminder_uuid,
        shared_reminder_user_uuid=unshare_user_id,
        is_deleted=False
    ).first()

    if not shared_reminder_record:
        logger.info("Validation: No share record found.")
        return jsonify({"success": False, "message": "No share record found."}), 404

    # Soft delete
    shared_reminder_record.is_deleted = True
    db.session.commit()

    logger.info("Reminder unshared successfully!, Reminder UUID: %s", share_reminder_uuid)
    return jsonify({"success": True, "message": "Reminder unshared successfully."})


# API to preview RRULE
@reminders_bp.route("/api/reminder/preview-next-occurrences", methods=["POST"])
def api_preview_next_occurrences():
    """
    Build RRULE from user input and return next occurrences for live preview.
    """
    logger.info("/api/reminder/preview-next-occurrences route called")

    # Check if user is logged in and return User UUID if authenticated, else throw error
    check_login_result = check_login_for_api()

    # Validations
    if not check_login_result:
        logger.info("User not logged in, returning error")
        return jsonify({"success": False, "message": "User not logged in."}), 401

    data = request.json or {}

    reminder_recurrence_type = data.get("reminder_recurrence_type", "NONE")
    reminder_date_start = data.get("reminder_date_start")
    reminder_date_end = data.get("reminder_date_end")

    logger.debug(f"Reminder Recurrence Type: {reminder_recurrence_type}")
    logger.debug(f"Reminder Date Start: {reminder_date_start}")
    logger.debug(f"Reminder Date End: {reminder_date_end}")

    rrule_str = build_rrule_string(
        reminder_recurrence_type,
        reminder_date_start,
        reminder_date_end,
        interval=1,
        byweekday=[],
        bymonthday=None,
    )
    logger.debug(f"RRULE: {rrule_str}")

    if not rrule_str:
        logger.error("Invalid RRULE")
        return jsonify({"next_occurrences": []})

    next_occurrences = get_next_occurrences_date_only(reminder_date_start, rrule_str, count=5)
    return jsonify({"next_occurrences": next_occurrences})


@reminders_bp.route("/api/reminder/update-completed", methods=["POST"])
def mark_completed():
    logger.info("/api/reminder/update-completed route called")

    # Check if user is logged in and return User UUID if authenticated, else throw error
    check_login_result = check_login_for_api()
    if isinstance(check_login_result, str):  # means it's an UUID string
        session_user_uuid = check_login_result

    # Validations-1
    if not check_login_result:
        logger.info("User not logged in, returning error")
        return jsonify({"success": False, "message": "User not logged in."}), 401

    data = request.get_json()
    reminder_uuid = data.get("reminder_uuid")
    reminder_is_completed = data.get("reminder_is_completed")

    logger.debug("reminder_uuid: %s", reminder_uuid)
    logger.debug("reminder_is_completed: %s", reminder_is_completed)

    # Fetch the reminder
    reminder = Reminder.query.filter_by(reminder_uuid=str(reminder_uuid), is_deleted=False).first()
    if not reminder:
        return jsonify({"success": False, "message": "Reminder not found"}), 404

    # Check if user is owner or shared-with user
    is_owner = reminder.reminder_user_uuid == session_user_uuid
    is_shared = (
        db.session.query(SharedReminder)
        .filter_by(shared_reminder_reminder_uuid=reminder.reminder_uuid,
                   shared_reminder_user_uuid=session_user_uuid,
                   is_deleted=False)
        .first()
    )

    if not (is_owner or is_shared):
        return jsonify({"success": False, "message": "Not authorized"}), 401

    reminder.reminder_is_completed = reminder_is_completed
    db.session.commit()

    return jsonify({"success": True, "message": "Reminder updated"})

# API to send alerts
# Note: This API is for internal use only and unauthenticated endpoint
@reminders_bp.route('/api/reminder/send-alerts', methods=['GET'])
def send_alerts():
    logger.info("/api/reminder/send-alerts route called")
    
    # Fetch the user object using the User UUID
    users = User.query.filter_by(is_deleted=False).all()
    if not users:
        return jsonify({"success": False, "message": "Users data not found"}), 400

    for each_user in users:
        logger.debug("user_uuid: %s", each_user.user_uuid)

        if each_user.user_alert_webhook_url is None:
            logger.info("Alert Webhook URL not found, skipping user: %s", each_user.user_uuid)
            continue
        else:
            # Part-1: Get reminders that belong to that user
            logger.info("Part-1: Get reminders that belong to that user: %s", each_user.user_uuid)

            my_reminders = Reminder.query.filter_by(
                reminder_user_uuid=each_user.user_uuid,
                reminder_is_completed=False,
                is_deleted=False
            ).order_by(Reminder.reminder_date_start).all()


            # Add dynamic properties
            for reminder in my_reminders:
                # Dynamically add 'reminder_is_shared' property
                reminder.reminder_is_shared = len(reminder.reminder_shared_with) > 0

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

                logger.debug("Owned Reminder: reminder_display_date_next_occurrence: %s", reminder_display_date_next_occurrence)
                logger.debug("Owned Reminder: reminder_sort_date_next_occurrence: %s", reminder_sort_date_next_occurrence)

                reminder.reminder_display_date_next_occurrence = reminder_display_date_next_occurrence
                reminder.reminder_sort_date_next_occurrence = reminder_sort_date_next_occurrence
            

            # Sort by next occurrence
            my_reminders = sorted(my_reminders, key=lambda x: x.reminder_sort_date_next_occurrence)
            
            # Logic for sending alerts
            today = datetime.now().date()
            
            for each_owned_reminder in my_reminders:
                if each_owned_reminder.reminder_display_date_next_occurrence == "N/A":
                    # Skip reminders that don't have a next occurrence
                    logger.debug("Owned Reminder: Skipping reminder as it doesn't have a next occurrence: %s", each_owned_reminder.reminder_uuid)
                    continue
                else:
                    logger.debug("Owned Reminder: reminder_uuid: %s", each_owned_reminder.reminder_uuid)
                    logger.debug("Owned Reminder: reminder_display_date_next_occurrence: %s", each_owned_reminder.reminder_display_date_next_occurrence)
                    logger.debug("Owned Reminder: reminder_sort_date_next_occurrence: %s", each_owned_reminder.reminder_sort_date_next_occurrence)
                
                    reminder_due_date = each_owned_reminder.reminder_sort_date_next_occurrence
                    logger.debug(f"Owned Reminder: reminder_due_date: {reminder_due_date}")

                    # Calculate due date diff
                    due_date_diff = reminder_due_date - today
                    logger.debug(f"Owned Reminder: due_date_diff: {due_date_diff}")
                    # Convert timedelta object to days
                    due_date_diff_days = due_date_diff.days
                    logger.debug(f"Owned Reminder: due_date_diff_days: {due_date_diff_days}")

                    # Current threshold for sending alerts
                    alert_threshold = 5
                    logger.debug(f"Owned Reminder: alert_threshold: {alert_threshold}")
                
                    if due_date_diff_days <= alert_threshold and reminder_due_date >= today:
                        # Send alert
                        logger.info(f"Owned Reminder: Sending alert for reminder: {each_owned_reminder.reminder_uuid} | Due Date Diff Days: {due_date_diff_days} days")

                        response_boolean_flag = send_alert_notification("Your Reminder", each_user.user_alert_webhook_url, each_owned_reminder.reminder_title, reminder_due_date)
                        if response_boolean_flag == False:
                            logger.error(f"Owned Reminder: Error sending notification for reminder: {each_owned_reminder.reminder_uuid}")
                        else:
                            logger.info(f"Owned Reminder: Notification sent successfully for reminder: {each_owned_reminder.reminder_uuid}")
                    else:
                        logger.debug(f"Owned Reminder: Skipping reminder as it's not due yet: {each_owned_reminder.reminder_uuid}")
                        continue



            # Part-2: Get reminders that have been shared with that user
            logger.info("Part-2: Get reminders that have been shared with that user: %s", each_user.user_uuid)

            user_reminder_shared_with = aliased(User)
            user_reminder_owner = aliased(User)
            
            # Get reminders that are shared with that user
            my_shared_reminders = (
                db.session.query(Reminder, SharedReminder, user_reminder_shared_with, user_reminder_owner)
                    # Join shared reminder
                    .join(SharedReminder, SharedReminder.shared_reminder_reminder_uuid == Reminder.reminder_uuid)
                    # Join the user the reminder is shared with
                    .join(user_reminder_shared_with, SharedReminder.shared_reminder_user_uuid == user_reminder_shared_with.user_uuid)
                    # Join the owner of the reminder
                    .join(user_reminder_owner, Reminder.reminder_user_uuid == user_reminder_owner.user_uuid)
                    .filter(
                        SharedReminder.shared_reminder_user_uuid == each_user.user_uuid,
                        SharedReminder.is_deleted == False,
                        Reminder.is_deleted == False,
                        Reminder.reminder_is_completed == False,
                        user_reminder_shared_with.is_deleted == False,
                        user_reminder_owner.is_deleted == False
                    )
                    .order_by(Reminder.reminder_date_start)
                    .all()
            )

            # For debugging only, hence commented out
            """
            for reminder, shared, user_reminder_shared_with, user_reminder_owner in my_shared_reminders:
                logger.debug(reminder.reminder_title)
                logger.debug(shared.shared_reminder_user_uuid)
                logger.debug(user_reminder_shared_with.user_username)
                logger.debug(user_reminder_owner.user_username)
                logger.debug("---\n")
            """


            # Add dynamic properties
            for reminder, shared, user_reminder_shared_with, user_reminder_owner in my_shared_reminders:
                
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

                reminder.reminder_display_date_next_occurrence = reminder_display_date_next_occurrence
                reminder.reminder_sort_date_next_occurrence = reminder_sort_date_next_occurrence

                logger.debug("Shared Reminder: reminder.reminder_display_date_next_occurrence: %s", reminder.reminder_display_date_next_occurrence)
                logger.debug("Shared Reminder: reminder.reminder_sort_date_next_occurrence: %s", reminder.reminder_sort_date_next_occurrence)
            

             # Sort by next occurrence
            my_shared_reminders = sorted(my_shared_reminders, key=lambda x: x[0].reminder_sort_date_next_occurrence)

            # For debugging only, hence commented out
            """
            logger.debug("---\n")
            for reminder, shared, user_reminder_shared_with, user_reminder_owner in my_shared_reminders:
                logger.debug(reminder.reminder_title)
                logger.debug(shared.shared_reminder_user_uuid)
                logger.debug(user_reminder_shared_with.user_username)
                logger.debug(user_reminder_owner.user_username)
                logger.debug(reminder.reminder_display_date_next_occurrence)
                logger.debug(reminder.reminder_sort_date_next_occurrence)
                logger.debug("---\n")
            """
            
            # Logic for sending alerts
            today = datetime.now().date()
            
            for reminder, shared, user_reminder_shared_with, user_reminder_owner in my_shared_reminders:
                if reminder.reminder_display_date_next_occurrence == "N/A":
                    # Skip reminders that don't have a next occurrence
                    logger.debug("Shared Reminder: Skipping reminder as it doesn't have a next occurrence: %s", reminder.reminder_uuid)
                    continue
                else:
                    logger.debug("Shared Reminder: reminder_uuid: %s", reminder.reminder_uuid)
                    logger.debug("Shared Reminder: reminder_display_date_next_occurrence: %s", reminder.reminder_display_date_next_occurrence)
                    logger.debug("Shared Reminder: reminder_sort_date_next_occurrence: %s", reminder.reminder_sort_date_next_occurrence)
                
                    reminder_due_date = reminder.reminder_sort_date_next_occurrence
                    logger.debug(f"Shared Reminder: reminder_due_date: {reminder_due_date}")

                    # Calculate due date diff
                    due_date_diff = reminder_due_date - today
                    logger.debug(f"Shared Reminder: due_date_diff: {due_date_diff}")
                    # Convert timedelta object to days
                    due_date_diff_days = due_date_diff.days
                    logger.debug(f"Shared Reminder: due_date_diff_days: {due_date_diff_days}")

                    # Current threshold for sending alerts
                    alert_threshold = 5
                    logger.debug(f"Shared Reminder: alert_threshold: {alert_threshold}")
                
                    if due_date_diff_days <= alert_threshold and reminder_due_date >= today:
                        # Send alert
                        logger.info(f"Shared Reminder: Sending alert for reminder: {reminder.reminder_uuid} | Due Date Diff Days: {due_date_diff_days} days")

                        response_boolean_flag = send_alert_notification("Shared Reminder", each_user.user_alert_webhook_url, reminder.reminder_title, reminder_due_date)
                        if response_boolean_flag == False:
                            logger.error(f"Shared Reminder: Error sending notification for reminder: {reminder.reminder_uuid}")
                        else:
                            logger.info(f"Shared Reminder: Notification sent successfully for reminder: {reminder.reminder_uuid}")
                    else:
                        logger.debug(f"Shared Reminder: Skipping reminder as it's not due yet: {reminder.reminder_uuid}")
                        continue
            
                        

    return jsonify({"success": True, "message": "Sending Alerts completed successfully!"}), 200

        