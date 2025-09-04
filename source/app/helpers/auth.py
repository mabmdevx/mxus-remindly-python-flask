from flask import redirect, session, url_for
from app.helpers.logging import setup_logger


logger = setup_logger()


def check_login_for_page():
    logger.info("check_login_for_page() called")

    session_user_uuid = session.get("user_uuid")
    if not session_user_uuid:
        logger.info("User not logged in, redirecting to login page")
        return redirect(url_for("auth.login"))
    else:
        return session_user_uuid
    

def check_login_for_api():
    logger.info("check_login_for_api() called")

    session_user_uuid = session.get("user_uuid")
    if not session_user_uuid:
        logger.info("User not logged in, returning error")
        return ValueError("User not logged in.")
    else:
        return session_user_uuid