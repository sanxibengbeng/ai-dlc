"""
Base repository interface for the User Management domain model.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic, Dict, Any

from base_entity import BaseEntity

# Generic type for entities
T = TypeVar('T', bound=BaseEntity)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository providing common CRUD operations for domain entities.
    
    This class defines the interface that all repositories must implement.
    Concrete implementations will provide in-memory storage.
    """
    
    def __init__(self):
        """Initialize the repository with in-memory storage."""
        self._storage: Dict[str, T] = {}
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Save an entity to the repository.
        
        Args:
            entity: Entity to save
        
        Returns:
            Saved entity
        """
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """
        Find an entity by its ID.
        
        Args:
            entity_id: ID of the entity to find
        
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[T]:
        """
        Find all entities in the repository.
        
        Returns:
            List of all entities
        """
        pass
    
    @abstractmethod
    def delete_by_id(self, entity_id: str) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: ID of the entity to delete
        
        Returns:
            True if entity was deleted, False if not found
        """
        pass
    
    @abstractmethod
    def exists_by_id(self, entity_id: str) -> bool:
        """
        Check if an entity exists by its ID.
        
        Args:
            entity_id: ID of the entity to check
        
        Returns:
            True if entity exists, False otherwise
        """
        pass
    
    def count(self) -> int:
        """
        Get the total count of entities in the repository.
        
        Returns:
            Total count of entities
        """
        return len(self._storage)
    
    def clear(self) -> None:
        """Clear all entities from the repository."""
        self._storage.clear()


class InMemoryRepository(BaseRepository[T]):
    """
    Concrete implementation of BaseRepository using in-memory storage.
    
    This implementation provides thread-safe operations for single-threaded applications.
    For multi-threaded applications, additional synchronization would be needed.
    """
    
    def save(self, entity: T) -> T:
        """
        Save an entity to in-memory storage.
        
        Args:
            entity: Entity to save
        
        Returns:
            Saved entity
        """
        if not isinstance(entity, BaseEntity):
            raise ValueError("Entity must be an instance of BaseEntity")
        
        # Update timestamp if entity already exists
        if entity.id in self._storage:
            entity.update_timestamp()
        
        self._storage[entity.id] = entity
        return entity
    
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """
        Find an entity by its ID.
        
        Args:
            entity_id: ID of the entity to find
        
        Returns:
            Entity if found, None otherwise
        """
        return self._storage.get(entity_id)
    
    def find_all(self) -> List[T]:
        """
        Find all entities in the repository.
        
        Returns:
            List of all entities
        """
        return list(self._storage.values())
    
    def delete_by_id(self, entity_id: str) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: ID of the entity to delete
        
        Returns:
            True if entity was deleted, False if not found
        """
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False
    
    def exists_by_id(self, entity_id: str) -> bool:
        """
        Check if an entity exists by its ID.
        
        Args:
            entity_id: ID of the entity to check
        
        Returns:
            True if entity exists, False otherwise
        """
        return entity_id in self._storage
    
    def find_by_attribute(self, attribute_name: str, value: Any) -> List[T]:
        """
        Find entities by a specific attribute value.
        
        Args:
            attribute_name: Name of the attribute to search by
            value: Value to search for
        
        Returns:
            List of entities matching the criteria
        """
        results = []
        for entity in self._storage.values():
            if hasattr(entity, attribute_name):
                if getattr(entity, attribute_name) == value:
                    results.append(entity)
        return results
    
    def find_first_by_attribute(self, attribute_name: str, value: Any) -> Optional[T]:
        """
        Find the first entity by a specific attribute value.
        
        Args:
            attribute_name: Name of the attribute to search by
            value: Value to search for
        
        Returns:
            First entity matching the criteria, or None if not found
        """
        for entity in self._storage.values():
            if hasattr(entity, attribute_name):
                if getattr(entity, attribute_name) == value:
                    return entity
        return None
    
    def find_by_multiple_attributes(self, **kwargs) -> List[T]:
        """
        Find entities by multiple attribute values.
        
        Args:
            **kwargs: Attribute name-value pairs to search by
        
        Returns:
            List of entities matching all criteria
        """
        results = []
        for entity in self._storage.values():
            match = True
            for attr_name, attr_value in kwargs.items():
                if not hasattr(entity, attr_name) or getattr(entity, attr_name) != attr_value:
                    match = False
                    break
            if match:
                results.append(entity)
        return results
    
    def update(self, entity: T) -> T:
        """
        Update an existing entity.
        
        Args:
            entity: Entity to update
        
        Returns:
            Updated entity
        
        Raises:
            ValueError: If entity doesn't exist
        """
        if not self.exists_by_id(entity.id):
            raise ValueError(f"Entity with ID {entity.id} does not exist")
        
        return self.save(entity)
