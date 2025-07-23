"""
SecurityAuditLogRepository for the User Management domain model.
"""

from typing import List, Optional
from datetime import datetime, timezone

from base_repository import InMemoryRepository
from security_audit_log import SecurityAuditLog
from enums import SecurityEventType


class SecurityAuditLogRepository(InMemoryRepository[SecurityAuditLog]):
    """
    Repository for SecurityAuditLog entities with domain-specific query methods.
    
    Provides methods for finding audit logs by user, event type, success status, and time ranges.
    Supports security monitoring and compliance reporting.
    """
    
    def find_by_user_id(self, user_id: str) -> List[SecurityAuditLog]:
        """
        Find all audit logs for a specific user.
        
        Args:
            user_id: User ID to search for
        
        Returns:
            List of audit logs for the user
        """
        if not user_id:
            return []
        
        return self.find_by_attribute('user_id', user_id.strip())
    
    def find_by_event_type(self, event_type: SecurityEventType) -> List[SecurityAuditLog]:
        """
        Find all audit logs for a specific event type.
        
        Args:
            event_type: Event type to search for
        
        Returns:
            List of audit logs for the event type
        """
        return self.find_by_attribute('event_type', event_type)
    
    def find_successful_events(self) -> List[SecurityAuditLog]:
        """
        Find all successful security events.
        
        Returns:
            List of successful audit logs
        """
        return self.find_by_attribute('success', True)
    
    def find_failed_events(self) -> List[SecurityAuditLog]:
        """
        Find all failed security events.
        
        Returns:
            List of failed audit logs
        """
        return self.find_by_attribute('success', False)
    
    def find_by_ip_address(self, ip_address: str) -> List[SecurityAuditLog]:
        """
        Find audit logs by IP address.
        
        Args:
            ip_address: IP address to search for
        
        Returns:
            List of audit logs from the IP address
        """
        if not ip_address:
            return []
        
        return self.find_by_attribute('ip_address', ip_address.strip())
    
    def find_by_user_and_event_type(self, user_id: str, event_type: SecurityEventType) -> List[SecurityAuditLog]:
        """
        Find audit logs by user ID and event type.
        
        Args:
            user_id: User ID
            event_type: Event type
        
        Returns:
            List of audit logs matching the criteria
        """
        if not user_id:
            return []
        
        return self.find_by_multiple_attributes(
            user_id=user_id.strip(),
            event_type=event_type
        )
    
    def find_failed_events_by_user(self, user_id: str) -> List[SecurityAuditLog]:
        """
        Find all failed events for a specific user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of failed audit logs for the user
        """
        if not user_id:
            return []
        
        return self.find_by_multiple_attributes(
            user_id=user_id.strip(),
            success=False
        )
    
    def find_login_attempts(self, user_id: Optional[str] = None) -> List[SecurityAuditLog]:
        """
        Find all login attempts (both successful and failed).
        
        Args:
            user_id: Optional user ID to filter by
        
        Returns:
            List of login attempt audit logs
        """
        login_events = []
        
        # Find both success and failure login events
        success_logins = self.find_by_event_type(SecurityEventType.LOGIN_SUCCESS)
        failed_logins = self.find_by_event_type(SecurityEventType.LOGIN_FAILURE)
        
        login_events.extend(success_logins)
        login_events.extend(failed_logins)
        
        # Filter by user if specified
        if user_id:
            login_events = [log for log in login_events if log.user_id == user_id.strip()]
        
        # Sort by created_at descending
        return sorted(login_events, key=lambda log: log.created_at, reverse=True)
    
    def find_failed_login_attempts(self, user_id: Optional[str] = None) -> List[SecurityAuditLog]:
        """
        Find failed login attempts.
        
        Args:
            user_id: Optional user ID to filter by
        
        Returns:
            List of failed login attempt audit logs
        """
        failed_logins = self.find_by_event_type(SecurityEventType.LOGIN_FAILURE)
        
        if user_id:
            failed_logins = [log for log in failed_logins if log.user_id == user_id.strip()]
        
        return sorted(failed_logins, key=lambda log: log.created_at, reverse=True)
    
    def find_events_in_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        user_id: Optional[str] = None,
        event_type: Optional[SecurityEventType] = None
    ) -> List[SecurityAuditLog]:
        """
        Find audit logs within a specific time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            user_id: Optional user ID to filter by
            event_type: Optional event type to filter by
        
        Returns:
            List of audit logs within the time range
        """
        results = []
        
        for log in self.find_all():
            # Check time range
            if not (start_time <= log.created_at <= end_time):
                continue
            
            # Check user filter
            if user_id and log.user_id != user_id.strip():
                continue
            
            # Check event type filter
            if event_type and log.event_type != event_type:
                continue
            
            results.append(log)
        
        return sorted(results, key=lambda log: log.created_at, reverse=True)
    
    def find_recent_events(self, hours: int = 24, user_id: Optional[str] = None) -> List[SecurityAuditLog]:
        """
        Find recent audit logs within the specified hours.
        
        Args:
            hours: Number of hours to look back
            user_id: Optional user ID to filter by
        
        Returns:
            List of recent audit logs
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timezone.utc.localize(
            datetime.now()
        ).replace(tzinfo=None).timedelta(hours=hours)
        
        return self.find_events_in_time_range(start_time, end_time, user_id)
    
    def find_suspicious_activities(self, hours: int = 1) -> List[SecurityAuditLog]:
        """
        Find potentially suspicious activities (multiple failed attempts from same IP).
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of suspicious audit logs
        """
        recent_failed = self.find_recent_events(hours)
        failed_events = [log for log in recent_failed if not log.success]
        
        # Group by IP address and count failures
        ip_failure_counts = {}
        for log in failed_events:
            if log.ip_address:
                ip = log.ip_address
                if ip not in ip_failure_counts:
                    ip_failure_counts[ip] = []
                ip_failure_counts[ip].append(log)
        
        # Return logs from IPs with multiple failures
        suspicious = []
        for ip, logs in ip_failure_counts.items():
            if len(logs) >= 3:  # 3 or more failures from same IP
                suspicious.extend(logs)
        
        return sorted(suspicious, key=lambda log: log.created_at, reverse=True)
    
    def get_event_statistics(self, hours: int = 24) -> dict:
        """
        Get statistics about security events within the specified time period.
        
        Args:
            hours: Number of hours to analyze
        
        Returns:
            Dictionary with event statistics
        """
        recent_events = self.find_recent_events(hours)
        
        stats = {
            "total_events": len(recent_events),
            "successful_events": 0,
            "failed_events": 0,
            "event_types": {},
            "unique_users": set(),
            "unique_ips": set()
        }
        
        for log in recent_events:
            if log.success:
                stats["successful_events"] += 1
            else:
                stats["failed_events"] += 1
            
            # Count event types
            event_type = log.event_type.value
            stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
            
            # Track unique users and IPs
            if log.user_id:
                stats["unique_users"].add(log.user_id)
            if log.ip_address:
                stats["unique_ips"].add(log.ip_address)
        
        # Convert sets to counts
        stats["unique_users"] = len(stats["unique_users"])
        stats["unique_ips"] = len(stats["unique_ips"])
        
        return stats
    
    def get_user_activity_summary(self, user_id: str, hours: int = 24) -> dict:
        """
        Get activity summary for a specific user.
        
        Args:
            user_id: User ID
            hours: Number of hours to analyze
        
        Returns:
            Dictionary with user activity summary
        """
        user_events = self.find_recent_events(hours, user_id)
        
        summary = {
            "total_events": len(user_events),
            "successful_events": 0,
            "failed_events": 0,
            "event_types": {},
            "last_activity": None
        }
        
        for log in user_events:
            if log.success:
                summary["successful_events"] += 1
            else:
                summary["failed_events"] += 1
            
            # Count event types
            event_type = log.event_type.value
            summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1
            
            # Track last activity
            if summary["last_activity"] is None or log.created_at > summary["last_activity"]:
                summary["last_activity"] = log.created_at
        
        return summary
    
    def cleanup_old_logs(self, older_than_days: int = 90) -> int:
        """
        Remove audit logs older than specified days.
        
        Args:
            older_than_days: Number of days to keep logs
        
        Returns:
            Number of logs removed
        """
        cutoff_date = datetime.now(timezone.utc) - timezone.utc.localize(
            datetime.now()
        ).replace(tzinfo=None).timedelta(days=older_than_days)
        
        old_logs = []
        for log in self.find_all():
            if log.created_at < cutoff_date:
                old_logs.append(log)
        
        count = 0
        for log in old_logs:
            if self.delete_by_id(log.id):
                count += 1
        
        return count
    
    def delete_by_user_id(self, user_id: str) -> int:
        """
        Delete all audit logs for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of logs deleted
        """
        user_logs = self.find_by_user_id(user_id)
        count = 0
        
        for log in user_logs:
            if self.delete_by_id(log.id):
                count += 1
        
        return count
