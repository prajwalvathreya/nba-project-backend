from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import logging

from app.models.user import (
    UserCreate, UserResponse, LoginRequest, LoginResponse, 
    UserProfile
)
from app.services.auth_services import AuthService
from app.auth import create_login_response, get_current_user
from app.database import DatabaseError

logger = logging.getLogger(__name__)

# Create router with prefix and tags - THIS IS THE KEY LINE
router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/register", 
             response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user account."""
    try:
        # Validate registration data
        is_valid, error_message = AuthService.validate_registration_data(user_data)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Create user
        new_user = AuthService.create_user(user_data)
        
        logger.info(f"User registered successfully: {new_user.username}")
        return new_user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"Registration failed for {user_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to system error"
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(login_data: LoginRequest) -> Dict[str, Any]:
    """
    Authenticate user and generate access token.
    
    Args:
        login_data (LoginRequest): User login credentials
        
    Returns:
        Dict: Login response with access token
        
    Raises:
        ValueError: If credentials are invalid
        DatabaseError: If database operation fails
    """
    try:
        # Authenticate user
        user_data = AuthService.authenticate_user(login_data)
        
        # CHECK IF AUTHENTICATION FAILED - This is the fix!
        if user_data is None:
            raise ValueError("Invalid username or password")
        
        # Create and return login response with JWT token
        return create_login_response(user_data)
        
    except ValueError:
        # Re-raise ValueError for invalid credentials
        raise
    except DatabaseError:
        # Re-raise DatabaseError
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise DatabaseError(f"Login failed: {str(e)}")

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user's profile with statistics."""
    try:
        # Get user information
        user = AuthService.get_user_by_id(current_user['user_id'])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user statistics
        stats = AuthService.get_user_stats(current_user['user_id'])
        
        # Create profile response
        profile = UserProfile(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            total_predictions=stats['total_predictions'],
            total_points=stats['total_points'],
            groups_count=stats['groups_count']
        )
        
        return profile
        
    except DatabaseError as e:
        logger.error(f"Failed to get user profile for {current_user['user_id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@router.get("/verify-token", response_model=UserResponse)
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Verify JWT token validity and return user information."""
    try:
        user = AuthService.get_user_by_id(current_user['user_id'])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token user not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except DatabaseError as e:
        logger.error(f"Token verification failed for user {current_user['user_id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed"
        )

@router.get("/health")
async def auth_health_check():
    """Health check for authentication system."""
    try:
        from app.auth import PasswordManager, TokenManager
        
        # Test password hashing
        test_password = "test123456"
        hashed = PasswordManager.hash_password(test_password)
        password_valid = PasswordManager.verify_password(test_password, hashed)
        
        # Test JWT token creation
        test_user = {
            "user_id": 999,
            "username": "health_check",
            "email": "health@example.com"
        }
        
        test_token = TokenManager.create_access_token(test_user)
        token_data = TokenManager.verify_token(test_token)
        token_valid = token_data['user_id'] == test_user['user_id']
        
        return {
            "status": "healthy",
            "password_hashing": password_valid,
            "jwt_tokens": token_valid,
            "message": "Authentication system is working properly"
        }
        
    except Exception as e:
        logger.error(f"Authentication health check failed: {e}")
        return {
            "status": "unhealthy", 
            "error": str(e),
            "message": "Authentication system has issues"
        }