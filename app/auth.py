import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# Security configuration
security = HTTPBearer()

class AuthConfig:
    """Authentication configuration from environment variables"""
    
    def __init__(self):
        # JWT Secret Key - Fetch from environment variable
        self.jwt_secret = os.getenv('JWT_SECRET')
        if not self.jwt_secret:
            raise ValueError(
                "JWT_SECRET environment variable not found. "
                "Please set a secure secret key for JWT token signing."
            )
        
        # JWT Configuration
        self.jwt_algorithm = 'HS256'
        self.jwt_expire_hours = int(os.getenv('JWT_EXPIRE_HOURS', 24))  # 24 hours default
        
        # Password hashing configuration
        self.bcrypt_rounds = int(os.getenv('BCRYPT_ROUNDS', 12))  # 12 rounds for good security

# Global auth configuration
auth_config = AuthConfig()

class AuthError(Exception):
    """Custom exception for authentication operations"""
    pass

class PasswordManager:
    """Password hashing and verification utilities"""
    
    @staticmethod
    def hash_password(plain_password: str) -> str:
        """
        Hash a plain text password using bcrypt.
        
        Args:
            plain_password (str): Plain text password
            
        Returns:
            str: Hashed password as string
            
        Raises:
            AuthError: If password hashing fails
        """
        try:
            # Convert string to bytes and hash
            password_bytes = plain_password.encode('utf-8')
            salt = bcrypt.gensalt(rounds=auth_config.bcrypt_rounds)
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Return as string for database storage
            return hashed.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise AuthError("Failed to hash password") from e
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed password.
        
        Args:
            plain_password (str): Plain text password to verify
            hashed_password (str): Stored hashed password
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            return bcrypt.checkpw(password_bytes, hashed_bytes)
            
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

class TokenManager:
    """JWT token creation and verification utilities"""
    
    @staticmethod
    def create_access_token(user_data: Dict[str, Any]) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user_data (dict): User information to encode in token
                            Should include: user_id, username, email
                            
        Returns:
            str: JWT access token
            
        Raises:
            AuthError: If token creation fails
        """
        try:
            # Calculate expiration time using timezone-aware datetime
            now = datetime.now(timezone.utc)
            expire = now + timedelta(hours=auth_config.jwt_expire_hours)
            
            # Create token payload
            payload = {
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'exp': expire,
                'iat': now,
                'type': 'access_token'
            }
            
            # Create and return token
            token = jwt.encode(
                payload, 
                auth_config.jwt_secret, 
                algorithm=auth_config.jwt_algorithm
            )
            
            logger.info(f"Access token created for user {user_data['username']}")
            return token
            
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise AuthError("Failed to create access token") from e
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT access token.
        
        Args:
            token (str): JWT token to verify
            
        Returns:
            dict: Decoded token payload with user information
            
        Raises:
            AuthError: If token is invalid or expired
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, 
                auth_config.jwt_secret, 
                algorithms=[auth_config.jwt_algorithm]
            )
            
            # Validate token type
            if payload.get('type') != 'access_token':
                raise AuthError("Invalid token type")
            
            logger.debug(f"Token verified for user {payload.get('username')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise AuthError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise AuthError("Token verification failed") from e
    
    @staticmethod
    def extract_user_from_token(token: str) -> Dict[str, Any]:
        """
        Extract user information from a valid JWT token.
        
        Args:
            token (str): JWT token
            
        Returns:
            dict: User information (user_id, username, email)
            
        Raises:
            AuthError: If token is invalid
        """
        payload = TokenManager.verify_token(token)
        
        return {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'email': payload.get('email')
        }

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user from JWT token.

    Usage:
        @app.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            return {"message": f"Hello {current_user['username']}"}

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        dict: Current user information

    Raises:
        HTTPException: 401 if authentication fails
    """
    try:
        # Extract token from Authorization header
        token = credentials.credentials
        
        # Verify token and extract user info
        user_info = TokenManager.extract_user_from_token(token)
        
        if not user_info or not user_info.get('user_id'):
            raise AuthError("Invalid user information in token")
        
        return user_info

    except AuthError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_login_response(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a standardized login response with access token.
    
    Args:
        user_data (dict): User information from database
                         Must include: user_id, username, email

    Returns:
        dict: Login response with access token and user info

    Usage:
        user = get_user_from_database(username, password)
        return create_login_response(user)
    """
    try:
        # Create access token
        access_token = TokenManager.create_access_token(user_data)
        
        # Return standardized response
        return {
            'access_token': access_token,
            'token_type': 'bearer',
            'expires_in': auth_config.jwt_expire_hours * 3600,  # Convert to seconds
            'user': {
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['email']
            }
        }

    except Exception as e:
        logger.error(f"Login response creation failed: {e}")
        raise AuthError("Failed to create login response") from e

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength according to application requirements.
    
    Args:
        password (str): Password to validate
        
    Returns:
        Tuple: (is_valid: bool, error_message: str)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters long"
    
    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)
    
    if not has_letter:
        return False, "Password must contain at least one letter"
    
    if not has_number:
        return False, "Password must contain at least one number"
    
    return True, ""

def get_token_info() -> Dict[str, Any]:
    """
    Get information about JWT token configuration.
    Useful for health checks and debugging.
    
    Returns:
        dict: Token configuration information
    """
    return {
        'algorithm': auth_config.jwt_algorithm,
        'expire_hours': auth_config.jwt_expire_hours,
        'bcrypt_rounds': auth_config.bcrypt_rounds,
        'secret_configured': bool(auth_config.jwt_secret)
    }

# Railway deployment helper
def initialize_auth_on_startup():
    """
    Initialize authentication system and validate configuration on startup.
    Call this in main.py when the FastAPI app starts.
    
    Raises:
        RuntimeError: If authentication setup is invalid
    """
    logger.info("Initializing authentication system...")
    
    try:
        # Test JWT secret is configured
        if not auth_config.jwt_secret:
            raise RuntimeError("JWT_SECRET environment variable not configured")
        
        # Test password hashing
        test_password = "test123"
        hashed = PasswordManager.hash_password(test_password)
        
        if not PasswordManager.verify_password(test_password, hashed):
            raise RuntimeError("Password hashing verification failed")
        
        # Test JWT token creation and verification
        test_user_data = {
            'user_id': 1,
            'username': 'test_user',
            'email': 'test@example.com'
        }

        test_token = TokenManager.create_access_token(test_user_data)
        verified_data = TokenManager.verify_token(test_token)

        if verified_data['user_id'] != test_user_data['user_id']:
            raise RuntimeError("JWT token verification failed")

        logger.info("Authentication system initialized successfully")
        logger.info(f"JWT expiration: {auth_config.jwt_expire_hours} hours")
        logger.info(f"Bcrypt rounds: {auth_config.bcrypt_rounds}")

    except Exception as e:
        logger.error(f"Authentication initialization failed: {e}")
        raise RuntimeError(f"Authentication setup failed: {e}")

# Export commonly used functions and classes
__all__ = [
    'PasswordManager',
    'TokenManager',
    'get_current_user',
    'create_login_response',
    'validate_password_strength',
    'get_token_info',
    'initialize_auth_on_startup',
    'AuthError'
]