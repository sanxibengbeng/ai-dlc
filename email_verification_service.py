"""
EmailVerificationService for the User Management domain model.
"""

from typing import Optional, Dict, Any

from user import User
from email_verification import EmailVerification
from security_audit_log import SecurityAuditLog
from user_repository import UserRepository
from email_verification_repository import EmailVerificationRepository
from security_audit_log_repository import SecurityAuditLogRepository
from enums import SecurityEventType
from exceptions import ValidationException, ExpiredTokenException, EntityNotFoundException
from logging_config import logger


class EmailVerificationService:
    """
    Service for handling email verification workflow.
    
    Orchestrates the email verification process including:
    - Token validation and verification
    - Account activation
    - Resending verification emails
    - Security audit logging
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        email_verification_repository: EmailVerificationRepository,
        audit_log_repository: SecurityAuditLogRepository
    ):
        """
        Initialize the email verification service with required repositories.
        
        Args:
            user_repository: Repository for user entities
            email_verification_repository: Repository for email verifications
            audit_log_repository: Repository for security audit logs
        """
        self.user_repository = user_repository
        self.email_verification_repository = email_verification_repository
        self.audit_log_repository = audit_log_repository
    
    def verify_email(
        self,
        verification_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify email using verification token and activate user account.
        
        Args:
            verification_token: Email verification token
            ip_address: IP address of verification request
            user_agent: User agent of verification request
        
        Returns:
            Dictionary with verification result
        
        Raises:
            ValidationException: If token is invalid or already used
            ExpiredTokenException: If token has expired
            EntityNotFoundException: If verification record not found
        """
        logger.info(f"Starting email verification for token: {verification_token[:10]}...")
        
        try:
            # Step 1: Find verification record
            verification = self.email_verification_repository.find_by_verification_token(verification_token)
            if not verification:
                raise EntityNotFoundException("Invalid verification token")
            
            # Step 2: Find associated user
            user = self.user_repository.find_by_id(verification.user_id)
            if not user:
                raise EntityNotFoundException("User not found for verification token")
            
            # Step 3: Verify the token
            if verification.verify_email(verification_token):
                # Step 4: Activate user account
                user.activate()
                self.user_repository.save(user)
                
                # Step 5: Save verification record
                self.email_verification_repository.save(verification)
                
                # Step 6: Log successful verification
                self._log_verification_event(
                    user_id=user.id,
                    email=user.email,
                    success=True,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                logger.info(f"Email verification successful for user: {user.email}")
                
                return {
                    "success": True,
                    "user_id": user.id,
                    "email": user.email,
                    "message": "Email verified successfully. Your account is now active.",
                    "account_activated": True
                }
            else:
                # This shouldn't happen if token was found, but handle gracefully
                raise ValidationException("Token verification failed")
                
        except (ValidationException, ExpiredTokenException, EntityNotFoundException) as e:
            logger.warning(f"Email verification failed: {str(e)}")
            
            # Try to get user info for logging (if possible)
            user_id = None
            email = None
            if 'verification' in locals() and verification:
                user = self.user_repository.find_by_id(verification.user_id)
                if user:
                    user_id = user.id
                    email = user.email
            
            # Log failed verification
            self._log_verification_event(
                user_id=user_id,
                email=email,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data={"failure_reason": str(e)}
            )
            
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error during email verification: {str(e)}")
            raise ValidationException("Email verification failed due to internal error")
    
    def resend_verification_email(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resend verification email for a user.
        
        Args:
            email: Email address to resend verification for
            ip_address: IP address of resend request
            user_agent: User agent of resend request
        
        Returns:
            Dictionary with resend result
        
        Raises:
            EntityNotFoundException: If user not found
            ValidationException: If email already verified or max resends exceeded
        """
        logger.info(f"Resending verification email for: {email}")
        
        try:
            # Step 1: Find user by email
            user = self.user_repository.find_by_email(email)
            if not user:
                raise EntityNotFoundException(f"User with email '{email}' not found")
            
            # Step 2: Check if user is already active
            if user.is_active:
                raise ValidationException("Email is already verified and account is active")
            
            # Step 3: Find latest verification record
            verification = self.email_verification_repository.find_latest_by_user_id(user.id)
            if not verification:
                raise EntityNotFoundException("No verification record found for user")
            
            # Step 4: Check if already verified
            if verification.is_verified:
                raise ValidationException("Email is already verified")
            
            # Step 5: Resend verification
            new_token = verification.resend_verification()
            self.email_verification_repository.save(verification)
            
            # Step 6: Log resend event
            self._log_verification_event(
                user_id=user.id,
                email=user.email,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data={
                    "action": "resend",
                    "resend_count": verification.resend_count
                }
            )
            
            logger.info(f"Verification email resent for user: {email}")
            
            return {
                "success": True,
                "user_id": user.id,
                "email": user.email,
                "verification_token": new_token,
                "message": "Verification email has been resent. Please check your email.",
                "resend_count": verification.resend_count,
                "remaining_resends": verification.MAX_RESEND_COUNT - verification.resend_count
            }
            
        except (EntityNotFoundException, ValidationException) as e:
            logger.warning(f"Resend verification failed for {email}: {str(e)}")
            
            # Log failed resend
            user_id = None
            if 'user' in locals() and user:
                user_id = user.id
            
            self._log_verification_event(
                user_id=user_id,
                email=email,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data={
                    "action": "resend",
                    "failure_reason": str(e)
                }
            )
            
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error during resend verification for {email}: {str(e)}")
            raise ValidationException("Resend verification failed due to internal error")
    
    def check_verification_status(self, email: str) -> Dict[str, Any]:
        """
        Check the verification status for an email address.
        
        Args:
            email: Email address to check
        
        Returns:
            Dictionary with verification status
        """
        user = self.user_repository.find_by_email(email)
        if not user:
            return {
                "found": False,
                "message": "User not found"
            }
        
        verification = self.email_verification_repository.find_latest_by_user_id(user.id)
        if not verification:
            return {
                "found": True,
                "user_id": user.id,
                "email": user.email,
                "is_verified": False,
                "is_active": user.is_active,
                "message": "No verification record found"
            }
        
        return {
            "found": True,
            "user_id": user.id,
            "email": user.email,
            "is_verified": verification.is_verified,
            "is_active": user.is_active,
            "verification_created": verification.created_at.isoformat(),
            "verification_expires": verification.token_expires_at.isoformat(),
            "is_expired": verification.is_expired(),
            "resend_count": verification.resend_count,
            "can_resend": verification.can_resend(),
            "verified_at": verification.verified_at.isoformat() if verification.verified_at else None
        }
    
    def get_verification_statistics(self) -> Dict[str, Any]:
        """
        Get email verification statistics.
        
        Returns:
            Dictionary with verification statistics
        """
        # Get verification stats from repository
        verification_stats = self.email_verification_repository.get_verification_stats()
        
        # Get user stats
        total_users = self.user_repository.count()
        active_users = len(self.user_repository.find_active_users())
        inactive_users = len(self.user_repository.find_inactive_users())
        
        # Get recent verification events
        recent_verifications = self.audit_log_repository.find_by_event_type(
            SecurityEventType.EMAIL_VERIFICATION
        )
        successful_verifications = [log for log in recent_verifications if log.success]
        failed_verifications = [log for log in recent_verifications if not log.success]
        
        return {
            "user_statistics": {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "activation_rate": (active_users / total_users * 100) if total_users > 0 else 0
            },
            "verification_statistics": verification_stats,
            "recent_activity": {
                "total_verification_attempts": len(recent_verifications),
                "successful_verifications": len(successful_verifications),
                "failed_verifications": len(failed_verifications),
                "success_rate": (len(successful_verifications) / len(recent_verifications) * 100) 
                              if recent_verifications else 0
            }
        }
    
    def cleanup_expired_verifications(self) -> Dict[str, int]:
        """
        Clean up expired email verifications.
        
        Returns:
            Dictionary with cleanup statistics
        """
        logger.info("Starting cleanup of expired email verifications")
        
        expired_count = self.email_verification_repository.cleanup_expired_verifications()
        
        logger.info(f"Cleaned up {expired_count} expired email verifications")
        
        return {
            "expired_verifications_cleaned": expired_count
        }
    
    def _log_verification_event(
        self,
        user_id: Optional[str],
        email: Optional[str],
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log email verification event for audit purposes.
        
        Args:
            user_id: User ID
            email: Email address
            success: Whether verification was successful
            ip_address: IP address
            user_agent: User agent
            additional_data: Additional data to log
        """
        try:
            description = "Email verification completed" if success else "Email verification failed"
            
            # Add email to additional data if provided
            if additional_data is None:
                additional_data = {}
            if email:
                additional_data["email"] = email
            
            audit_log = SecurityAuditLog(
                event_type=SecurityEventType.EMAIL_VERIFICATION,
                event_description=description,
                success=success,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data=additional_data
            )
            self.audit_log_repository.save(audit_log)
        except Exception as e:
            logger.error(f"Failed to log verification event: {str(e)}")
    
    def force_verify_email(self, email: str, admin_user_id: str) -> Dict[str, Any]:
        """
        Force verify an email (admin function).
        
        Args:
            email: Email to force verify
            admin_user_id: ID of admin performing the action
        
        Returns:
            Dictionary with result
        
        Raises:
            EntityNotFoundException: If user not found
            ValidationException: If already verified
        """
        logger.info(f"Force verifying email: {email} by admin: {admin_user_id}")
        
        user = self.user_repository.find_by_email(email)
        if not user:
            raise EntityNotFoundException(f"User with email '{email}' not found")
        
        if user.is_active:
            raise ValidationException("User account is already active")
        
        # Activate user
        user.activate()
        self.user_repository.save(user)
        
        # Mark verification as verified
        verification = self.email_verification_repository.find_latest_by_user_id(user.id)
        if verification and not verification.is_verified:
            verification.is_verified = True
            verification.verified_at = verification.created_at.__class__.now(verification.created_at.tzinfo)
            self.email_verification_repository.save(verification)
        
        # Log admin action
        self._log_verification_event(
            user_id=user.id,
            email=user.email,
            success=True,
            additional_data={
                "action": "force_verify",
                "admin_user_id": admin_user_id
            }
        )
        
        logger.info(f"Email force verified for user: {email}")
        
        return {
            "success": True,
            "user_id": user.id,
            "email": user.email,
            "message": "Email has been force verified and account activated",
            "account_activated": True
        }
