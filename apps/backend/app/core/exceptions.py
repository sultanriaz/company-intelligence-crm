from typing import Any, Dict, Optional


class AppBaseException(Exception):
    """Base exception for application domain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SSRFViolationException(AppBaseException):
    """Raised when an outbound URL points to an internal or restricted network address."""
    pass


class ResourceNotFoundException(AppBaseException):
    """Raised when a requested database entity does not exist."""
    pass


class DuplicateEntityException(AppBaseException):
    """Raised when attempting to insert an entity violating uniqueness constraints."""
    pass


class WorkflowExecutionException(AppBaseException):
    """Raised when an error occurs during agent workflow execution."""
    pass


class RateLimitExceededException(AppBaseException):
    """Raised when an external domain or API rate limit is exceeded."""
    pass


class EmailComplianceViolationException(AppBaseException):
    """Raised when an outbound email violates suppression or eligibility rules."""
    pass


class ProviderDispatchException(AppBaseException):
    """Raised when an external provider (email, LLM, search) call fails."""
    pass


class AuthenticationFailedException(AppBaseException):
    """Raised when invalid credentials or token provided."""
    pass


class PermissionDeniedException(AppBaseException):
    """Raised when user lacks required workspace permissions."""
    pass
