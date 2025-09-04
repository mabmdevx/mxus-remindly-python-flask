from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .. import db, bcrypt
from app.models.user import User
from app.helpers.auth import check_login_for_page
from app.helpers.logging import setup_logger


logger = setup_logger()
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    logger.info("/ index page route called")
    if "user_username" not in session:
        logger.info("User not logged in, redirecting to login page")
        return redirect(url_for("auth.login"))
    return render_template("auth_pages/dashboard.html", user=session.get("username"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    logger.info("/login route called")

    msg_error = ""
    if request.method == "POST":
        user_username = request.form.get("user_username")
        user_password = request.form.get("user_password")

        logger.debug("Username: %s", user_username)

        if not user_username or not user_password:
            logger.info("Validation: Missing username or password")
            msg_error = "Please enter your username and password"
        else:
            user = User.query.filter_by(user_username=user_username).first()

            if user and bcrypt.check_password_hash(user.user_password, user_password):

                session["user_id"] = user.user_id
                session["user_uuid"] = user.user_uuid
                session["user_username"] = user.user_username
                session["user_email"] = user.user_email

                logger.info("Login successful, username: %s", user.user_username)
                flash("Login successful!", "success")
                return redirect(url_for("reminders.dashboard"))
            else:
                logger.info("Validation: Invalid username or password")
                msg_error = "Invalid username or password"

    return render_template("unauth_pages/login.html", msg_error=msg_error)


@auth_bp.route("/logout")
def logout():
    logger.info("/logout route called")

    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    logger.info("/signup route called")

    msg_error = ""
    if request.method == "POST":
        user_username = request.form.get("user_username")
        user_password = request.form.get("user_password")
        user_confirm_password = request.form.get("user_confirm_password")
        user_email = request.form.get("user_email")

        logger.debug("Username: %s", user_username)
        logger.debug("Email: %s", user_email)

        if not user_username or not user_password or not user_email:
            logger.info("Validation: Missing username, password or email")
            msg_error = "Please enter your username, password and email"
        elif user_password != user_confirm_password:
            logger.info("Validation: Passwords do not match")
            msg_error = "Passwords do not match"
        else:
            existing = User.query.filter_by(user_username=user_username).first()
            if existing:
                logger.info("Validation: Username already exists")
                msg_error = "Username already exists"
            else:
                hashed_pw = bcrypt.generate_password_hash(user_password).decode("utf-8")
                new_user = User(user_username=user_username, user_password=hashed_pw, user_email=user_email)
                db.session.add(new_user)
                db.session.commit()
                logger.info("Signup successful, username: %s", user_username)
                flash("Signup successful, please login.", "success")
                return redirect(url_for("auth.login"))

    return render_template("unauth_pages/signup.html", msg_error=msg_error)


@auth_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    logger.info("/change-password route called")

     # Check if user is logged in and return User UUID if authenticated, else redirect to login
    check_login_result = check_login_for_page()
    if not isinstance(check_login_result, str):  # means it's a Response (redirect), not a UUID string
        return check_login_result
    else:
        session_user_uuid = check_login_result

    msg_success = None
    msg_error = None

    if request.method == "POST":
        current_password = request.form.get("app_current_password")
        new_password = request.form.get("app_new_password")
        confirm_password = request.form.get("app_confirm_password")

        # Get the logged-in user object by User UUID
        user = User.query.filter_by(user_uuid=session_user_uuid).first()

        if not user:
            logger.info("Validation: User not found.")
            msg_error = "User not found."
        elif not bcrypt.check_password_hash(user.user_password, current_password):
            logger.info("Validation: Current password is incorrect.")
            msg_error = "Current password is incorrect."
        elif new_password != confirm_password:
            logger.info("Validation: New passwords do not match.")
            msg_error = "New passwords do not match."
        else:
            # Update password
            hashed_pw = bcrypt.generate_password_hash(new_password).decode("utf-8")
            user.user_password = hashed_pw
            db.session.commit()

            logger.info("Password changed successfully, username: %s", user.user_username)
            msg_success = "Password changed successfully."

    return render_template(
        "auth_pages/change_password.html",
        msg_success=msg_success,
        msg_error=msg_error
    )
