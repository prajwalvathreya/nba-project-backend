from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class GroupCreate(BaseModel):
    """Request model for creating a new group"""
    group_name: str = Field(..., min_length=3, max_length=100, description="Name of the group")

class GroupJoin(BaseModel):
    """Request model for joining a group by code"""
    group_code: str = Field(..., min_length=6, max_length=6, description="6-character group code")

class GroupResponse(BaseModel):
    """Response model for group details"""
    group_id: int
    group_code: str
    group_name: str
    creator_id: int
    creation_date: datetime
    creator_username: Optional[str] = None
    member_count: Optional[int] = None
    is_creator: Optional[bool] = None
    joined_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class GroupMemberResponse(BaseModel):
    """Response model for group member details"""
    user_id: int
    username: str
    email: str
    joined_date: datetime
    is_creator: bool
    total_points: int = 0
    rank_position: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

class GroupLeaveResponse(BaseModel):
    """Response model for leaving a group"""
    message: str
    left_group: int

class GroupDeleteResponse(BaseModel):
    """Response model for deleting a group"""
    message: str
    deleted_count: int