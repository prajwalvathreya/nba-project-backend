from typing import Optional, Dict, Any
import logging
from datetime import datetime, timezone

from app.database import call_procedure, DatabaseError
from app.auth import PasswordManager, TokenManager, create_login_response
from app.models.user import UserCreate, UserResponse, LoginRequest, LoginResponse, TokenData

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service with business logic for user management"""
    
    @staticmethod
    def create_user(user_data: UserCreate) -> UserResponse:
        """
        Create a new user account.
        
        Args:
            user_data (UserCreate): User registration data
            
        Returns:
            UserResponse: Created user information
            
        Raises:
            DatabaseError: If user creation fails
            ValueError: If user already exists
        """
        try:
            # Hash the password
            hashed_password = PasswordManager.hash_password(user_data.password)
            
            # Call stored procedure to create user
            # We'll need to create this procedure in procedures.sql
            result = call_procedure('create_user', [
                user_data.username,
                user_data.email,
                hashed_password
            ])
            
            if result and len(result) > 0:
                user = result[0]
                logger.info(f"User created successfully: {user_data.username}")
                
                return UserResponse(
                    user_id=user['user_id'],
                    username=user['username'],
                    email=user['email'],
                    created_at=user['created_at']
                )
            else:
                raise DatabaseError("User creation returned no data")
                
        except DatabaseError as e:
            # Check if it's a duplicate user error (we'll define error codes in procedure)
            if "[3001]" in str(e):  # Username already exists
                raise ValueError("Username already exists")
            elif "[3002]" in str(e):  # Email already exists
                raise ValueError("Email already exists")
            else:
                logger.error(f"User creation failed for {user_data.username}: {e}")
                raise DatabaseError(f"Failed to create user: {e}")
    
    @staticmethod
    def authenticate_user(login_data: LoginRequest) -> Optional[Dict[str, Any]]:
        """
        Authenticate user credentials and return user data.
        
        Args:
            login_data (LoginRequest): Login credentials
            
        Returns:
            Optional[Dict]: User data if authentication successful, None otherwise
        """
        try:
            # Get user by username or email
            # We'll need to create this procedure in procedures.sql
            result = call_procedure('get_user_for_login', [login_data.username])
            
            if not result or len(result) == 0:
                logger.warning(f"Login attempt for non-existent user: {login_data.username}")
                return None
            
            user = result[0]

            # Verify password
            if not PasswordManager.verify_password(login_data.password, user['password']):
                logger.warning(f"Invalid password for user: {login_data.username}")
                return None
            
            logger.info(f"User authenticated successfully: {user['username']}")
            
            # Return user data (without password)
            return {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at']
            }
            
        except DatabaseError as e:
            logger.error(f"Authentication failed for {login_data.username}: {e}")
            return None
    
    @staticmethod
    def login_user(login_data: LoginRequest) -> LoginResponse:
        """
        Complete login process with JWT token creation.
        
        Args:
            login_data (LoginRequest): Login credentials
            
        Returns:
            LoginResponse: Login response with JWT token
            
        Raises:
            ValueError: If authentication fails
        """
        # Authenticate user
        user_data = AuthService.authenticate_user(login_data)
        
        if not user_data:
            raise ValueError("Invalid credentials")
        
        # Create login response with JWT token
        login_response_data = create_login_response(user_data)
        
        return LoginResponse(**login_response_data)
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[UserResponse]:
        """
        Get user information by user ID.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Optional[UserResponse]: User data or None if not found
        """
        try:
            result = call_procedure('get_user_by_id', [user_id])
            
            if not result or len(result) == 0:
                return None
            
            user = result[0]
            
            return UserResponse(
                user_id=user['user_id'],
                username=user['username'],
                email=user['email'],
                created_at=user['created_at']
            )
            
        except DatabaseError as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[UserResponse]:
        """
        Get user information by username.
        
        Args:
            username (str): Username
            
        Returns:
            Optional[UserResponse]: User data or None if not found
        """
        try:
            result = call_procedure('get_user_by_username', [username.lower()])
            
            if not result or len(result) == 0:
                return None
            
            user = result[0]
            
            return UserResponse(
                user_id=user['user_id'],
                username=user['username'],
                email=user['email'],
                created_at=user['created_at']
            )
            
        except DatabaseError as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None
    
    @staticmethod
    def check_username_exists(username: str) -> bool:
        """
        Check if a username already exists.
        
        Args:
            username (str): Username to check
            
        Returns:
            bool: True if username exists, False otherwise
        """
        try:
            result = call_procedure('check_username_exists', [username.lower()])
            
            if result and len(result) > 0:
                return result[0]['exists'] > 0
            
            return False
            
        except DatabaseError as e:
            logger.error(f"Failed to check username existence {username}: {e}")
            return False
    
    @staticmethod
    def check_email_exists(email: str) -> bool:
        """
        Check if an email already exists.
        
        Args:
            email (str): Email to check
            
        Returns:
            bool: True if email exists, False otherwise
        """
        try:
            result = call_procedure('check_email_exists', [email.lower()])
            
            if result and len(result) > 0:
                return result[0]['exists'] > 0
            
            return False
            
        except DatabaseError as e:
            logger.error(f"Failed to check email existence {email}: {e}")
            return False
    
    @staticmethod
    def validate_registration_data(user_data: UserCreate) -> tuple[bool, str]:
        """
        Validate user registration data against existing users.
        
        Args:
            user_data (UserCreate): User registration data
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Check if username exists
            if AuthService.check_username_exists(user_data.username):
                return False, "Username already exists"
            
            # Check if email exists
            if AuthService.check_email_exists(user_data.email):
                return False, "Email already exists"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Registration validation failed: {e}")
            return False, "Validation failed due to system error"
    
    @staticmethod
    def get_user_stats(user_id: int) -> Dict[str, Any]:
        """
        Get user statistics for dashboard/profile.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Dict: User statistics
        """
        try:
            result = call_procedure('get_user_stats', [user_id])
            
            if result and len(result) > 0:
                stats = result[0]
                return {
                    'total_predictions': stats.get('total_predictions', 0),
                    'total_points': stats.get('total_points', 0),
                    'groups_count': stats.get('groups_count', 0),
                    'accuracy_percentage': stats.get('accuracy_percentage', 0.0)
                }
            
            # Return default stats if no data
            return {
                'total_predictions': 0,
                'total_points': 0,
                'groups_count': 0,
                'accuracy_percentage': 0.0
            }
            
        except DatabaseError as e:
            logger.error(f"Failed to get user stats for user {user_id}: {e}")
            return {
                'total_predictions': 0,
                'total_points': 0,
                'groups_count': 0,
                'accuracy_percentage': 0.0
            }

class AuthValidationService:
    """Validation utilities for authentication"""
    
    @staticmethod
    def validate_token_user(token_data: TokenData) -> bool:
        """
        Validate that a token's user data is still valid.
        
        Args:
            token_data (TokenData): Token payload data
            
        Returns:
            bool: True if user is valid, False otherwise
        """
        try:
            # Check if user still exists and is active
            user = AuthService.get_user_by_id(token_data.user_id)
            
            if not user:
                logger.warning(f"Token validation failed - user not found: {token_data.user_id}")
                return False
            
            # Verify token data matches current user data
            if user.username != token_data.username or user.email != token_data.email:
                logger.warning(f"Token validation failed - user data mismatch: {token_data.user_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False

# Export service classes
__all__ = [
    'AuthService',
    'AuthValidationService']