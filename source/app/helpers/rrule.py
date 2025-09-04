# helpers/rrule.py
from dateutil.rrule import rrule, rrulestr, DAILY, WEEKLY, MONTHLY, YEARLY, MO, TU, WE, TH, FR, SA, SU
from datetime import datetime
from itertools import islice
from app.helpers.logging import setup_logger


logger = setup_logger()

WEEKDAY_MAP = {'MO': MO, 'TU': TU, 'WE': WE, 'TH': TH, 'FR': FR, 'SA': SA, 'SU': SU}
FREQ_MAP = {
    "DAILY": DAILY,
    "WEEKLY": WEEKLY,
    "MONTHLY": MONTHLY,
    "YEARLY": YEARLY
}


def build_rrule_string(recurrence_type, start_date, end_date=None, interval=1, byweekday=None, bymonthday=None):
    """
    Build RRULE string from recurrence inputs.
    start_date and end_date can be string (YYYY-MM-DD) or date/datetime object.
    """
    logger.info("build_rrule_string() called")

    logger.debug("recurrence_type: %s", recurrence_type)
    logger.debug("start_date: %s", start_date)
    logger.debug("end_date: %s", end_date)
    logger.debug("interval: %s", interval)
    logger.debug("byweekday: %s", byweekday)
    logger.debug("bymonthday: %s", bymonthday)

    if recurrence_type == "NONE" or not start_date:
        return None

    # Convert start_date / end_date to datetime
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date and isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    params = {"dtstart": start_date}
    if end_date:
        params["until"] = end_date
    if interval:
        params["interval"] = interval

    freq = FREQ_MAP.get(recurrence_type)
    if freq is None:
        return None

    if recurrence_type == "WEEKLY" and byweekday:
        params["byweekday"] = [WEEKDAY_MAP[d] for d in byweekday]
    if recurrence_type == "MONTHLY" and bymonthday:
        params["bymonthday"] = bymonthday

    return rrule(freq=freq, **params).__str__()


def parse_rrule(rrule_string):
    """
    Parse an RRULE string and return a dictionary with INTERVAL, BYDAY, BYMONTHDAY.
    """
    logger.info("parse_rrule() called")

    logger.debug("rrule_string: %s", rrule_string)

    if not rrule_string:
        return {}

    rule_obj = rrulestr(rrule_string)
    parsed = {
        "INTERVAL": rule_obj._interval,
        "BYDAY": [d.__repr__()[:2] for d in rule_obj._byweekday] if rule_obj._byweekday else None,
        "BYMONTHDAY": rule_obj._bymonthday[0] if rule_obj._bymonthday else None
    }
    logger.debug("parsed RRULE: %s", parsed)
    return parsed


def get_next_occurrences(reminder_date_start, rrule_string, count=5):
    """
    Return the next `count` occurrences of the given rrule string.
    If an UNTIL date is defined in the rrule, occurrences will not go beyond it.
    """
    logger.info("get_next_occurrences() called")

    logger.debug("reminder_date_start: %s", reminder_date_start)
    logger.debug("rrule_string: %s", rrule_string)
    logger.debug("count: %s", count)

    # Ensure reminder_date_start is a date object
    if isinstance(reminder_date_start, str):
        reminder_date_start = datetime.strptime(reminder_date_start, "%Y-%m-%d").date()

    if not rrule_string:
        return []

    rule = rrulestr(rrule_string)
    now = datetime.now()
    date_now = now.date()

    # Pull occurrences after "now"
    occurrences = list(islice(rule.xafter(now, count=count), count))

    # If UNTIL is defined, filter out dates beyond it
    until = getattr(rule, "_until", None)
    if until:
        occurrences = [dt for dt in occurrences if dt <= until]

    # If reminder_date_start is in the future, that becomes the first occurrence instead
    # And remove the last occurrence
    #if reminder_date_start > date_now:
    #    logger.debug("reminder_date_start is in the future, using it as first occurrence")
    #    occurrences = [reminder_date_start] + occurrences
    #    # Remove last occurrence
    #    occurrences = occurrences[:-1]
        
    return [dt.strftime("%Y-%m-%d %H:%M") for dt in occurrences]


def get_next_occurrences_date_only(reminder_date_start, rrule_string, count=5):
    """
    Wrapper over get_next_occurrences to strip out time.
    Returns only date in YYYY-MM-DD format.
    """
    logger.info("get_next_occurrences_date_only() called")

    logger.debug("reminder_date_start: %s", reminder_date_start)
    logger.debug("rrule_string: %s", rrule_string)
    logger.debug("count: %s", count)

    occurrences = get_next_occurrences(reminder_date_start, rrule_string, count)
    return [dt.split(" ")[0] for dt in occurrences]