"""
AuthenticationToken entity for the User Management domain model.
"""

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

from base_entity import BaseEntity
from enums import TokenType
from exceptions import ValidationException, RevokedTokenException


class AuthenticationToken(BaseEntity):
    """
    AuthenticationToken entity managing JWT tokens for stateless authentication.
    
    Attributes:
        id (str): Unique identifier for the token
        user_id (str): Reference to the User entity
        token_hash (str): Hash of the JWT token for revocation
        token_type (TokenType): Type of token (ACCESS, REFRESH)
        expires_at (datetime): When the token expires
        is_revoked (bool): Whether the token has been revoked
        revoked_at (datetime): When the token was revoked
        revoked_reason (str): Reason for token revocation
        created_at (datetime): When the token was created
        ip_address (str): IP address from which token was created
        user_agent (str): User agent from which token was created
        updated_at (datetime): When the token was last updated
    """
    
    # Configuration constants
    ACCESS_TOKEN_EXPIRY_HOURS = 24
    REFRESH_TOKEN_EXPIRY_DAYS = 30
    
    def __init__(
        self,
        user_id: str,
        token: str,
        token_type: TokenType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        custom_expiry: Optional[datetime] = None,
        token_id: Optional[str] = None
    ):
        """
        Initialize AuthenticationToken entity.
        
        Args:
            user_id: Reference to the User entity
            token: JWT token string to hash and store
            token_type: Type of token (ACCESS, REFRESH)
            ip_address: IP address from which token was created
            user_agent: User agent from which token was created
            custom_expiry: Custom expiry time (overrides default)
            token_id: Optional UUID string for the token
        
        Raises:
            ValidationException: If validation fails
        """
        super().__init__(token_id)
        
        self.user_id = self._validate_user_id(user_id)
        self.token_hash = self._hash_token(token)
        self.token_type = self._validate_token_type(token_type)
        self.expires_at = custom_expiry or self._calculate_expiry(token_type)
        self.is_revoked = False
        self.revoked_at: Optional[datetime] = None
        self.revoked_reason: Optional[str] = None
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def _validate_user_id(self, user_id: str) -> str:
        """Validate user ID."""
        if not user_id or not user_id.strip():
            raise ValidationException("User ID is required")
        return user_id.strip()
    
    def _validate_token_type(self, token_type: TokenType) -> TokenType:
        """Validate token type."""
        if not isinstance(token_type, TokenType):
            raise ValidationException("Token type must be a valid TokenType enum")
        return token_type
    
    def _hash_token(self, token: str) -> str:
        """
        Create SHA-256 hash of the token for storage.
        
        Args:
            token: JWT token string
        
        Returns:
            SHA-256 hash of the token
        """
        if not token:
            raise ValidationException("Token is required")
        
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    def _calculate_expiry(self, token_type: TokenType) -> datetime:
        """
        Calculate token expiry based on type.
        
        Args:
            token_type: Type of token
        
        Returns:
            Expiry datetime
        """
        now = datetime.now(timezone.utc)
        
        if token_type == TokenType.ACCESS:
            return now + timedelta(hours=self.ACCESS_TOKEN_EXPIRY_HOURS)
        elif token_type == TokenType.REFRESH:
            return now + timedelta(days=self.REFRESH_TOKEN_EXPIRY_DAYS)
        else:
            # Default to access token expiry
            return now + timedelta(hours=self.ACCESS_TOKEN_EXPIRY_HOURS)
    
    def is_valid(self) -> bool:
        """
        Check if the token is valid (not revoked and not expired).
        
        Returns:
            True if token is valid, False otherwise
        """
        if self.is_revoked:
            return False
        
        return datetime.now(timezone.utc) < self.expires_at
    
    def is_expired(self) -> bool:
        """
        Check if the token has expired.
        
        Returns:
            True if expired, False otherwise
        """
        return datetime.now(timezone.utc) >= self.expires_at
    
    def verify_token(self, token: str) -> bool:
        """
        Verify if the provided token matches this token record.
        
        Args:
            token: JWT token string to verify
        
        Returns:
            True if token matches and is valid, False otherwise
        
        Raises:
            RevokedTokenException: If token has been revoked
        """
        if self.is_revoked:
            raise RevokedTokenException(f"Token has been revoked: {self.revoked_reason}")
        
        if self.is_expired():
            return False
        
        token_hash = self._hash_token(token)
        return token_hash == self.token_hash
    
    def revoke(self, reason: str = "Manual revocation") -> None:
        """
        Revoke the token.
        
        Args:
            reason: Reason for revocation
        """
        if self.is_revoked:
            return  # Already revoked
        
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)
        self.revoked_reason = reason
        self.update_timestamp()
    
    def get_time_until_expiry(self) -> timedelta:
        """
        Get time remaining until token expires.
        
        Returns:
            Time remaining as timedelta, or zero if expired
        """
        if self.is_expired():
            return timedelta(0)
        
        return self.expires_at - datetime.now(timezone.utc)
    
    def extend_expiry(self, additional_time: timedelta) -> None:
        """
        Extend token expiry time.
        
        Args:
            additional_time: Additional time to add to expiry
        
        Raises:
            ValidationException: If token is revoked
        """
        if self.is_revoked:
            raise ValidationException("Cannot extend expiry of revoked token")
        
        self.expires_at += additional_time
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convert token to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token_hash": self.token_hash,
            "token_type": self.token_type.value,
            "expires_at": self.expires_at.isoformat(),
            "is_revoked": self.is_revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revoked_reason": self.revoked_reason,
            "created_at": self.created_at.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "updated_at": self.updated_at.isoformat()
        }
    
    def __str__(self) -> str:
        """String representation of the token."""
        status = "revoked" if self.is_revoked else ("expired" if self.is_expired() else "active")
        return f"AuthenticationToken(id='{self.id}', type='{self.token_type.value}', status='{status}')"
