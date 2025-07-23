"""
UserRegistrationService for the User Management domain model.
"""

from typing import Optional, Dict, Any

from user import User
from user_credentials import UserCredentials
from email_verification import EmailVerification
from security_audit_log import SecurityAuditLog
from user_repository import UserRepository
from user_credentials_repository import UserCredentialsRepository
from email_verification_repository import EmailVerificationRepository
from security_audit_log_repository import SecurityAuditLogRepository
from enums import UserRole, SecurityEventType
from exceptions import DuplicateEntityException, ValidationException
from logging_config import logger


class UserRegistrationService:
    """
    Service for handling user registration workflow.
    
    Orchestrates the complete user registration process including:
    - User creation with validation
    - Credentials setup
    - Email verification initiation
    - Security audit logging
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        credentials_repository: UserCredentialsRepository,
        email_verification_repository: EmailVerificationRepository,
        audit_log_repository: SecurityAuditLogRepository
    ):
        """
        Initialize the registration service with required repositories.
        
        Args:
            user_repository: Repository for user entities
            credentials_repository: Repository for user credentials
            email_verification_repository: Repository for email verifications
            audit_log_repository: Repository for security audit logs
        """
        self.user_repository = user_repository
        self.credentials_repository = credentials_repository
        self.email_verification_repository = email_verification_repository
        self.audit_log_repository = audit_log_repository
    
    def register_user(
        self,
        name: str,
        email: str,
        employee_id: str,
        department: str,
        job_title: str,
        password: str,
        role: UserRole,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a new user with complete workflow.
        
        Args:
            name: Full name of the user
            email: Email address
            employee_id: Company employee ID
            department: Department name
            job_title: Job title
            password: Password
            role: User role
            ip_address: IP address of registration request
            user_agent: User agent of registration request
        
        Returns:
            Dictionary with registration result
        
        Raises:
            DuplicateEntityException: If email or employee ID already exists
            ValidationException: If validation fails
        """
        logger.info(f"Starting user registration for email: {email}")
        
        try:
            # Step 1: Validate uniqueness
            self._validate_uniqueness(email, employee_id)
            
            # Step 2: Create user entity (inactive by default)
            user = User(
                name=name,
                email=email,
                role=role,
                employee_id=employee_id,
                department=department,
                job_title=job_title,
                is_active=False  # User starts inactive until email verification
            )
            
            # Step 3: Save user
            saved_user = self.user_repository.save(user)
            logger.info(f"User created with ID: {saved_user.id}")
            
            # Step 4: Create credentials
            credentials = UserCredentials(
                user_id=saved_user.id,
                password=password
            )
            saved_credentials = self.credentials_repository.save(credentials)
            logger.info(f"Credentials created for user: {saved_user.id}")
            
            # Step 5: Create email verification
            email_verification = EmailVerification(
                user_id=saved_user.id,
                email=saved_user.email
            )
            saved_verification = self.email_verification_repository.save(email_verification)
            logger.info(f"Email verification created for user: {saved_user.id}")
            
            # Step 6: Log successful registration
            self._log_registration_event(
                user_id=saved_user.id,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data={
                    "role": role.value,
                    "department": department,
                    "employee_id": employee_id
                }
            )
            
            logger.info(f"User registration completed successfully for: {email}")
            
            return {
                "success": True,
                "user_id": saved_user.id,
                "email": saved_user.email,
                "verification_token": saved_verification.verification_token,
                "message": "Registration successful. Please check your email for verification instructions.",
                "requires_email_verification": True
            }
            
        except (DuplicateEntityException, ValidationException) as e:
            logger.warning(f"User registration failed for {email}: {str(e)}")
            
            # Log failed registration
            self._log_registration_event(
                user_id=None,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data={
                    "email": email,
                    "employee_id": employee_id,
                    "failure_reason": str(e)
                }
            )
            
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error during registration for {email}: {str(e)}")
            
            # Log failed registration
            self._log_registration_event(
                user_id=None,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data={
                    "email": email,
                    "employee_id": employee_id,
                    "failure_reason": "Internal error"
                }
            )
            
            raise ValidationException("Registration failed due to internal error")
    
    def _validate_uniqueness(self, email: str, employee_id: str) -> None:
        """
        Validate that email and employee ID are unique.
        
        Args:
            email: Email to validate
            employee_id: Employee ID to validate
        
        Raises:
            DuplicateEntityException: If email or employee ID already exists
        """
        # Check email uniqueness
        if self.user_repository.email_exists(email):
            raise DuplicateEntityException(f"User with email '{email}' already exists")
        
        # Check employee ID uniqueness
        if self.user_repository.employee_id_exists(employee_id):
            raise DuplicateEntityException(f"User with employee ID '{employee_id}' already exists")
    
    def _log_registration_event(
        self,
        user_id: Optional[str],
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log user registration event for audit purposes.
        
        Args:
            user_id: User ID (if registration was successful)
            success: Whether registration was successful
            ip_address: IP address
            user_agent: User agent
            additional_data: Additional data to log
        """
        try:
            audit_log = SecurityAuditLog.create_user_registration_log(
                user_id=user_id,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data=additional_data
            )
            self.audit_log_repository.save(audit_log)
        except Exception as e:
            logger.error(f"Failed to log registration event: {str(e)}")
    
    def check_registration_eligibility(self, email: str, employee_id: str) -> Dict[str, Any]:
        """
        Check if a user can register with the given email and employee ID.
        
        Args:
            email: Email to check
            employee_id: Employee ID to check
        
        Returns:
            Dictionary with eligibility status
        """
        result = {
            "eligible": True,
            "issues": []
        }
        
        # Check email availability
        if self.user_repository.email_exists(email):
            result["eligible"] = False
            result["issues"].append(f"Email '{email}' is already registered")
        
        # Check employee ID availability
        if self.user_repository.employee_id_exists(employee_id):
            result["eligible"] = False
            result["issues"].append(f"Employee ID '{employee_id}' is already registered")
        
        return result
    
    def get_registration_statistics(self) -> Dict[str, Any]:
        """
        Get registration statistics.
        
        Returns:
            Dictionary with registration statistics
        """
        # Get all users
        all_users = self.user_repository.find_all()
        active_users = self.user_repository.find_active_users()
        inactive_users = self.user_repository.find_inactive_users()
        
        # Get users by role
        solution_architects = self.user_repository.find_by_role(UserRole.SOLUTION_ARCHITECT)
        sales_managers = self.user_repository.find_by_role(UserRole.SALES_MANAGER)
        
        # Get recent registration events
        recent_registrations = self.audit_log_repository.find_by_event_type(
            SecurityEventType.USER_REGISTRATION
        )
        successful_registrations = [log for log in recent_registrations if log.success]
        failed_registrations = [log for log in recent_registrations if not log.success]
        
        return {
            "total_users": len(all_users),
            "active_users": len(active_users),
            "inactive_users": len(inactive_users),
            "solution_architects": len(solution_architects),
            "sales_managers": len(sales_managers),
            "total_registration_attempts": len(recent_registrations),
            "successful_registrations": len(successful_registrations),
            "failed_registrations": len(failed_registrations),
            "departments": self.user_repository.get_all_departments(),
            "job_titles": self.user_repository.get_all_job_titles()
        }
    
    def cleanup_incomplete_registrations(self, hours_old: int = 24) -> Dict[str, int]:
        """
        Clean up incomplete registrations (inactive users with expired verifications).
        
        Args:
            hours_old: Hours after which to consider registrations incomplete
        
        Returns:
            Dictionary with cleanup statistics
        """
        logger.info(f"Starting cleanup of incomplete registrations older than {hours_old} hours")
        
        # Find expired email verifications
        expired_verifications = self.email_verification_repository.find_expired_verifications()
        
        users_cleaned = 0
        credentials_cleaned = 0
        verifications_cleaned = 0
        
        for verification in expired_verifications:
            # Check if user is still inactive
            user = self.user_repository.find_by_id(verification.user_id)
            if user and not user.is_active:
                # Delete user, credentials, and verification
                if self.user_repository.delete_by_id(user.id):
                    users_cleaned += 1
                
                if self.credentials_repository.delete_by_user_id(user.id):
                    credentials_cleaned += 1
                
                if self.email_verification_repository.delete_by_id(verification.id):
                    verifications_cleaned += 1
                
                logger.info(f"Cleaned up incomplete registration for user: {user.email}")
        
        result = {
            "users_cleaned": users_cleaned,
            "credentials_cleaned": credentials_cleaned,
            "verifications_cleaned": verifications_cleaned
        }
        
        logger.info(f"Cleanup completed: {result}")
        return result
