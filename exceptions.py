"""
Custom exceptions for the User Management domain model.
"""


class DomainException(Exception):
    """Base exception for all domain-related errors."""
    pass


class ValidationException(DomainException):
    """Raised when domain validation fails."""
    pass


class AuthenticationException(DomainException):
    """Raised when authentication fails."""
    pass


class AuthorizationException(DomainException):
    """Raised when authorization fails."""
    pass


class EntityNotFoundException(DomainException):
    """Raised when a requested entity is not found."""
    pass


class DuplicateEntityException(DomainException):
    """Raised when attempting to create a duplicate entity."""
    pass


class TokenException(DomainException):
    """Raised when token operations fail."""
    pass


class AccountLockedException(AuthenticationException):
    """Raised when attempting to authenticate with a locked account."""
    pass


class AccountNotActivatedException(AuthenticationException):
    """Raised when attempting to authenticate with an inactive account."""
    pass


class InvalidCredentialsException(AuthenticationException):
    """Raised when provided credentials are invalid."""
    pass


class ExpiredTokenException(TokenException):
    """Raised when a token has expired."""
    pass


class InvalidTokenException(TokenException):
    """Raised when a token is invalid or malformed."""
    pass


class RevokedTokenException(TokenException):
    """Raised when attempting to use a revoked token."""
    pass
