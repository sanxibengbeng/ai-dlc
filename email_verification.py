"""
EmailVerification entity for the User Management domain model.
"""

import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from base_entity import BaseEntity
from exceptions import ValidationException, ExpiredTokenException


class EmailVerification(BaseEntity):
    """
    EmailVerification entity managing the email verification process for account activation.
    
    Attributes:
        id (str): Unique identifier for the verification
        user_id (str): Reference to the User entity
        email (str): Email address to be verified
        verification_token (str): Unique token for verification
        token_expires_at (datetime): When the verification token expires (1 week)
        is_verified (bool): Whether the email has been verified
        verified_at (datetime): When the email was verified
        created_at (datetime): When the verification was created
        resend_count (int): Number of times verification email was resent
        last_resend_at (datetime): When verification email was last resent
        updated_at (datetime): When the verification was last updated
    """
    
    # Configuration constants
    TOKEN_EXPIRY_DAYS = 7
    MAX_RESEND_COUNT = 3
    TOKEN_LENGTH = 32
    
    def __init__(
        self,
        user_id: str,
        email: str,
        verification_id: Optional[str] = None
    ):
        """
        Initialize EmailVerification entity.
        
        Args:
            user_id: Reference to the User entity
            email: Email address to be verified
            verification_id: Optional UUID string for the verification
        
        Raises:
            ValidationException: If validation fails
        """
        super().__init__(verification_id)
        
        self.user_id = self._validate_user_id(user_id)
        self.email = self._validate_email(email)
        self.verification_token = self._generate_verification_token()
        self.token_expires_at = datetime.now(timezone.utc) + timedelta(days=self.TOKEN_EXPIRY_DAYS)
        self.is_verified = False
        self.verified_at: Optional[datetime] = None
        self.resend_count = 0
        self.last_resend_at: Optional[datetime] = None
    
    def _validate_user_id(self, user_id: str) -> str:
        """Validate user ID."""
        if not user_id or not user_id.strip():
            raise ValidationException("User ID is required")
        return user_id.strip()
    
    def _validate_email(self, email: str) -> str:
        """Validate email format."""
        if not email or not email.strip():
            raise ValidationException("Email is required")
        return email.strip().lower()
    
    def _generate_verification_token(self) -> str:
        """
        Generate a secure random verification token.
        
        Returns:
            Secure random token string
        """
        return secrets.token_urlsafe(self.TOKEN_LENGTH)
    
    def is_token_valid(self) -> bool:
        """
        Check if the verification token is still valid.
        
        Returns:
            True if token is valid and not expired, False otherwise
        """
        if self.is_verified:
            return False
        
        return datetime.now(timezone.utc) < self.token_expires_at
    
    def verify_email(self, token: str) -> bool:
        """
        Verify email using the provided token.
        
        Args:
            token: Verification token to validate
        
        Returns:
            True if verification successful, False otherwise
        
        Raises:
            ExpiredTokenException: If token has expired
            ValidationException: If already verified
        """
        if self.is_verified:
            raise ValidationException("Email is already verified")
        
        if not self.is_token_valid():
            raise ExpiredTokenException("Verification token has expired")
        
        if not token or token != self.verification_token:
            return False
        
        # Mark as verified
        self.is_verified = True
        self.verified_at = datetime.now(timezone.utc)
        self.update_timestamp()
        
        return True
    
    def resend_verification(self) -> str:
        """
        Generate new verification token for resending email.
        
        Returns:
            New verification token
        
        Raises:
            ValidationException: If already verified or max resend count exceeded
        """
        if self.is_verified:
            raise ValidationException("Email is already verified")
        
        if self.resend_count >= self.MAX_RESEND_COUNT:
            raise ValidationException(f"Maximum resend limit ({self.MAX_RESEND_COUNT}) exceeded")
        
        # Generate new token and extend expiry
        self.verification_token = self._generate_verification_token()
        self.token_expires_at = datetime.now(timezone.utc) + timedelta(days=self.TOKEN_EXPIRY_DAYS)
        self.resend_count += 1
        self.last_resend_at = datetime.now(timezone.utc)
        self.update_timestamp()
        
        return self.verification_token
    
    def is_expired(self) -> bool:
        """
        Check if the verification token has expired.
        
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
    
    def can_resend(self) -> bool:
        """
        Check if verification email can be resent.
        
        Returns:
            True if can resend, False otherwise
        """
        return not self.is_verified and self.resend_count < self.MAX_RESEND_COUNT
    
    def to_dict(self) -> dict:
        """Convert verification to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.email,
            "verification_token": self.verification_token,
            "token_expires_at": self.token_expires_at.isoformat(),
            "is_verified": self.is_verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "created_at": self.created_at.isoformat(),
            "resend_count": self.resend_count,
            "last_resend_at": self.last_resend_at.isoformat() if self.last_resend_at else None,
            "updated_at": self.updated_at.isoformat()
        }
    
    def __str__(self) -> str:
        """String representation of the verification."""
        status = "verified" if self.is_verified else "pending"
        return f"EmailVerification(id='{self.id}', email='{self.email}', status='{status}')"
