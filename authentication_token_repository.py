"""
AuthenticationTokenRepository for the User Management domain model.
"""

from typing import List, Optional
from datetime import datetime, timezone

from base_repository import InMemoryRepository
from authentication_token import AuthenticationToken
from enums import TokenType


class AuthenticationTokenRepository(InMemoryRepository[AuthenticationToken]):
    """
    Repository for AuthenticationToken entities with domain-specific query methods.
    
    Provides methods for finding tokens by user ID, hash, type, and status.
    Supports token lifecycle management and security operations.
    """
    
    def find_by_user_id(self, user_id: str) -> List[AuthenticationToken]:
        """
        Find all authentication tokens for a user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            List of authentication tokens for the user
        """
        if not user_id:
            return []
        
        return self.find_by_attribute('user_id', user_id.strip())
    
    def find_by_token_hash(self, token_hash: str) -> Optional[AuthenticationToken]:
        """
        Find authentication token by token hash.
        
        Args:
            token_hash: Token hash to search for
        
        Returns:
            AuthenticationToken if found, None otherwise
        """
        if not token_hash:
            return None
        
        return self.find_first_by_attribute('token_hash', token_hash.strip())
    
    def find_by_user_and_type(self, user_id: str, token_type: TokenType) -> List[AuthenticationToken]:
        """
        Find tokens by user ID and token type.
        
        Args:
            user_id: User ID
            token_type: Token type
        
        Returns:
            List of tokens matching the criteria
        """
        if not user_id:
            return []
        
        return self.find_by_multiple_attributes(
            user_id=user_id.strip(),
            token_type=token_type
        )
    
    def find_valid_tokens_by_user(self, user_id: str) -> List[AuthenticationToken]:
        """
        Find all valid (not revoked, not expired) tokens for a user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            List of valid tokens for the user
        """
        tokens = self.find_by_user_id(user_id)
        return [token for token in tokens if token.is_valid()]
    
    def find_expired_tokens(self) -> List[AuthenticationToken]:
        """
        Find all expired tokens.
        
        Returns:
            List of expired tokens
        """
        expired = []
        for token in self.find_all():
            if token.is_expired() and not token.is_revoked:
                expired.append(token)
        return expired
    
    def find_revoked_tokens(self) -> List[AuthenticationToken]:
        """
        Find all revoked tokens.
        
        Returns:
            List of revoked tokens
        """
        return self.find_by_attribute('is_revoked', True)
    
    def find_active_tokens(self) -> List[AuthenticationToken]:
        """
        Find all active (valid, not revoked, not expired) tokens.
        
        Returns:
            List of active tokens
        """
        active = []
        for token in self.find_all():
            if token.is_valid():
                active.append(token)
        return active
    
    def find_tokens_by_type(self, token_type: TokenType) -> List[AuthenticationToken]:
        """
        Find all tokens of a specific type.
        
        Args:
            token_type: Token type to search for
        
        Returns:
            List of tokens of the specified type
        """
        return self.find_by_attribute('token_type', token_type)
    
    def find_tokens_by_ip_address(self, ip_address: str) -> List[AuthenticationToken]:
        """
        Find tokens by IP address.
        
        Args:
            ip_address: IP address to search for
        
        Returns:
            List of tokens from the IP address
        """
        if not ip_address:
            return []
        
        return self.find_by_attribute('ip_address', ip_address.strip())
    
    def revoke_user_tokens(self, user_id: str, reason: str = "User logout") -> int:
        """
        Revoke all active tokens for a user.
        
        Args:
            user_id: User ID
            reason: Reason for revocation
        
        Returns:
            Number of tokens revoked
        """
        active_tokens = self.find_valid_tokens_by_user(user_id)
        count = 0
        
        for token in active_tokens:
            token.revoke(reason)
            self.save(token)
            count += 1
        
        return count
    
    def revoke_tokens_by_type(self, user_id: str, token_type: TokenType, reason: str = "Token type revocation") -> int:
        """
        Revoke all tokens of a specific type for a user.
        
        Args:
            user_id: User ID
            token_type: Token type to revoke
            reason: Reason for revocation
        
        Returns:
            Number of tokens revoked
        """
        tokens = self.find_by_user_and_type(user_id, token_type)
        count = 0
        
        for token in tokens:
            if token.is_valid():
                token.revoke(reason)
                self.save(token)
                count += 1
        
        return count
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from storage.
        
        Returns:
            Number of expired tokens removed
        """
        expired = self.find_expired_tokens()
        count = 0
        
        for token in expired:
            if self.delete_by_id(token.id):
                count += 1
        
        return count
    
    def cleanup_revoked_tokens(self, older_than_days: int = 30) -> int:
        """
        Remove revoked tokens older than specified days.
        
        Args:
            older_than_days: Number of days to keep revoked tokens
        
        Returns:
            Number of revoked tokens removed
        """
        cutoff_date = datetime.now(timezone.utc) - timezone.utc.localize(
            datetime.now()
        ).replace(tzinfo=None).timedelta(days=older_than_days)
        
        revoked_tokens = self.find_revoked_tokens()
        count = 0
        
        for token in revoked_tokens:
            if token.revoked_at and token.revoked_at < cutoff_date:
                if self.delete_by_id(token.id):
                    count += 1
        
        return count
    
    def get_token_stats(self) -> dict:
        """
        Get statistics about authentication tokens.
        
        Returns:
            Dictionary with token statistics
        """
        all_tokens = self.find_all()
        active_count = 0
        expired_count = 0
        revoked_count = 0
        access_count = 0
        refresh_count = 0
        
        for token in all_tokens:
            if token.is_revoked:
                revoked_count += 1
            elif token.is_expired():
                expired_count += 1
            else:
                active_count += 1
            
            if token.token_type == TokenType.ACCESS:
                access_count += 1
            elif token.token_type == TokenType.REFRESH:
                refresh_count += 1
        
        return {
            "total_tokens": len(all_tokens),
            "active": active_count,
            "expired": expired_count,
            "revoked": revoked_count,
            "access_tokens": access_count,
            "refresh_tokens": refresh_count
        }
    
    def find_recent_tokens(self, hours: int = 24) -> List[AuthenticationToken]:
        """
        Find tokens created within the specified hours.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of recent tokens
        """
        cutoff_time = datetime.now(timezone.utc) - timezone.utc.localize(
            datetime.now()
        ).replace(tzinfo=None).timedelta(hours=hours)
        
        recent = []
        for token in self.find_all():
            if token.created_at >= cutoff_time:
                recent.append(token)
        
        return recent
    
    def find_tokens_expiring_soon(self, hours: int = 1) -> List[AuthenticationToken]:
        """
        Find tokens that will expire within the specified hours.
        
        Args:
            hours: Number of hours to look ahead
        
        Returns:
            List of tokens expiring soon
        """
        expiry_threshold = datetime.now(timezone.utc) + timezone.utc.localize(
            datetime.now()
        ).replace(tzinfo=None).timedelta(hours=hours)
        
        expiring_soon = []
        for token in self.find_all():
            if not token.is_revoked and not token.is_expired() and token.expires_at <= expiry_threshold:
                expiring_soon.append(token)
        
        return expiring_soon
    
    def delete_by_user_id(self, user_id: str) -> int:
        """
        Delete all tokens for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of tokens deleted
        """
        tokens = self.find_by_user_id(user_id)
        count = 0
        
        for token in tokens:
            if self.delete_by_id(token.id):
                count += 1
        
        return count
    
    def has_valid_token(self, user_id: str, token_type: Optional[TokenType] = None) -> bool:
        """
        Check if a user has any valid tokens.
        
        Args:
            user_id: User ID to check
            token_type: Optional token type to filter by
        
        Returns:
            True if user has valid tokens, False otherwise
        """
        if token_type:
            tokens = self.find_by_user_and_type(user_id, token_type)
        else:
            tokens = self.find_by_user_id(user_id)
        
        for token in tokens:
            if token.is_valid():
                return True
        
        return False
