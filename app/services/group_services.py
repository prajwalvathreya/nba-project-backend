from typing import List, Dict, Any, Optional
from app.database import call_procedure, DatabaseError
import logging

logger = logging.getLogger(__name__)

class GroupService:
    """Service layer for group-related operations"""
    
    @staticmethod
    def create_group(group_name: str, creator_id: int) -> Dict[str, Any]:
        """
        Create a new group.
        
        Args:
            group_name: Name of the group
            creator_id: User ID of the group creator
            
        Returns:
            Dict: Created group data
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = call_procedure('create_group', [group_name, creator_id])
            
            if not result:
                raise DatabaseError("Failed to create group")
            
            logger.info(f"Group '{group_name}' created by user {creator_id}")
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to create group: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating group: {e}")
            raise DatabaseError(f"Failed to create group: {str(e)}")
    
    @staticmethod
    def get_group_by_id(group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get group details by ID.
        
        Args:
            group_id: The group ID
            
        Returns:
            Dict: Group data or None if not found
        """
        try:
            result = call_procedure('get_group_by_id', [group_id])
            
            if not result:
                logger.info(f"Group {group_id} not found")
                return None
            
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch group {group_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching group {group_id}: {e}")
            raise DatabaseError(f"Failed to fetch group: {str(e)}")
    
    @staticmethod
    def get_group_by_code(group_code: str) -> Optional[Dict[str, Any]]:
        """
        Get group details by group code.
        
        Args:
            group_code: 6-character group code
            
        Returns:
            Dict: Group data or None if not found
        """
        try:
            # Make code uppercase for case-insensitive lookup
            group_code = group_code.upper()
            result = call_procedure('get_group_by_code', [group_code])
            
            if not result:
                logger.info(f"Group with code {group_code} not found")
                return None
            
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch group by code {group_code}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching group by code: {e}")
            raise DatabaseError(f"Failed to fetch group: {str(e)}")
    
    @staticmethod
    def get_user_groups(user_id: int) -> List[Dict[str, Any]]:
        """
        Get all groups for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List[Dict]: List of groups the user is a member of
        """
        try:
            result = call_procedure('get_user_groups', [user_id])
            
            if not result:
                logger.info(f"User {user_id} has no groups")
                return []
            
            logger.info(f"Found {len(result)} groups for user {user_id}")
            return result
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch groups for user {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching user groups: {e}")
            raise DatabaseError(f"Failed to fetch user groups: {str(e)}")
    
    @staticmethod
    def join_group(user_id: int, group_code: str) -> Dict[str, Any]:
        """
        Join a group by group code.
        
        Args:
            user_id: The user ID
            group_code: 6-character group code
            
        Returns:
            Dict: Group data after joining
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            # Make code uppercase for case-insensitive lookup
            group_code = group_code.upper()
            result = call_procedure('join_group', [user_id, group_code])
            
            if not result:
                raise DatabaseError("Failed to join group")
            
            logger.info(f"User {user_id} joined group with code {group_code}")
            return result[0]
            
        except DatabaseError as e:
            logger.error(f"Failed to join group: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error joining group: {e}")
            raise DatabaseError(f"Failed to join group: {str(e)}")
    
    @staticmethod
    def leave_group(user_id: int, group_id: int) -> int:
        """
        Leave a group.
        
        Args:
            user_id: The user ID
            group_id: The group ID
            
        Returns:
            int: Number of rows affected (should be 1)
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            result = call_procedure('leave_group', [user_id, group_id])
            
            if not result:
                raise DatabaseError("Failed to leave group")
            
            left_count = result[0]['left_group']
            logger.info(f"User {user_id} left group {group_id}")
            return left_count
            
        except DatabaseError as e:
            logger.error(f"Failed to leave group: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error leaving group: {e}")
            raise DatabaseError(f"Failed to leave group: {str(e)}")
    
    @staticmethod
    def get_group_members(group_id: int) -> List[Dict[str, Any]]:
        """
        Get all members of a group.
        
        Args:
            group_id: The group ID
            
        Returns:
            List[Dict]: List of group members
        """
        try:
            result = call_procedure('get_group_members', [group_id])
            
            if not result:
                logger.info(f"Group {group_id} has no members")
                return []
            
            logger.info(f"Found {len(result)} members in group {group_id}")
            return result
            
        except DatabaseError as e:
            logger.error(f"Failed to fetch members for group {group_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching group members: {e}")
            raise DatabaseError(f"Failed to fetch group members: {str(e)}")
    
    @staticmethod
    def delete_group(group_id: int, user_id: int) -> int:
        """
        Delete a group (only by creator).
        
        Args:
            group_id: The group ID
            user_id: The user ID (must be creator)
            
        Returns:
            int: Number of rows deleted (should be 1)
            
        Raises:
            DatabaseError: If operation fails
        """
        try:
            result = call_procedure('delete_group', [group_id, user_id])
            
            if not result:
                raise DatabaseError("Failed to delete group")
            
            deleted_count = result[0]['deleted_count']
            logger.info(f"Group {group_id} deleted by user {user_id}")
            return deleted_count
            
        except DatabaseError as e:
            logger.error(f"Failed to delete group: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting group: {e}")
            raise DatabaseError(f"Failed to delete group: {str(e)}")