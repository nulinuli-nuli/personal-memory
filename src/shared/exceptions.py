"""Custom exceptions for the application."""


class PersonalMemoryError(Exception):
    """Base exception for all personal memory errors."""
    pass


class RecordNotFoundError(PersonalMemoryError):
    """Raised when a record is not found."""
    pass


class InvalidInputError(PersonalMemoryError):
    """Raised when input validation fails."""
    pass


class AIServiceError(PersonalMemoryError):
    """Raised when AI service fails."""
    pass


class DatabaseError(PersonalMemoryError):
    """Raised when database operation fails."""
    pass


class UserNotFoundError(PersonalMemoryError):
    """Raised when a user is not found."""
    pass


class IntentRecognitionError(PersonalMemoryError):
    """Raised when AI intent recognition fails."""
    pass


class LowConfidenceError(PersonalMemoryError):
    """Raised when AI confidence is below threshold."""
    pass


class QueryGenerationError(PersonalMemoryError):
    """Raised when AI query generation fails."""
    pass
