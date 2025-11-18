from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    created_at: Optional[datetime] = None  # Make it optional
    
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class UserBase(BaseModel):
    """Base user model with common fields"""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")

class UserCreate(UserBase):
    """User creation request model"""
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 characters)")
    
    @field_validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()  # Store usernames in lowercase
    
    @field_validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        
        if not has_number:
            raise ValueError('Password must contain at least one number')
            
        return v

class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")
    
    @field_validator('username')
    def normalize_username(cls, v):
        """Normalize username to lowercase"""
        return v.lower().strip()

class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: int
    username: str
    email: str
    
class UserUpdate(BaseModel):
    """User update model (optional fields)"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None)
    
    @field_validator('username')
    def validate_username(cls, v):
        """Validate username format if provided"""
        if v is not None:
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
            return v.lower()
        return v

class PasswordChange(BaseModel):
    """Password change request model"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        
        if not has_number:
            raise ValueError('Password must contain at least one number')
            
        return v

class UserProfile(UserResponse):
    """Extended user profile model"""
    total_predictions: Optional[int] = Field(0, description="Total predictions made")
    total_points: Optional[int] = Field(0, description="Total points earned")
    groups_count: Optional[int] = Field(0, description="Number of groups joined")
    
# Error response models
class ErrorDetail(BaseModel):
    """Error detail model"""
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")

class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    detail: list[dict] = Field(..., description="List of validation errors")
    
class AuthErrorResponse(BaseModel):
    """Authentication error response model"""
    detail: str = Field(..., description="Authentication error message")