"""
PasswordResetRepository for the User Management domain model.
"""

from typing import List, Optional
from datetime import datetime, timezone

from base_repository import InMemoryRepository
from password_reset import PasswordReset


class PasswordResetRepository(InMemoryRepository[PasswordReset]):
    """
    Repository for PasswordReset entities with domain-specific query methods.
    
    Provides methods for finding password resets by user ID, token, and status.
    Supports managing password reset lifecycle and security.
    """
    
    def find_by_user_id(self, user_id: str) -> List[PasswordReset]:
        """
        Find all password resets for a user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            List of password resets for the user
        """
        if not user_id:
            return []
        
        return self.find_by_attribute('user_id', user_id.strip())
    
    def find_by_reset_token(self, token: str) -> Optional[PasswordReset]:
        """
        Find password reset by token.
        
        Args:
            token: Reset token to search for
        
        Returns:
            PasswordReset if found, None otherwise
        """
        if not token:
            return None
        
        return self.find_first_by_attribute('reset_token', token.strip())
    
    def find_latest_by_user_id(self, user_id: str) -> Optional[PasswordReset]:
        """
        Find the latest password reset for a user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            Latest PasswordReset if found, None otherwise
        """
        resets = self.find_by_user_id(user_id)
        if not resets:
            return None
        
        # Sort by created_at descending and return the first (latest)
        return max(resets, key=lambda r: r.created_at)
    
    def find_active_by_user_id(self, user_id: str) -> List[PasswordReset]:
        """
        Find all active (unused, not expired) password resets for a user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            List of active password resets
        """
        resets = self.find_by_user_id(user_id)
        return [r for r in resets if r.is_token_valid()]
    
    def find_used_resets(self) -> List[PasswordReset]:
        """
        Find all used password resets.
        
        Returns:
            List of used password resets
        """
        return self.find_by_attribute('is_used', True)
    
    def find_unused_resets(self) -> List[PasswordReset]:
        """
        Find all unused password resets.
        
        Returns:
            List of unused password resets
        """
        return self.find_by_attribute('is_used', False)
    
    def find_expired_resets(self) -> List[PasswordReset]:
        """
        Find all expired password resets.
        
        Returns:
            List of expired password resets
        """
        expired = []
        for reset in self.find_all():
            if reset.is_expired() and not reset.is_used:
                expired.append(reset)
        return expired
    
    def find_active_resets(self) -> List[PasswordReset]:
        """
        Find all active (not used, not expired) password resets.
        
        Returns:
            List of active password resets
        """
        active = []
        for reset in self.find_all():
            if reset.is_token_valid():
                active.append(reset)
        return active
    
    def find_by_ip_address(self, ip_address: str) -> List[PasswordReset]:
        """
        Find password resets by IP address.
        
        Args:
            ip_address: IP address to search for
        
        Returns:
            List of password resets from the IP address
        """
        if not ip_address:
            return []
        
        return self.find_by_attribute('ip_address', ip_address.strip())
    
    def has_active_reset(self, user_id: str) -> bool:
        """
        Check if a user has any active password reset requests.
        
        Args:
            user_id: User ID to check
        
        Returns:
            True if user has active reset requests, False otherwise
        """
        active_resets = self.find_active_by_user_id(user_id)
        return len(active_resets) > 0
    
    def invalidate_user_resets(self, user_id: str) -> int:
        """
        Invalidate all active password resets for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of resets invalidated
        """
        active_resets = self.find_active_by_user_id(user_id)
        count = 0
        
        for reset in active_resets:
            reset.invalidate()
            self.save(reset)
            count += 1
        
        return count
    
    def cleanup_expired_resets(self) -> int:
        """
        Remove expired password resets from storage.
        
        Returns:
            Number of expired resets removed
        """
        expired = self.find_expired_resets()
        count = 0
        
        for reset in expired:
            if self.delete_by_id(reset.id):
                count += 1
        
        return count
    
    def cleanup_used_resets(self, older_than_days: int = 30) -> int:
        """
        Remove used password resets older than specified days.
        
        Args:
            older_than_days: Number of days to keep used resets
        
        Returns:
            Number of used resets removed
        """
        cutoff_date = datetime.now(timezone.utc) - timezone.utc.localize(
            datetime.now()
        ).replace(tzinfo=None).timedelta(days=older_than_days)
        
        used_resets = self.find_used_resets()
        count = 0
        
        for reset in used_resets:
            if reset.used_at and reset.used_at < cutoff_date:
                if self.delete_by_id(reset.id):
                    count += 1
        
        return count
    
    def get_reset_stats(self) -> dict:
        """
        Get statistics about password resets.
        
        Returns:
            Dictionary with reset statistics
        """
        all_resets = self.find_all()
        used_count = 0
        active_count = 0
        expired_count = 0
        
        for reset in all_resets:
            if reset.is_used:
                used_count += 1
            elif reset.is_expired():
                expired_count += 1
            else:
                active_count += 1
        
        return {
            "total_resets": len(all_resets),
            "used": used_count,
            "active": active_count,
            "expired": expired_count
        }
    
    def find_recent_resets(self, hours: int = 24) -> List[PasswordReset]:
        """
        Find password resets created within the specified hours.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of recent password resets
        """
        cutoff_time = datetime.now(timezone.utc) - timezone.utc.localize(
            datetime.now()
        ).replace(tzinfo=None).timedelta(hours=hours)
        
        recent = []
        for reset in self.find_all():
            if reset.created_at >= cutoff_time:
                recent.append(reset)
        
        return recent
    
    def find_frequent_reset_users(self, min_count: int = 3, days: int = 7) -> List[str]:
        """
        Find users who have requested password resets frequently.
        
        Args:
            min_count: Minimum number of resets to be considered frequent
            days: Number of days to look back
        
        Returns:
            List of user IDs with frequent reset requests
        """
        cutoff_time = datetime.now(timezone.utc) - timezone.utc.localize(
            datetime.now()
        ).replace(tzinfo=None).timedelta(days=days)
        
        user_reset_counts = {}
        
        for reset in self.find_all():
            if reset.created_at >= cutoff_time:
                user_id = reset.user_id
                user_reset_counts[user_id] = user_reset_counts.get(user_id, 0) + 1
        
        frequent_users = []
        for user_id, count in user_reset_counts.items():
            if count >= min_count:
                frequent_users.append(user_id)
        
        return frequent_users
    
    def delete_by_user_id(self, user_id: str) -> int:
        """
        Delete all password resets for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of resets deleted
        """
        resets = self.find_by_user_id(user_id)
        count = 0
        
        for reset in resets:
            if self.delete_by_id(reset.id):
                count += 1
        
        return count
