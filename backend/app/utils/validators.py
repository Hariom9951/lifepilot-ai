import uuid


def is_valid_uuid(val: str) -> bool:
    """
    Check if a string is a valid UUIDv4 format.
    """
    try:
        uuid.UUID(val, version=4)
        return True
    except ValueError:
        return False
