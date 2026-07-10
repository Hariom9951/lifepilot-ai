import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.responses.schemas import ErrorDetails, ErrorResponse
from app.core.exceptions.custom import AppException

logger = logging.getLogger("app.exceptions")


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handles all custom AppExceptions, returning standard JSON ErrorResponses.
    """
    assert isinstance(exc, AppException)
    logger.error(
        f"AppException [{exc.status_code}]: {exc.message} | Errors: {exc.errors}"
    )
    response_content = ErrorResponse(
        success=False,
        message=exc.message,
        errors=exc.errors,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content.model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Handles standard Pydantic validation errors and format them to standardized JSON.
    """
    assert isinstance(exc, RequestValidationError)
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    errors_list = [
        ErrorDetails(
            loc=list(map(str, err["loc"])), msg=err["msg"], type=err["type"]
        )
        for err in exc.errors()
    ]
    response_content = ErrorResponse(
        success=False,
        message="Request validation failed.",
        errors=[err.model_dump() for err in errors_list],
    )
    return JSONResponse(
        status_code=422,
        content=response_content.model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled generic system exceptions.
    """
    logger.exception(f"Unhandled server exception: {exc}")
    response_content = ErrorResponse(
        success=False,
        message="Internal server error occurred.",
        errors=[str(exc)] if request.app.debug else ["Please check server logs."],
    )
    return JSONResponse(
        status_code=500,
        content=response_content.model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global handlers on the FastAPI application instance.
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
