"""
User entity for the User Management domain model.
"""

from datetime import datetime, timezone
from typing import Optional
import re

from base_entity import BaseEntity
from enums import UserRole
from exceptions import ValidationException


class User(BaseEntity):
    """
    User entity representing basic user information across the system.
    
    Attributes:
        id (str): Unique identifier for the user
        name (str): Full name of the user
        email (str): Email address (used for login)
        role (UserRole): User role in the system
        employee_id (str): Company employee ID (pure number)
        department (str): Department or business unit
        job_title (str): Official job title
        is_active (bool): Whether the user account is active
        created_at (datetime): When the user account was created
        last_login_at (datetime): When the user last logged in
        profile_picture_url (str): URL to profile picture
        phone_number (str): Contact phone number
    """
    
    def __init__(
        self,
        name: str,
        email: str,
        role: UserRole,
        employee_id: str,
        department: str,
        job_title: str,
        user_id: Optional[str] = None,
        is_active: bool = False,
        last_login_at: Optional[datetime] = None,
        profile_picture_url: Optional[str] = None,
        phone_number: Optional[str] = None
    ):
        """
        Initialize User entity.
        
        Args:
            name: Full name of the user
            email: Email address (used for login)
            role: User role in the system
            employee_id: Company employee ID (pure number)
            department: Department or business unit
            job_title: Official job title
            user_id: Optional UUID string for the user
            is_active: Whether the user account is active (default: False)
            last_login_at: When the user last logged in
            profile_picture_url: URL to profile picture
            phone_number: Contact phone number
        
        Raises:
            ValidationException: If validation fails
        """
        super().__init__(user_id)
        
        # Validate and set required fields
        self.name = self._validate_name(name)
        self.email = self._validate_email(email)
        self.role = self._validate_role(role)
        self.employee_id = self._validate_employee_id(employee_id)
        self.department = self._validate_department(department)
        self.job_title = self._validate_job_title(job_title)
        
        # Set other fields
        self.is_active = is_active
        self.last_login_at = last_login_at
        self.profile_picture_url = profile_picture_url
        self.phone_number = phone_number
    
    def _validate_name(self, name: str) -> str:
        """Validate user name."""
        if not name or not name.strip():
            raise ValidationException("Name is required")
        if len(name.strip()) > 255:
            raise ValidationException("Name must be 255 characters or less")
        return name.strip()
    
    def _validate_email(self, email: str) -> str:
        """Validate email format."""
        if not email or not email.strip():
            raise ValidationException("Email is required")
        
        email = email.strip().lower()
        
        # Basic email format validation (RFC 5322 compliant)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationException("Invalid email format")
        
        return email
    
    def _validate_role(self, role: UserRole) -> UserRole:
        """Validate user role."""
        if not isinstance(role, UserRole):
            raise ValidationException("Role must be a valid UserRole enum")
        return role
    
    def _validate_employee_id(self, employee_id: str) -> str:
        """Validate employee ID (must be pure numeric string)."""
        if not employee_id or not employee_id.strip():
            raise ValidationException("Employee ID is required")
        
        employee_id = employee_id.strip()
        
        if not employee_id.isdigit():
            raise ValidationException("Employee ID must be a pure numeric string")
        
        return employee_id
    
    def _validate_department(self, department: str) -> str:
        """Validate department."""
        if not department or not department.strip():
            raise ValidationException("Department is required")
        if len(department.strip()) > 255:
            raise ValidationException("Department must be 255 characters or less")
        return department.strip()
    
    def _validate_job_title(self, job_title: str) -> str:
        """Validate job title."""
        if not job_title or not job_title.strip():
            raise ValidationException("Job title is required")
        if len(job_title.strip()) > 255:
            raise ValidationException("Job title must be 255 characters or less")
        return job_title.strip()
    
    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True
        self.update_timestamp()
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
        self.update_timestamp()
    
    def update_last_login(self) -> None:
        """Update the last login timestamp to current UTC time."""
        self.last_login_at = datetime.now(timezone.utc)
        self.update_timestamp()
    
    def update_profile(
        self,
        name: Optional[str] = None,
        department: Optional[str] = None,
        job_title: Optional[str] = None,
        profile_picture_url: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> None:
        """
        Update user profile information.
        
        Args:
            name: New name (optional)
            department: New department (optional)
            job_title: New job title (optional)
            profile_picture_url: New profile picture URL (optional)
            phone_number: New phone number (optional)
        """
        if name is not None:
            self.name = self._validate_name(name)
        if department is not None:
            self.department = self._validate_department(department)
        if job_title is not None:
            self.job_title = self._validate_job_title(job_title)
        if profile_picture_url is not None:
            self.profile_picture_url = profile_picture_url
        if phone_number is not None:
            self.phone_number = phone_number
        
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convert user to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "employee_id": self.employee_id,
            "department": self.department,
            "job_title": self.job_title,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "profile_picture_url": self.profile_picture_url,
            "phone_number": self.phone_number,
            "updated_at": self.updated_at.isoformat()
        }
    
    def __str__(self) -> str:
        """String representation of the user."""
        return f"User(id='{self.id}', name='{self.name}', email='{self.email}', role='{self.role.value}')"
