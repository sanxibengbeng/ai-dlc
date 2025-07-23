"""
PasswordReset entity for the User Management domain model.
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from base_entity import BaseEntity
from exceptions import ValidationException, ExpiredTokenException


class PasswordReset(BaseEntity):
    """
    PasswordReset entity managing password reset requests and tokens.
    
    Attributes:
        id (str): Unique identifier for the password reset
        user_id (str): Reference to the User entity
        reset_token (str): Unique token for password reset
        token_expires_at (datetime): When the reset token expires (24 hours)
        is_used (bool): Whether the reset token has been used
        used_at (datetime): When the reset token was used
        created_at (datetime): When the reset request was created
        ip_address (str): IP address from which reset was requested
        user_agent (str): User agent from which reset was requested
        updated_at (datetime): When the reset was last updated
    """
    
    # Configuration constants
    TOKEN_EXPIRY_HOURS = 24
    TOKEN_LENGTH = 32
    
    def __init__(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reset_id: Optional[str] = None
    ):
        """
        Initialize PasswordReset entity.
        
        Args:
            user_id: Reference to the User entity
            ip_address: IP address from which reset was requested
            user_agent: User agent from which reset was requested
            reset_id: Optional UUID string for the reset
        
        Raises:
            ValidationException: If validation fails
        """
        super().__init__(reset_id)
        
        self.user_id = self._validate_user_id(user_id)
        self.reset_token = self._generate_reset_token()
        self.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=self.TOKEN_EXPIRY_HOURS)
        self.is_used = False
        self.used_at: Optional[datetime] = None
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def _validate_user_id(self, user_id: str) -> str:
        """Validate user ID."""
        if not user_id or not user_id.strip():
            raise ValidationException("User ID is required")
        return user_id.strip()
    
    def _generate_reset_token(self) -> str:
        """
        Generate a secure random reset token.
        
        Returns:
            Secure random token string
        """
        return secrets.token_urlsafe(self.TOKEN_LENGTH)
    
    def is_token_valid(self) -> bool:
        """
        Check if the reset token is still valid.
        
        Returns:
            True if token is valid, not used, and not expired, False otherwise
        """
        if self.is_used:
            return False
        
        return datetime.now(timezone.utc) < self.token_expires_at
    
    def validate_token(self, token: str) -> bool:
        """
        Validate the provided reset token.
        
        Args:
            token: Reset token to validate
        
        Returns:
            True if token is valid, False otherwise
        
        Raises:
            ExpiredTokenException: If token has expired
            ValidationException: If token has already been used
        """
        if self.is_used:
            raise ValidationException("Reset token has already been used")
        
        if not self.is_token_valid():
            raise ExpiredTokenException("Reset token has expired")
        
        return token == self.reset_token
    
    def use_token(self, token: str) -> bool:
        """
        Use the reset token (mark as used).
        
        Args:
            token: Reset token to use
        
        Returns:
            True if token was successfully used, False otherwise
        
        Raises:
            ExpiredTokenException: If token has expired
            ValidationException: If token has already been used or is invalid
        """
        if not self.validate_token(token):
            raise ValidationException("Invalid reset token")
        
        # Mark token as used
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)
        self.update_timestamp()
        
        return True
    
    def is_expired(self) -> bool:
        """
        Check if the reset token has expired.
        
        Returns:
            True if expired, False otherwise
        """
        return datetime.now(timezone.utc) >= self.token_expires_at
    
    def get_time_until_expiry(self) -> timedelta:
        """
        Get time remaining until token expires.
        
        Returns:
            Time remaining as timedelta, or zero if expired
        """
        if self.is_expired():
            return timedelta(0)
        
        return self.token_expires_at - datetime.now(timezone.utc)
    
    def invalidate(self) -> None:
        """
        Invalidate the reset token (mark as used without actually using it).
        Useful for security purposes when a token needs to be revoked.
        """
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convert password reset to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "reset_token": self.reset_token,
            "token_expires_at": self.token_expires_at.isoformat(),
            "is_used": self.is_used,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "created_at": self.created_at.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "updated_at": self.updated_at.isoformat()
        }
    
    def __str__(self) -> str:
        """String representation of the password reset."""
        status = "used" if self.is_used else ("expired" if self.is_expired() else "active")
        return f"PasswordReset(id='{self.id}', user_id='{self.user_id}', status='{status}')"
