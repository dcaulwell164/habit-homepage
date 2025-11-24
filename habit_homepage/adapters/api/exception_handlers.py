"""
API exception handlers for translating domain exceptions to HTTP responses.

This module provides FastAPI exception handlers that convert domain-layer
exceptions into appropriate HTTP responses with proper status codes and
structured error messages.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from habit_homepage.domain.exceptions import (
    BusinessRuleViolationError,
    DailyLogNotFoundError,
    DuplicateResourceError,
    GoalNotFoundError,
    HabitAlreadyLoggedError,
    HabitNotFoundError,
    HabitTrackerException,
    InvalidDateRangeError,
    InvalidGoalConfigError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ResourceNotFoundError,
    ValidationError,
)


def create_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    """
    Create a standardized JSON error response.

    Args:
        status_code: HTTP status code
        error_type: Error type identifier (e.g., "ResourceNotFound")
        message: Human-readable error message
        details: Optional additional error details

    Returns:
        JSONResponse with structured error format
    """
    content = {
        "error": {
            "type": error_type,
            "message": message,
        }
    }
    if details:
        content["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=content)


# Resource Not Found Handlers
async def handle_resource_not_found(
    request: Request, exc: ResourceNotFoundError
) -> JSONResponse:
    """Handle ResourceNotFoundError and its subclasses."""
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_type="ResourceNotFound",
        message=str(exc),
        details={
            "resource_type": exc.resource_type,
            "resource_id": exc.resource_id,
        },
    )


async def handle_habit_not_found(
    request: Request, exc: HabitNotFoundError
) -> JSONResponse:
    """Handle HabitNotFoundError."""
    return await handle_resource_not_found(request, exc)


async def handle_goal_not_found(
    request: Request, exc: GoalNotFoundError
) -> JSONResponse:
    """Handle GoalNotFoundError."""
    return await handle_resource_not_found(request, exc)


async def handle_daily_log_not_found(
    request: Request, exc: DailyLogNotFoundError
) -> JSONResponse:
    """Handle DailyLogNotFoundError."""
    return await handle_resource_not_found(request, exc)


# Validation Error Handlers
async def handle_validation_error(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle ValidationError and its subclasses."""
    details = {}
    if hasattr(exc, "field") and exc.field:
        details["field"] = exc.field

    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type="ValidationError",
        message=str(exc),
        details=details if details else None,
    )


async def handle_invalid_date_range(
    request: Request, exc: InvalidDateRangeError
) -> JSONResponse:
    """Handle InvalidDateRangeError."""
    return await handle_validation_error(request, exc)


async def handle_invalid_goal_config(
    request: Request, exc: InvalidGoalConfigError
) -> JSONResponse:
    """Handle InvalidGoalConfigError."""
    return await handle_validation_error(request, exc)


# Business Rule Violation Handlers
async def handle_business_rule_violation(
    request: Request, exc: BusinessRuleViolationError
) -> JSONResponse:
    """Handle BusinessRuleViolationError and its subclasses."""
    return create_error_response(
        status_code=status.HTTP_409_CONFLICT,
        error_type="BusinessRuleViolation",
        message=str(exc),
    )


async def handle_duplicate_resource(
    request: Request, exc: DuplicateResourceError
) -> JSONResponse:
    """Handle DuplicateResourceError."""
    return create_error_response(
        status_code=status.HTTP_409_CONFLICT,
        error_type="DuplicateResource",
        message=str(exc),
        details={
            "resource_type": exc.resource_type,
            "identifier": exc.identifier,
        },
    )


async def handle_habit_already_logged(
    request: Request, exc: HabitAlreadyLoggedError
) -> JSONResponse:
    """Handle HabitAlreadyLoggedError."""
    return await handle_business_rule_violation(request, exc)


# Provider Error Handlers
async def handle_provider_error(request: Request, exc: ProviderError) -> JSONResponse:
    """Handle ProviderError and its subclasses."""
    details = {"provider": exc.provider_name}
    if exc.original_error:
        details["original_error"] = str(exc.original_error)

    return create_error_response(
        status_code=status.HTTP_502_BAD_GATEWAY,
        error_type="ProviderError",
        message=str(exc),
        details=details,
    )


async def handle_provider_authentication_error(
    request: Request, exc: ProviderAuthenticationError
) -> JSONResponse:
    """Handle ProviderAuthenticationError."""
    return create_error_response(
        status_code=status.HTTP_502_BAD_GATEWAY,
        error_type="ProviderAuthenticationError",
        message=str(exc),
        details={"provider": exc.provider_name},
    )


async def handle_provider_rate_limit(
    request: Request, exc: ProviderRateLimitError
) -> JSONResponse:
    """Handle ProviderRateLimitError."""
    details = {"provider": exc.provider_name}
    if exc.retry_after:
        details["retry_after"] = exc.retry_after

    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)

    response = create_error_response(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_type="ProviderRateLimitError",
        message=str(exc),
        details=details,
    )

    if headers:
        for key, value in headers.items():
            response.headers[key] = value

    return response


async def handle_provider_unavailable(
    request: Request, exc: ProviderUnavailableError
) -> JSONResponse:
    """Handle ProviderUnavailableError."""
    return create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type="ProviderUnavailableError",
        message=str(exc),
        details={"provider": exc.provider_name},
    )


# Generic Habit Tracker Exception Handler
async def handle_habit_tracker_exception(
    request: Request, exc: HabitTrackerException
) -> JSONResponse:
    """
    Fallback handler for any HabitTrackerException not caught by specific handlers.

    This ensures all domain exceptions are handled gracefully.
    """
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="HabitTrackerError",
        message=str(exc),
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with a FastAPI application.

    Call this function in main.py after creating the FastAPI app.

    Usage:
        app = FastAPI()
        register_exception_handlers(app)
    """
    # Resource not found handlers
    app.add_exception_handler(ResourceNotFoundError, handle_resource_not_found)
    app.add_exception_handler(HabitNotFoundError, handle_habit_not_found)
    app.add_exception_handler(GoalNotFoundError, handle_goal_not_found)
    app.add_exception_handler(DailyLogNotFoundError, handle_daily_log_not_found)

    # Validation error handlers
    app.add_exception_handler(ValidationError, handle_validation_error)
    app.add_exception_handler(InvalidDateRangeError, handle_invalid_date_range)
    app.add_exception_handler(InvalidGoalConfigError, handle_invalid_goal_config)

    # Business rule violation handlers
    app.add_exception_handler(
        BusinessRuleViolationError, handle_business_rule_violation
    )
    app.add_exception_handler(DuplicateResourceError, handle_duplicate_resource)
    app.add_exception_handler(HabitAlreadyLoggedError, handle_habit_already_logged)

    # Provider error handlers
    app.add_exception_handler(ProviderError, handle_provider_error)
    app.add_exception_handler(
        ProviderAuthenticationError, handle_provider_authentication_error
    )
    app.add_exception_handler(ProviderRateLimitError, handle_provider_rate_limit)
    app.add_exception_handler(ProviderUnavailableError, handle_provider_unavailable)

    # Fallback handler for any other HabitTrackerException
    app.add_exception_handler(HabitTrackerException, handle_habit_tracker_exception)
