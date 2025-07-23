"""
Enums for the User Management domain model.
"""

from enum import Enum


class UserRole(Enum):
    """User roles in the system."""
    SOLUTION_ARCHITECT = "SolutionArchitect"
    SALES_MANAGER = "SalesManager"
    
    def __str__(self) -> str:
        return self.value


class TokenType(Enum):
    """Types of authentication tokens."""
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"
    
    def __str__(self) -> str:
        return self.value


class SecurityEventType(Enum):
    """Types of security events for audit logging."""
    USER_REGISTRATION = "USER_REGISTRATION"
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET_REQUEST = "PASSWORD_RESET_REQUEST"
    PASSWORD_RESET_COMPLETE = "PASSWORD_RESET_COMPLETE"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    
    def __str__(self) -> str:
        return self.value
