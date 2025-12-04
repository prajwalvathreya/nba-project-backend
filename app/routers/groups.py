from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.group import (
    GroupCreate, 
    GroupJoin, 
    GroupResponse, 
    GroupMemberResponse,
    GroupLeaveResponse,
    GroupDeleteResponse
)
from app.services.group_services import GroupService
from app.auth import get_current_user
from app.database import DatabaseError
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new group.
    
    - **group_name**: Name of the group (3-100 characters)
    
    The creator is automatically added as a member.
    Returns the created group with auto-generated group code.
    """
    try:
        group = GroupService.create_group(
            group_name=group_data.group_name,
            creator_id=current_user['user_id']
        )
        
        logger.info(f"Group created: {group['group_name']} by user {current_user['username']}")
        return group
        
    except DatabaseError as e:
        logger.error(f"Failed to create group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group"
        )


@router.post("/join", response_model=GroupResponse)
async def join_group(
    join_data: GroupJoin,
    current_user: dict = Depends(get_current_user)
):
    """
    Join a group using a group code.
    
    - **group_code**: 6-character group code (case-insensitive)
    
    Returns the group details after successfully joining.
    """
    try:
        group = GroupService.join_group(
            user_id=current_user['user_id'],
            group_code=join_data.group_code
        )
        
        logger.info(f"group returned: {group}")
        logger.info(f"User {current_user['username']} joined group {group.get('group_name')}")
        return group
        
    except DatabaseError as e:
        error_msg = str(e)
        
        # Handle specific errors from stored procedure
        if "Group not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found with that code"
            )
        elif "already a member" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already a member of this group"
            )
        else:
            logger.error(f"Failed to join group: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to join group"
            )


@router.get("/me", response_model=List[GroupResponse])
async def get_my_groups(current_user: dict = Depends(get_current_user)):
    """
    Get all groups that the current user is a member of.
    
    Returns list of groups with details including member count and creator info.
    """
    try:
        groups = GroupService.get_user_groups(current_user['user_id'])
        return groups
        
    except DatabaseError as e:
        logger.error(f"Failed to fetch user groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your groups"
        )


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get details of a specific group by ID.
    
    - **group_id**: The group's unique identifier
    
    Returns full group details including member count and creator info.
    """
    try:
        group = GroupService.get_group_by_id(group_id)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group {group_id} not found"
            )
        
        return group
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Failed to fetch group {group_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch group details"
        )


@router.get("/code/{group_code}", response_model=GroupResponse)
async def get_group_by_code(group_code: str):
    """
    Look up a group by its code (public endpoint for sharing).
    
    - **group_code**: 6-character group code (case-insensitive)
    
    Useful for sharing group links. Does not require authentication.
    """
    try:
        group = GroupService.get_group_by_code(group_code)
        
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found with that code"
            )
        
        return group
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Failed to fetch group by code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch group"
        )


@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all members of a group.
    
    - **group_id**: The group's unique identifier
    
    Returns list of members with their points and rank in the group.
    """
    try:
        members = GroupService.get_group_members(group_id)
        return members
        
    except DatabaseError as e:
        logger.error(f"Failed to fetch group members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch group members"
        )


@router.delete("/{group_id}/leave", response_model=GroupLeaveResponse)
async def leave_group(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Leave a group.
    
    - **group_id**: The group's unique identifier
    
    Group creators cannot leave their own group - they must delete it instead.
    """
    try:
        left_count = GroupService.leave_group(
            user_id=current_user['user_id'],
            group_id=group_id
        )
        
        logger.info(f"User {current_user['username']} left group {group_id}")
        return {
            "message": "Successfully left the group",
            "left_group": left_count
        }
        
    except DatabaseError as e:
        error_msg = str(e)
        
        # Handle specific errors from stored procedure
        if "creator cannot leave" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group creator cannot leave the group. Delete the group instead."
            )
        elif "not a member" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are not a member of this group"
            )
        else:
            logger.error(f"Failed to leave group: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to leave group"
            )


@router.delete("/{group_id}", response_model=GroupDeleteResponse)
async def delete_group(
    group_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a group (only by creator).
    
    - **group_id**: The group's unique identifier
    
    Only the group creator can delete the group.
    All members, predictions, and leaderboard data will be removed.
    """
    try:
        deleted_count = GroupService.delete_group(
            group_id=group_id,
            user_id=current_user['user_id']
        )
        
        logger.info(f"Group {group_id} deleted by user {current_user['username']}")
        return {
            "message": "Group successfully deleted",
            "deleted_count": deleted_count
        }
        
    except DatabaseError as e:
        error_msg = str(e)
        
        # Handle specific errors from stored procedure
        if "Group not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        elif "Only the group creator" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the group creator can delete the group"
            )
        else:
            logger.error(f"Failed to delete group: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete group"
            )