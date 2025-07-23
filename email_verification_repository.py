"""
EmailVerificationRepository for the User Management domain model.
"""

from typing import List, Optional
from datetime import datetime, timezone

from base_repository import InMemoryRepository
from email_verification import EmailVerification


class EmailVerificationRepository(InMemoryRepository[EmailVerification]):
    """
    Repository for EmailVerification entities with domain-specific query methods.
    
    Provides methods for finding verifications by user ID, token, email, and status.
    Supports managing email verification lifecycle.
    """
    
    def find_by_user_id(self, user_id: str) -> List[EmailVerification]:
        """
        Find all email verifications for a user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            List of email verifications for the user
        """
        if not user_id:
            return []
        
        return self.find_by_attribute('user_id', user_id.strip())
    
    def find_by_verification_token(self, token: str) -> Optional[EmailVerification]:
        """
        Find email verification by token.
        
        Args:
            token: Verification token to search for
        
        Returns:
            EmailVerification if found, None otherwise
        """
        if not token:
            return None
        
        return self.find_first_by_attribute('verification_token', token.strip())
    
    def find_by_email(self, email: str) -> List[EmailVerification]:
        """
        Find all email verifications for an email address.
        
        Args:
            email: Email address to search for
        
        Returns:
            List of email verifications for the email
        """
        if not email:
            return []
        
        email_lower = email.lower().strip()
        return self.find_by_attribute('email', email_lower)
    
    def find_latest_by_user_id(self, user_id: str) -> Optional[EmailVerification]:
        """
        Find the latest email verification for a user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            Latest EmailVerification if found, None otherwise
        """
        verifications = self.find_by_user_id(user_id)
        if not verifications:
            return None
        
        # Sort by created_at descending and return the first (latest)
        return max(verifications, key=lambda v: v.created_at)
    
    def find_verified_by_user_id(self, user_id: str) -> List[EmailVerification]:
        """
        Find all verified email verifications for a user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            List of verified email verifications
        """
        verifications = self.find_by_user_id(user_id)
        return [v for v in verifications if v.is_verified]
    
    def find_pending_by_user_id(self, user_id: str) -> List[EmailVerification]:
        """
        Find all pending (unverified) email verifications for a user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            List of pending email verifications
        """
        verifications = self.find_by_user_id(user_id)
        return [v for v in verifications if not v.is_verified]
    
    def find_expired_verifications(self) -> List[EmailVerification]:
        """
        Find all expired email verifications.
        
        Returns:
            List of expired email verifications
        """
        expired = []
        for verification in self.find_all():
            if verification.is_expired() and not verification.is_verified:
                expired.append(verification)
        return expired
    
    def find_active_verifications(self) -> List[EmailVerification]:
        """
        Find all active (not expired, not verified) email verifications.
        
        Returns:
            List of active email verifications
        """
        active = []
        for verification in self.find_all():
            if verification.is_token_valid():
                active.append(verification)
        return active
    
    def find_verifications_by_resend_count(self, min_count: int) -> List[EmailVerification]:
        """
        Find verifications with resend count >= specified minimum.
        
        Args:
            min_count: Minimum resend count
        
        Returns:
            List of verifications with high resend count
        """
        results = []
        for verification in self.find_all():
            if verification.resend_count >= min_count:
                results.append(verification)
        return results
    
    def is_email_verified_for_user(self, user_id: str, email: str) -> bool:
        """
        Check if a specific email is verified for a user.
        
        Args:
            user_id: User ID
            email: Email address
        
        Returns:
            True if email is verified for the user, False otherwise
        """
        if not user_id or not email:
            return False
        
        email_lower = email.lower().strip()
        verifications = self.find_by_multiple_attributes(
            user_id=user_id.strip(),
            email=email_lower,
            is_verified=True
        )
        return len(verifications) > 0
    
    def has_pending_verification(self, user_id: str, email: str) -> bool:
        """
        Check if there's a pending verification for user and email.
        
        Args:
            user_id: User ID
            email: Email address
        
        Returns:
            True if there's a pending verification, False otherwise
        """
        if not user_id or not email:
            return False
        
        email_lower = email.lower().strip()
        verifications = self.find_by_multiple_attributes(
            user_id=user_id.strip(),
            email=email_lower,
            is_verified=False
        )
        
        # Check if any are still valid (not expired)
        for verification in verifications:
            if verification.is_token_valid():
                return True
        
        return False
    
    def cleanup_expired_verifications(self) -> int:
        """
        Remove expired email verifications from storage.
        
        Returns:
            Number of expired verifications removed
        """
        expired = self.find_expired_verifications()
        count = 0
        
        for verification in expired:
            if self.delete_by_id(verification.id):
                count += 1
        
        return count
    
    def get_verification_stats(self) -> dict:
        """
        Get statistics about email verifications.
        
        Returns:
            Dictionary with verification statistics
        """
        all_verifications = self.find_all()
        verified_count = 0
        pending_count = 0
        expired_count = 0
        high_resend_count = 0
        
        for verification in all_verifications:
            if verification.is_verified:
                verified_count += 1
            elif verification.is_expired():
                expired_count += 1
            else:
                pending_count += 1
            
            if verification.resend_count >= 2:  # High resend threshold
                high_resend_count += 1
        
        return {
            "total_verifications": len(all_verifications),
            "verified": verified_count,
            "pending": pending_count,
            "expired": expired_count,
            "high_resend_count": high_resend_count
        }
    
    def delete_by_user_id(self, user_id: str) -> int:
        """
        Delete all email verifications for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of verifications deleted
        """
        verifications = self.find_by_user_id(user_id)
        count = 0
        
        for verification in verifications:
            if self.delete_by_id(verification.id):
                count += 1
        
        return count
    
    def find_recent_verifications(self, hours: int = 24) -> List[EmailVerification]:
        """
        Find verifications created within the specified hours.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of recent verifications
        """
        cutoff_time = datetime.now(timezone.utc) - timezone.utc.localize(
            datetime.now()
        ).replace(tzinfo=None).timedelta(hours=hours)
        
        recent = []
        for verification in self.find_all():
            if verification.created_at >= cutoff_time:
                recent.append(verification)
        
        return recent
