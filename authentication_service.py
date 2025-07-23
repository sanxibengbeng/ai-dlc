"""
AuthenticationService for the User Management domain model.
"""

from typing import Optional, Dict, Any

from user import User
from user_credentials import UserCredentials
from authentication_token import AuthenticationToken
from security_audit_log import SecurityAuditLog
from user_repository import UserRepository
from user_credentials_repository import UserCredentialsRepository
from authentication_token_repository import AuthenticationTokenRepository
from security_audit_log_repository import SecurityAuditLogRepository
from enums import TokenType, SecurityEventType
from exceptions import (
    AuthenticationException, AccountLockedException, AccountNotActivatedException,
    InvalidCredentialsException, EntityNotFoundException, ValidationException
)
from logging_config import logger


class AuthenticationService:
    """
    Service for handling user authentication workflow.
    
    Orchestrates the authentication process including:
    - User login with credential validation
    - Token generation and management
    - Account lockout handling
    - Security audit logging
    - Logout operations
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        credentials_repository: UserCredentialsRepository,
        token_repository: AuthenticationTokenRepository,
        audit_log_repository: SecurityAuditLogRepository
    ):
        """
        Initialize the authentication service with required repositories.
        
        Args:
            user_repository: Repository for user entities
            credentials_repository: Repository for user credentials
            token_repository: Repository for authentication tokens
            audit_log_repository: Repository for security audit logs
        """
        self.user_repository = user_repository
        self.credentials_repository = credentials_repository
        self.token_repository = token_repository
        self.audit_log_repository = audit_log_repository
    
    def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email address
            password: User password
            ip_address: IP address of login request
            user_agent: User agent of login request
        
        Returns:
            Dictionary with authentication result including access token
        
        Raises:
            InvalidCredentialsException: If credentials are invalid
            AccountLockedException: If account is locked
            AccountNotActivatedException: If account is not activated
            EntityNotFoundException: If user not found
        """
        logger.info(f"Authentication attempt for email: {email}")
        
        user = None
        failure_reason = None
        
        try:
            # Step 1: Find user by email
            user = self.user_repository.find_by_email(email)
            if not user:
                failure_reason = "User not found"
                raise InvalidCredentialsException("Invalid email or password")
            
            # Step 2: Check if account is active
            if not user.is_active:
                failure_reason = "Account not activated"
                raise AccountNotActivatedException("Account is not activated. Please verify your email.")
            
            # Step 3: Find user credentials
            credentials = self.credentials_repository.find_by_user_id(user.id)
            if not credentials:
                failure_reason = "Credentials not found"
                raise InvalidCredentialsException("Invalid email or password")
            
            # Step 4: Verify password (this handles account lockout internally)
            if not credentials.verify_password(password):
                failure_reason = "Invalid password"
                raise InvalidCredentialsException("Invalid email or password")
            
            # Step 5: Check if password change is required
            must_change_password = credentials.must_change_password
            
            # Step 6: Generate access token
            token_payload = self._create_token_payload(user)
            access_token = self._generate_jwt_token(token_payload)
            
            # Step 7: Store token record
            token_record = AuthenticationToken(
                user_id=user.id,
                token=access_token,
                token_type=TokenType.ACCESS,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.token_repository.save(token_record)
            
            # Step 8: Update user last login
            user.update_last_login()
            self.user_repository.save(user)
            
            # Step 9: Log successful login
            self._log_authentication_event(
                user_id=user.id,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data={
                    "token_id": token_record.id,
                    "must_change_password": must_change_password
                }
            )
            
            logger.info(f"Authentication successful for user: {email}")
            
            return {
                "success": True,
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "access_token": access_token,
                "token_expires_at": token_record.expires_at.isoformat(),
                "must_change_password": must_change_password,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "message": "Authentication successful"
            }
            
        except (AccountLockedException, AccountNotActivatedException) as e:
            logger.warning(f"Authentication failed for {email}: {str(e)}")
            
            # Log failed login with specific reason
            self._log_authentication_event(
                user_id=user.id if user else None,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=str(e)
            )
            
            raise
            
        except InvalidCredentialsException as e:
            logger.warning(f"Authentication failed for {email}: Invalid credentials")
            
            # Log failed login
            self._log_authentication_event(
                user_id=user.id if user else None,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=failure_reason or "Invalid credentials"
            )
            
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error during authentication for {email}: {str(e)}")
            
            # Log failed login
            self._log_authentication_event(
                user_id=user.id if user else None,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason="Internal error"
            )
            
            raise AuthenticationException("Authentication failed due to internal error")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate an authentication token.
        
        Args:
            token: JWT token to validate
        
        Returns:
            Dictionary with validation result and user info
        
        Raises:
            ValidationException: If token is invalid, expired, or revoked
        """
        try:
            # Step 1: Decode token to get token hash
            token_hash = AuthenticationToken._hash_token(None, token)
            
            # Step 2: Find token record
            token_record = self.token_repository.find_by_token_hash(token_hash)
            if not token_record:
                raise ValidationException("Invalid token")
            
            # Step 3: Verify token
            if not token_record.verify_token(token):
                raise ValidationException("Token validation failed")
            
            # Step 4: Find user
            user = self.user_repository.find_by_id(token_record.user_id)
            if not user:
                raise ValidationException("User not found for token")
            
            # Step 5: Check if user is still active
            if not user.is_active:
                raise ValidationException("User account is not active")
            
            return {
                "valid": True,
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "token_id": token_record.id,
                "expires_at": token_record.expires_at.isoformat()
            }
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {str(e)}")
            raise ValidationException("Token validation failed")
    
    def logout_user(
        self,
        token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Logout user by revoking their token.
        
        Args:
            token: JWT token to revoke
            ip_address: IP address of logout request
            user_agent: User agent of logout request
        
        Returns:
            Dictionary with logout result
        """
        try:
            # Step 1: Validate token first
            token_info = self.validate_token(token)
            user_id = token_info["user_id"]
            
            # Step 2: Find and revoke token
            token_hash = AuthenticationToken._hash_token(None, token)
            token_record = self.token_repository.find_by_token_hash(token_hash)
            
            if token_record:
                token_record.revoke("User logout")
                self.token_repository.save(token_record)
            
            # Step 3: Log logout event
            audit_log = SecurityAuditLog(
                event_type=SecurityEventType.TOKEN_REVOKED,
                event_description="User logged out",
                success=True,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_data={"reason": "User logout"}
            )
            self.audit_log_repository.save(audit_log)
            
            logger.info(f"User logged out successfully: {user_id}")
            
            return {
                "success": True,
                "message": "Logout successful"
            }
            
        except ValidationException as e:
            logger.warning(f"Logout failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during logout: {str(e)}")
            raise ValidationException("Logout failed due to internal error")
    
    def revoke_all_user_tokens(
        self,
        user_id: str,
        reason: str = "Security revocation"
    ) -> Dict[str, Any]:
        """
        Revoke all tokens for a user (security function).
        
        Args:
            user_id: User ID
            reason: Reason for revocation
        
        Returns:
            Dictionary with revocation result
        """
        logger.info(f"Revoking all tokens for user: {user_id}")
        
        revoked_count = self.token_repository.revoke_user_tokens(user_id, reason)
        
        # Log revocation event
        audit_log = SecurityAuditLog(
            event_type=SecurityEventType.TOKEN_REVOKED,
            event_description=f"All user tokens revoked: {reason}",
            success=True,
            user_id=user_id,
            additional_data={
                "reason": reason,
                "tokens_revoked": revoked_count
            }
        )
        self.audit_log_repository.save(audit_log)
        
        logger.info(f"Revoked {revoked_count} tokens for user: {user_id}")
        
        return {
            "success": True,
            "tokens_revoked": revoked_count,
            "message": f"Revoked {revoked_count} tokens"
        }
    
    def get_authentication_statistics(self) -> Dict[str, Any]:
        """
        Get authentication statistics.
        
        Returns:
            Dictionary with authentication statistics
        """
        # Get login events
        login_attempts = self.audit_log_repository.find_login_attempts()
        successful_logins = [log for log in login_attempts if log.success]
        failed_logins = [log for log in login_attempts if not log.success]
        
        # Get token statistics
        token_stats = self.token_repository.get_token_stats()
        
        # Get locked accounts
        locked_accounts = self.credentials_repository.find_locked_accounts()
        
        # Get accounts with failed attempts
        accounts_with_failures = self.credentials_repository.find_accounts_with_failed_attempts()
        
        return {
            "login_statistics": {
                "total_login_attempts": len(login_attempts),
                "successful_logins": len(successful_logins),
                "failed_logins": len(failed_logins),
                "success_rate": (len(successful_logins) / len(login_attempts) * 100) 
                              if login_attempts else 0
            },
            "token_statistics": token_stats,
            "security_statistics": {
                "locked_accounts": len(locked_accounts),
                "accounts_with_failed_attempts": len(accounts_with_failures)
            }
        }
    
    def _create_token_payload(self, user: User) -> Dict[str, Any]:
        """
        Create JWT token payload for user.
        
        Args:
            user: User entity
        
        Returns:
            Token payload dictionary
        """
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "employee_id": user.employee_id
        }
    
    def _generate_jwt_token(self, payload: Dict[str, Any]) -> str:
        """
        Generate JWT token from payload.
        
        Args:
            payload: Token payload
        
        Returns:
            JWT token string
        
        Note: This is a simplified implementation. In production, use proper JWT library.
        """
        import json
        import base64
        import hashlib
        
        # Simple JWT-like token for demo purposes
        header = {"alg": "HS256", "typ": "JWT"}
        
        # Encode header and payload
        header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        
        # Create signature (simplified)
        message = f"{header_encoded}.{payload_encoded}"
        signature = hashlib.sha256(f"{message}.secret_key".encode()).hexdigest()[:32]
        
        return f"{header_encoded}.{payload_encoded}.{signature}"
    
    def _log_authentication_event(
        self,
        user_id: Optional[str],
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log authentication event for audit purposes.
        
        Args:
            user_id: User ID
            success: Whether authentication was successful
            ip_address: IP address
            user_agent: User agent
            failure_reason: Reason for failure
            additional_data: Additional data to log
        """
        try:
            audit_log = SecurityAuditLog.create_login_log(
                user_id=user_id,
                success=success,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=failure_reason
            )
            
            # Add additional data if provided
            if additional_data:
                for key, value in additional_data.items():
                    audit_log.add_additional_data(key, value)
            
            self.audit_log_repository.save(audit_log)
        except Exception as e:
            logger.error(f"Failed to log authentication event: {str(e)}")
    
    def cleanup_expired_tokens(self) -> Dict[str, int]:
        """
        Clean up expired authentication tokens.
        
        Returns:
            Dictionary with cleanup statistics
        """
        logger.info("Starting cleanup of expired authentication tokens")
        
        expired_count = self.token_repository.cleanup_expired_tokens()
        
        logger.info(f"Cleaned up {expired_count} expired tokens")
        
        return {
            "expired_tokens_cleaned": expired_count
        }
