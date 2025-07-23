"""
UserCredentialsRepository for the User Management domain model.
"""

from typing import List, Optional
from datetime import datetime, timezone

from base_repository import InMemoryRepository
from user_credentials import UserCredentials
from exceptions import DuplicateEntityException


class UserCredentialsRepository(InMemoryRepository[UserCredentials]):
    """
    Repository for UserCredentials entities with domain-specific query methods.
    
    Provides methods for finding credentials by user ID and managing account security.
    Enforces one-to-one relationship between User and UserCredentials.
    """
    
    def save(self, credentials: UserCredentials) -> UserCredentials:
        """
        Save user credentials with uniqueness validation.
        
        Args:
            credentials: UserCredentials to save
        
        Returns:
            Saved credentials
        
        Raises:
            DuplicateEntityException: If credentials for user already exist
        """
        # Check for duplicate user_id (one-to-one relationship)
        existing_credentials = self.find_by_user_id(credentials.user_id)
        if existing_credentials and existing_credentials.id != credentials.id:
            raise DuplicateEntityException(f"Credentials for user '{credentials.user_id}' already exist")
        
        return super().save(credentials)
    
    def find_by_user_id(self, user_id: str) -> Optional[UserCredentials]:
        """
        Find credentials by user ID.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            UserCredentials if found, None otherwise
        """
        if not user_id:
            return None
        
        return self.find_first_by_attribute('user_id', user_id.strip())
    
    def find_locked_accounts(self) -> List[UserCredentials]:
        """
        Find all currently locked accounts.
        
        Returns:
            List of credentials for locked accounts
        """
        locked_accounts = []
        for credentials in self.find_all():
            if credentials.is_account_locked():
                locked_accounts.append(credentials)
        return locked_accounts
    
    def find_accounts_with_failed_attempts(self, min_attempts: int = 1) -> List[UserCredentials]:
        """
        Find accounts with failed login attempts.
        
        Args:
            min_attempts: Minimum number of failed attempts to include
        
        Returns:
            List of credentials with failed attempts
        """
        results = []
        for credentials in self.find_all():
            if credentials.failed_login_attempts >= min_attempts:
                results.append(credentials)
        return results
    
    def find_accounts_requiring_password_change(self) -> List[UserCredentials]:
        """
        Find accounts that require password change.
        
        Returns:
            List of credentials requiring password change
        """
        return self.find_by_attribute('must_change_password', True)
    
    def find_accounts_by_password_age(self, days_old: int) -> List[UserCredentials]:
        """
        Find accounts where password is older than specified days.
        
        Args:
            days_old: Number of days to check against
        
        Returns:
            List of credentials with old passwords
        """
        cutoff_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timezone.utc.localize(datetime.now()).replace(tzinfo=None).timedelta(days=days_old)
        
        results = []
        for credentials in self.find_all():
            if credentials.password_last_changed < cutoff_date:
                results.append(credentials)
        return results
    
    def unlock_account(self, user_id: str) -> bool:
        """
        Unlock an account by user ID.
        
        Args:
            user_id: User ID of account to unlock
        
        Returns:
            True if account was unlocked, False if not found
        """
        credentials = self.find_by_user_id(user_id)
        if credentials:
            credentials.unlock_account()
            self.save(credentials)
            return True
        return False
    
    def force_password_change(self, user_id: str) -> bool:
        """
        Force password change for a user.
        
        Args:
            user_id: User ID to force password change for
        
        Returns:
            True if successful, False if user not found
        """
        credentials = self.find_by_user_id(user_id)
        if credentials:
            credentials.force_password_change()
            self.save(credentials)
            return True
        return False
    
    def get_locked_account_count(self) -> int:
        """
        Get the count of currently locked accounts.
        
        Returns:
            Count of locked accounts
        """
        return len(self.find_locked_accounts())
    
    def get_failed_attempts_count(self, min_attempts: int = 1) -> int:
        """
        Get the count of accounts with failed attempts.
        
        Args:
            min_attempts: Minimum number of failed attempts to count
        
        Returns:
            Count of accounts with failed attempts
        """
        return len(self.find_accounts_with_failed_attempts(min_attempts))
    
    def get_password_change_required_count(self) -> int:
        """
        Get the count of accounts requiring password change.
        
        Returns:
            Count of accounts requiring password change
        """
        return len(self.find_accounts_requiring_password_change())
    
    def delete_by_user_id(self, user_id: str) -> bool:
        """
        Delete credentials by user ID.
        
        Args:
            user_id: User ID of credentials to delete
        
        Returns:
            True if credentials were deleted, False if not found
        """
        credentials = self.find_by_user_id(user_id)
        if credentials:
            return self.delete_by_id(credentials.id)
        return False
    
    def user_has_credentials(self, user_id: str) -> bool:
        """
        Check if a user has credentials.
        
        Args:
            user_id: User ID to check
        
        Returns:
            True if user has credentials, False otherwise
        """
        return self.find_by_user_id(user_id) is not None
    
    def get_security_summary(self) -> dict:
        """
        Get a summary of security-related statistics.
        
        Returns:
            Dictionary with security statistics
        """
        all_credentials = self.find_all()
        locked_count = 0
        failed_attempts_count = 0
        password_change_required_count = 0
        
        for credentials in all_credentials:
            if credentials.is_account_locked():
                locked_count += 1
            if credentials.failed_login_attempts > 0:
                failed_attempts_count += 1
            if credentials.must_change_password:
                password_change_required_count += 1
        
        return {
            "total_accounts": len(all_credentials),
            "locked_accounts": locked_count,
            "accounts_with_failed_attempts": failed_attempts_count,
            "accounts_requiring_password_change": password_change_required_count
        }
