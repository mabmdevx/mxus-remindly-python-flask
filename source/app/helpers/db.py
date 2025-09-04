from dotenv import load_dotenv
import os
from app.helpers.logging import setup_logger


logger = setup_logger()

# Load environment variables
load_dotenv()


def get_db_connection_string():
    logger.info("Getting database connection string...")

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_user = os.getenv("DB_USER", "remindly")
    db_password = os.getenv("DB_PASSWORD", "password")
    db_name = os.getenv("DB_NAME", "remindly")

    logger.debug("Database Host: %s", db_host)
    logger.debug("Database Port: %s", db_port)
    logger.debug("Database Name: %s", db_name)
    logger.debug("Database connection string: %s", f"mysql+pymysql://<hidden>:<hidden>@{db_host}:{db_port}/{db_name}")

    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"