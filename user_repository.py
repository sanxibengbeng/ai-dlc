"""
UserRepository for the User Management domain model.
"""

from typing import List, Optional

from base_repository import InMemoryRepository
from user import User
from enums import UserRole
from exceptions import DuplicateEntityException


class UserRepository(InMemoryRepository[User]):
    """
    Repository for User entities with domain-specific query methods.
    
    Provides methods for finding users by email, employee ID, role, and other criteria.
    Enforces uniqueness constraints for email and employee ID.
    """
    
    def save(self, user: User) -> User:
        """
        Save a user with uniqueness validation.
        
        Args:
            user: User to save
        
        Returns:
            Saved user
        
        Raises:
            DuplicateEntityException: If email or employee ID already exists
        """
        # Check for duplicate email (case-insensitive)
        existing_user_by_email = self.find_by_email(user.email)
        if existing_user_by_email and existing_user_by_email.id != user.id:
            raise DuplicateEntityException(f"User with email '{user.email}' already exists")
        
        # Check for duplicate employee ID
        existing_user_by_employee_id = self.find_by_employee_id(user.employee_id)
        if existing_user_by_employee_id and existing_user_by_employee_id.id != user.id:
            raise DuplicateEntityException(f"User with employee ID '{user.employee_id}' already exists")
        
        return super().save(user)
    
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by email address (case-insensitive).
        
        Args:
            email: Email address to search for
        
        Returns:
            User if found, None otherwise
        """
        if not email:
            return None
        
        email_lower = email.lower().strip()
        return self.find_first_by_attribute('email', email_lower)
    
    def find_by_employee_id(self, employee_id: str) -> Optional[User]:
        """
        Find a user by employee ID.
        
        Args:
            employee_id: Employee ID to search for
        
        Returns:
            User if found, None otherwise
        """
        if not employee_id:
            return None
        
        return self.find_first_by_attribute('employee_id', employee_id.strip())
    
    def find_by_role(self, role: UserRole) -> List[User]:
        """
        Find all users with a specific role.
        
        Args:
            role: User role to search for
        
        Returns:
            List of users with the specified role
        """
        return self.find_by_attribute('role', role)
    
    def find_active_users(self) -> List[User]:
        """
        Find all active users.
        
        Returns:
            List of active users
        """
        return self.find_by_attribute('is_active', True)
    
    def find_inactive_users(self) -> List[User]:
        """
        Find all inactive users.
        
        Returns:
            List of inactive users
        """
        return self.find_by_attribute('is_active', False)
    
    def find_by_department(self, department: str) -> List[User]:
        """
        Find all users in a specific department.
        
        Args:
            department: Department name to search for
        
        Returns:
            List of users in the specified department
        """
        if not department:
            return []
        
        return self.find_by_attribute('department', department.strip())
    
    def find_by_job_title(self, job_title: str) -> List[User]:
        """
        Find all users with a specific job title.
        
        Args:
            job_title: Job title to search for
        
        Returns:
            List of users with the specified job title
        """
        if not job_title:
            return []
        
        return self.find_by_attribute('job_title', job_title.strip())
    
    def find_by_role_and_department(self, role: UserRole, department: str) -> List[User]:
        """
        Find users by role and department.
        
        Args:
            role: User role
            department: Department name
        
        Returns:
            List of users matching both criteria
        """
        if not department:
            return []
        
        return self.find_by_multiple_attributes(role=role, department=department.strip())
    
    def find_active_users_by_role(self, role: UserRole) -> List[User]:
        """
        Find active users with a specific role.
        
        Args:
            role: User role to search for
        
        Returns:
            List of active users with the specified role
        """
        return self.find_by_multiple_attributes(role=role, is_active=True)
    
    def search_by_name(self, name_query: str) -> List[User]:
        """
        Search users by name (case-insensitive partial match).
        
        Args:
            name_query: Name query string
        
        Returns:
            List of users whose names contain the query string
        """
        if not name_query:
            return []
        
        query_lower = name_query.lower().strip()
        results = []
        
        for user in self.find_all():
            if query_lower in user.name.lower():
                results.append(user)
        
        return results
    
    def email_exists(self, email: str) -> bool:
        """
        Check if an email address is already registered.
        
        Args:
            email: Email address to check
        
        Returns:
            True if email exists, False otherwise
        """
        return self.find_by_email(email) is not None
    
    def employee_id_exists(self, employee_id: str) -> bool:
        """
        Check if an employee ID is already registered.
        
        Args:
            employee_id: Employee ID to check
        
        Returns:
            True if employee ID exists, False otherwise
        """
        return self.find_by_employee_id(employee_id) is not None
    
    def get_user_count_by_role(self, role: UserRole) -> int:
        """
        Get the count of users with a specific role.
        
        Args:
            role: User role
        
        Returns:
            Count of users with the specified role
        """
        return len(self.find_by_role(role))
    
    def get_active_user_count(self) -> int:
        """
        Get the count of active users.
        
        Returns:
            Count of active users
        """
        return len(self.find_active_users())
    
    def get_department_user_count(self, department: str) -> int:
        """
        Get the count of users in a specific department.
        
        Args:
            department: Department name
        
        Returns:
            Count of users in the specified department
        """
        return len(self.find_by_department(department))
    
    def get_all_departments(self) -> List[str]:
        """
        Get a list of all unique departments.
        
        Returns:
            List of unique department names
        """
        departments = set()
        for user in self.find_all():
            departments.add(user.department)
        return sorted(list(departments))
    
    def get_all_job_titles(self) -> List[str]:
        """
        Get a list of all unique job titles.
        
        Returns:
            List of unique job titles
        """
        job_titles = set()
        for user in self.find_all():
            job_titles.add(user.job_title)
        return sorted(list(job_titles))
