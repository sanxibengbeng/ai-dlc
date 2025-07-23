"""
Base domain entity class providing common attributes and functionality.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional


class BaseEntity:
    """
    Base class for all domain entities providing common attributes and functionality.
    
    Attributes:
        id (str): Unique identifier for the entity (UUID4)
        created_at (datetime): When the entity was created (UTC)
        updated_at (datetime): When the entity was last updated (UTC)
    """
    
    def __init__(self, entity_id: Optional[str] = None):
        """
        Initialize base entity with common attributes.
        
        Args:
            entity_id: Optional UUID string. If not provided, a new UUID4 will be generated.
        """
        self.id: str = entity_id or str(uuid.uuid4())
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = datetime.now(timezone.utc)
    
    def __eq__(self, other) -> bool:
        """Check equality based on entity ID."""
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Generate hash based on entity ID."""
        return hash(self.id)
    
    def __repr__(self) -> str:
        """String representation of the entity."""
        return f"{self.__class__.__name__}(id='{self.id}')"
