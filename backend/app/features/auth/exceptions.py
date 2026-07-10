from app.core.exceptions.custom import AppException


class DuplicateEmailError(AppException):
    def __init__(self, message: str = "Email address is already registered.") -> None:
        super().__init__(status_code=409, message=message)


class DuplicateUsernameError(AppException):
    def __init__(self, message: str = "Username is already taken.") -> None:
        super().__init__(status_code=409, message=message)


class InvalidCredentialsError(AppException):
    def __init__(self, message: str = "Invalid username/email or password.") -> None:
        super().__init__(status_code=401, message=message)


class TokenExpiredError(AppException):
    def __init__(self, message: str = "Authentication token has expired.") -> None:
        super().__init__(status_code=401, message=message)


class InvalidTokenError(AppException):
    def __init__(self, message: str = "Authentication token is invalid or malformed.") -> None:
        super().__init__(status_code=401, message=message)


class RoleNotFoundError(AppException):
    def __init__(self, message: str = "Designated user role not found.") -> None:
        super().__init__(status_code=404, message=message)
