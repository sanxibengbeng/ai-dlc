"""
UserCredentials entity for the User Management domain model.
"""

import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional

from base_entity import BaseEntity
from exceptions import ValidationException, AccountLockedException


class UserCredentials(BaseEntity):
    """
    UserCredentials entity managing password storage and authentication credentials.
    
    Attributes:
        id (str): Unique identifier for the credentials
        user_id (str): Reference to the User entity
        password_hash (str): Hashed password using bcrypt
        password_salt (str): Salt used for password hashing
        password_last_changed (datetime): When the password was last changed
        failed_login_attempts (int): Number of consecutive failed login attempts
        account_locked_until (datetime): Account lockout expiration time
        must_change_password (bool): Whether user must change password on next login
        created_at (datetime): When the credentials were created
        updated_at (datetime): When the credentials were last updated
    """
    
    # Security constants
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    BCRYPT_ROUNDS = 12
    MIN_PASSWORD_LENGTH = 6
    
    def __init__(
        self,
        user_id: str,
        password: str,
        credentials_id: Optional[str] = None,
        must_change_password: bool = False
    ):
        """
        Initialize UserCredentials entity.
        
        Args:
            user_id: Reference to the User entity
            password: Plain text password to be hashed
            credentials_id: Optional UUID string for the credentials
            must_change_password: Whether user must change password on next login
        
        Raises:
            ValidationException: If validation fails
        """
        super().__init__(credentials_id)
        
        self.user_id = self._validate_user_id(user_id)
        self.password_hash, self.password_salt = self._hash_password(password)
        self.password_last_changed = datetime.now(timezone.utc)
        self.failed_login_attempts = 0
        self.account_locked_until: Optional[datetime] = None
        self.must_change_password = must_change_password
    
    def _validate_user_id(self, user_id: str) -> str:
        """Validate user ID."""
        if not user_id or not user_id.strip():
            raise ValidationException("User ID is required")
        return user_id.strip()
    
    def _validate_password(self, password: str) -> str:
        """Validate password requirements."""
        if not password:
            raise ValidationException("Password is required")
        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValidationException(f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters long")
        return password
    
    def _hash_password(self, password: str) -> tuple[str, str]:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
        
        Returns:
            Tuple of (password_hash, password_salt)
        """
        validated_password = self._validate_password(password)
        
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=self.BCRYPT_ROUNDS)
        password_hash = bcrypt.hashpw(validated_password.encode('utf-8'), salt)
        
        return password_hash.decode('utf-8'), salt.decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
        
        Returns:
            True if password matches, False otherwise
        
        Raises:
            AccountLockedException: If account is currently locked
        """
        # Check if account is locked
        if self.is_account_locked():
            raise AccountLockedException("Account is temporarily locked due to too many failed login attempts")
        
        if not password:
            return False
        
        try:
            # Verify password using bcrypt
            is_valid = bcrypt.checkpw(
                password.encode('utf-8'),
                self.password_hash.encode('utf-8')
            )
            
            if is_valid:
                self._reset_failed_attempts()
            else:
                self._increment_failed_attempts()
            
            return is_valid
        
        except Exception:
            self._increment_failed_attempts()
            return False
    
    def change_password(self, old_password: str, new_password: str) -> None:
        """
        Change user password.
        
        Args:
            old_password: Current password for verification
            new_password: New password to set
        
        Raises:
            ValidationException: If old password is incorrect or new password is invalid
            AccountLockedException: If account is currently locked
        """
        # Verify old password
        if not self.verify_password(old_password):
            raise ValidationException("Current password is incorrect")
        
        # Set new password
        self.password_hash, self.password_salt = self._hash_password(new_password)
        self.password_last_changed = datetime.now(timezone.utc)
        self.must_change_password = False
        self.update_timestamp()
    
    def reset_password(self, new_password: str) -> None:
        """
        Reset password (used during password reset flow).
        
        Args:
            new_password: New password to set
        """
        self.password_hash, self.password_salt = self._hash_password(new_password)
        self.password_last_changed = datetime.now(timezone.utc)
        self.must_change_password = False
        self._reset_failed_attempts()
        self.update_timestamp()
    
    def _increment_failed_attempts(self) -> None:
        """Increment failed login attempts and lock account if necessary."""
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            self.account_locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=self.LOCKOUT_DURATION_MINUTES
            )
        
        self.update_timestamp()
    
    def _reset_failed_attempts(self) -> None:
        """Reset failed login attempts and unlock account."""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.update_timestamp()
    
    def is_account_locked(self) -> bool:
        """
        Check if account is currently locked.
        
        Returns:
            True if account is locked, False otherwise
        """
        if self.account_locked_until is None:
            return False
        
        # Check if lockout period has expired
        if datetime.now(timezone.utc) >= self.account_locked_until:
            self._reset_failed_attempts()
            return False
        
        return True
    
    def unlock_account(self) -> None:
        """Manually unlock account (admin function)."""
        self._reset_failed_attempts()
    
    def force_password_change(self) -> None:
        """Force user to change password on next login."""
        self.must_change_password = True
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convert credentials to dictionary representation (excluding sensitive data)."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "password_last_changed": self.password_last_changed.isoformat(),
            "failed_login_attempts": self.failed_login_attempts,
            "account_locked_until": self.account_locked_until.isoformat() if self.account_locked_until else None,
            "must_change_password": self.must_change_password,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def __str__(self) -> str:
        """String representation of the credentials."""
        return f"UserCredentials(id='{self.id}', user_id='{self.user_id}')"
