from datetime import UTC, datetime


def get_utc_now() -> datetime:
    """
    Return current datetime with timezone aware UTC set.
    """
    return datetime.now(UTC)


def format_iso(dt: datetime) -> str:
    """
    Format a datetime object as a timezone-aware ISO string.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()
