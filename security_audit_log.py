"""
SecurityAuditLog entity for the User Management domain model.
"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from base_entity import BaseEntity
from enums import SecurityEventType
from exceptions import ValidationException


class SecurityAuditLog(BaseEntity):
    """
    SecurityAuditLog entity tracking security-related events for audit purposes.
    
    Attributes:
        id (str): Unique identifier for the audit log entry
        user_id (str): Reference to the User entity (if applicable)
        event_type (SecurityEventType): Type of security event
        event_description (str): Description of the security event
        success (bool): Whether the event was successful
        ip_address (str): IP address from which event occurred
        user_agent (str): User agent from which event occurred
        additional_data (dict): Additional event-specific data
        created_at (datetime): When the event occurred
    """
    
    def __init__(
        self,
        event_type: SecurityEventType,
        event_description: str,
        success: bool,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        log_id: Optional[str] = None
    ):
        """
        Initialize SecurityAuditLog entity.
        
        Args:
            event_type: Type of security event
            event_description: Description of the security event
            success: Whether the event was successful
            user_id: Reference to the User entity (if applicable)
            ip_address: IP address from which event occurred
            user_agent: User agent from which event occurred
            additional_data: Additional event-specific data
            log_id: Optional UUID string for the log entry
        
        Raises:
            ValidationException: If validation fails
        """
        super().__init__(log_id)
        
        self.user_id = user_id
        self.event_type = self._validate_event_type(event_type)
        self.event_description = self._validate_event_description(event_description)
        self.success = success
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.additional_data = additional_data or {}
    
    def _validate_event_type(self, event_type: SecurityEventType) -> SecurityEventType:
        """Validate event type."""
        if not isinstance(event_type, SecurityEventType):
            raise ValidationException("Event type must be a valid SecurityEventType enum")
        return event_type
    
    def _validate_event_description(self, description: str) -> str:
        """Validate event description."""
        if not description or not description.strip():
            raise ValidationException("Event description is required")
        if len(description.strip()) > 1000:
            raise ValidationException("Event description must be 1000 characters or less")
        return description.strip()
    
    def add_additional_data(self, key: str, value: Any) -> None:
        """
        Add additional data to the audit log entry.
        
        Args:
            key: Data key
            value: Data value (must be JSON serializable)
        
        Raises:
            ValidationException: If value is not JSON serializable
        """
        try:
            # Test JSON serialization
            json.dumps(value)
            self.additional_data[key] = value
        except (TypeError, ValueError) as e:
            raise ValidationException(f"Additional data value must be JSON serializable: {e}")
    
    def get_additional_data(self, key: str, default: Any = None) -> Any:
        """
        Get additional data value by key.
        
        Args:
            key: Data key
            default: Default value if key not found
        
        Returns:
            Data value or default
        """
        return self.additional_data.get(key, default)
    
    def is_user_event(self) -> bool:
        """
        Check if this is a user-specific event.
        
        Returns:
            True if user_id is set, False otherwise
        """
        return self.user_id is not None
    
    def is_success_event(self) -> bool:
        """
        Check if this event was successful.
        
        Returns:
            True if successful, False otherwise
        """
        return self.success
    
    def is_failure_event(self) -> bool:
        """
        Check if this event was a failure.
        
        Returns:
            True if failed, False otherwise
        """
        return not self.success
    
    def get_event_summary(self) -> str:
        """
        Get a summary of the event for display purposes.
        
        Returns:
            Event summary string
        """
        status = "SUCCESS" if self.success else "FAILURE"
        user_info = f" (User: {self.user_id})" if self.user_id else ""
        return f"[{status}] {self.event_type.value}: {self.event_description}{user_info}"
    
    def to_dict(self) -> dict:
        """Convert audit log to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type": self.event_type.value,
            "event_description": self.event_description,
            "success": self.success,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "additional_data": self.additional_data,
            "created_at": self.created_at.isoformat()
        }
    
    def to_json(self) -> str:
        """
        Convert audit log to JSON string.
        
        Returns:
            JSON representation of the audit log
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def create_user_registration_log(
        cls,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> 'SecurityAuditLog':
        """
        Create a user registration audit log entry.
        
        Args:
            user_id: User ID
            success: Whether registration was successful
            ip_address: IP address
            user_agent: User agent
            additional_data: Additional data
        
        Returns:
            SecurityAuditLog instance
        """
        description = "User registration completed" if success else "User registration failed"
        return cls(
            event_type=SecurityEventType.USER_REGISTRATION,
            event_description=description,
            success=success,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_data
        )
    
    @classmethod
    def create_login_log(
        cls,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> 'SecurityAuditLog':
        """
        Create a login audit log entry.
        
        Args:
            user_id: User ID
            success: Whether login was successful
            ip_address: IP address
            user_agent: User agent
            failure_reason: Reason for login failure
        
        Returns:
            SecurityAuditLog instance
        """
        if success:
            event_type = SecurityEventType.LOGIN_SUCCESS
            description = "User successfully logged in"
            additional_data = None
        else:
            event_type = SecurityEventType.LOGIN_FAILURE
            description = "User login failed"
            additional_data = {"failure_reason": failure_reason} if failure_reason else None
        
        return cls(
            event_type=event_type,
            event_description=description,
            success=success,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_data
        )
    
    @classmethod
    def create_password_reset_log(
        cls,
        user_id: str,
        event_type: SecurityEventType,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> 'SecurityAuditLog':
        """
        Create a password reset audit log entry.
        
        Args:
            user_id: User ID
            event_type: PASSWORD_RESET_REQUEST or PASSWORD_RESET_COMPLETE
            success: Whether the operation was successful
            ip_address: IP address
            user_agent: User agent
        
        Returns:
            SecurityAuditLog instance
        """
        if event_type == SecurityEventType.PASSWORD_RESET_REQUEST:
            description = "Password reset requested" if success else "Password reset request failed"
        elif event_type == SecurityEventType.PASSWORD_RESET_COMPLETE:
            description = "Password reset completed" if success else "Password reset completion failed"
        else:
            description = f"Password reset event: {event_type.value}"
        
        return cls(
            event_type=event_type,
            event_description=description,
            success=success,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def __str__(self) -> str:
        """String representation of the audit log."""
        return f"SecurityAuditLog(id='{self.id}', event='{self.event_type.value}', success={self.success})"
