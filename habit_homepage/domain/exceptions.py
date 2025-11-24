"""
Domain exceptions for the habit tracking application.

These exceptions represent business rule violations and error conditions
that can occur during application operation.
"""


class HabitTrackerException(Exception):
    """Base exception for all habit tracker errors."""

    pass


# Resource Not Found Exceptions
class ResourceNotFoundError(HabitTrackerException):
    """Base exception for resource not found errors."""

    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with ID '{resource_id}' not found")


class HabitNotFoundError(ResourceNotFoundError):
    """Raised when a habit does not exist."""

    def __init__(self, habit_id: str):
        super().__init__("Habit", habit_id)


class GoalNotFoundError(ResourceNotFoundError):
    """Raised when a goal does not exist."""

    def __init__(self, goal_id: str):
        super().__init__("Goal", goal_id)


class DailyLogNotFoundError(ResourceNotFoundError):
    """Raised when a daily log does not exist."""

    def __init__(self, date: str):
        super().__init__("Daily Log", date)


# Validation Exceptions
class ValidationError(HabitTrackerException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class InvalidDateRangeError(ValidationError):
    """Raised when date range is invalid (start > end)."""

    def __init__(self, start: str, end: str):
        super().__init__(
            f"Invalid date range: start ({start}) must be before or equal to end ({end})"
        )


class InvalidGoalConfigError(ValidationError):
    """Raised when goal configuration is invalid."""

    pass


# Provider Exceptions
class ProviderError(HabitTrackerException):
    """Base exception for external provider errors."""

    def __init__(self, provider_name: str, message: str, original_error: Exception | None = None):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"{provider_name} provider error: {message}")


class ProviderAuthenticationError(ProviderError):
    """Raised when provider authentication fails."""

    def __init__(self, provider_name: str, message: str = "Authentication failed"):
        super().__init__(provider_name, message)


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded."""

    def __init__(self, provider_name: str, retry_after: int | None = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(provider_name, message)
        self.retry_after = retry_after


class ProviderUnavailableError(ProviderError):
    """Raised when provider service is unavailable."""

    def __init__(self, provider_name: str):
        super().__init__(provider_name, "Service temporarily unavailable")


# Business Logic Exceptions
class BusinessRuleViolationError(HabitTrackerException):
    """Raised when a business rule is violated."""

    pass


class DuplicateResourceError(BusinessRuleViolationError):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier
        super().__init__(
            f"{resource_type} with identifier '{identifier}' already exists"
        )


class HabitAlreadyLoggedError(BusinessRuleViolationError):
    """Raised when attempting to log a habit that's already logged for a date."""

    def __init__(self, habit_id: str, date: str):
        super().__init__(
            f"Habit '{habit_id}' already logged for date {date}. Use update instead."
        )
