import os
import pymysql
from pymysql.cursors import DictCursor
from typing import Optional
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class DatabaseConfig:
    """Database configuration from environment variables"""
    
    def __init__(self):
        # Fetch database connection parameters from environment variables
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME', 'nba_db')
        
        # Validate required environment variables
        if not self.user or not self.password:
            raise ValueError(
                "Database credentials not found. Please set DB_USER and DB_PASSWORD environment variables."
            )
    
    def get_connection_params(self) -> dict:
        """Get database connection parameters"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': 'utf8mb4',
            'cursorclass': DictCursor,
            'autocommit': False,
            'connect_timeout': 10,  # 10 seconds connection timeout
            'read_timeout': 30,     # 30 seconds read timeout
            'write_timeout': 30     # 30 seconds write timeout
        }

# Global database configuration
db_config = DatabaseConfig()

def get_database_connection():
    """
    Create a new database connection.
    
    Railway best practice: Create new connection per request
    rather than using connection pooling in serverless environments.
    
    Returns:
        pymysql.Connection: Database connection with DictCursor
        
    Raises:
        ConnectionError: If unable to connect to database
    """
    try:
        connection = pymysql.connect(**db_config.get_connection_params())
        logger.info("Database connection established successfully")
        return connection
        
    except pymysql.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise ConnectionError(f"Could not connect to database: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during database connection: {e}")
        raise ConnectionError(f"Database connection error: {e}")

@contextmanager
def get_db_cursor():
    """
    Context manager for database operations.
    Automatically handles connection creation and cleanup.
    
    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM User")
            result = cursor.fetchall()
            
    Yields:
        pymysql.cursors.DictCursor: Database cursor
        
    Raises:
        ConnectionError: If unable to establish database connection
    """
    connection = None
    cursor = None
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        yield cursor
        
        # Commit transaction if everything went well
        connection.commit()
        
    except Exception as e:
        if connection:
            connection.rollback()
            logger.error(f"Database operation failed, rolled back transaction: {e}")
        raise
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            logger.debug("Database connection closed")

def execute_stored_procedure(procedure_name: str, params: list = None) -> tuple:
    """
    Execute a stored procedure and return results.
    
    Args:
        procedure_name (str): Name of the stored procedure
        params (list, optional): List of parameters for the procedure
        
    Returns:
        tuple: (success: bool, result: any, error: str)
    """
    try:
        with get_db_cursor() as cursor:
            if params:
                cursor.callproc(procedure_name, params)
            else:
                cursor.callproc(procedure_name)
                
            result = cursor.fetchall()
            logger.info(f"Stored procedure '{procedure_name}' executed successfully")
            
            return True, result, None
            
    except Exception as e:
        error_msg = f"Failed to execute stored procedure '{procedure_name}': {e}"
        logger.error(error_msg)
        return False, None, error_msg

def call_procedure(procedure_name: str, params: list = None):
    """
    Simplified stored procedure call with automatic error handling.
    
    Args:
        procedure_name (str): Name of the stored procedure
        params (list, optional): List of parameters for the procedure
        
    Returns:
        List[dict]: Results from the stored procedure
        
    Raises:
        DatabaseError: If procedure execution fails
        
    Usage:
        # Simple call
        results = call_procedure('get_season_stats', ['2025-26'])
        
        # No parameters
        results = call_procedure('get_all_fixtures')
        
        # Multiple parameters
        results = call_procedure('submit_prediction', [user_id, group_id, fixture_id, home_score, away_score])
    """
    try:
        with get_db_cursor() as cursor:
            logger.debug(f"Calling procedure '{procedure_name}' with params: {params}")
            
            if params:
                cursor.callproc(procedure_name, params)
            else:
                cursor.callproc(procedure_name)
                
            result = cursor.fetchall()
            # Advance to the last result set if there are multiple
            while cursor.nextset():
                temp = cursor.fetchall()
                if temp:
                    result = temp
            logger.info(f"Procedure '{procedure_name}' executed successfully, returned {len(result)} rows")
            return result
            
    except pymysql.Error as e:
        # Handle SIGNAL SQLSTATE '45000' errors from stored procedures
        if len(e.args) >= 2:
            error_code = e.args[0]
            error_message = e.args[1]
            
            # Custom error codes from our stored procedures
            if 1000 <= error_code <= 5999:
                logger.error(f"Business logic error in '{procedure_name}': [{error_code}] {error_message}")
                raise DatabaseError(f"[{error_code}] {error_message}")
            else:
                logger.error(f"Database error in '{procedure_name}': [{error_code}] {error_message}")
                raise DatabaseError(f"Database error [{error_code}]: {error_message}")
        else:
            error_msg = f"Procedure '{procedure_name}' failed: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
            
    except Exception as e:
        error_msg = f"Procedure '{procedure_name}' failed with params {params}: {e}"
        logger.error(error_msg)
        raise DatabaseError(error_msg) from e

def test_database_connection() -> dict:
    """
    Test database connection and return status information.
    Useful for health checks and debugging.
    
    Returns:
        dict: Connection status and database information
    """
    try:
        # Use stored procedure instead of raw SQL
        result = call_procedure('test_database_connection')
        
        if result:
            connection_data = result[0]
            
            # Get table count using stored procedure
            health_data = call_procedure('get_database_health')
            health_info = health_data[0] if health_data else {}
            
            # Get existing tables using stored procedure
            tables_result = call_procedure('check_required_tables')
            table_names = [table['TABLE_NAME'] for table in tables_result]
            
            return {
                'status': health_info.get('status', 'connected'),
                'host': db_config.host,
                'database': connection_data.get('current_db', 'unknown'),
                'mysql_version': connection_data.get('version', 'unknown'),
                'tables_found': table_names,
                'tables_count': len(table_names)
            }
            
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'host': db_config.host,
            'database': db_config.database
        }

def check_required_tables() -> bool:
    """
    Check if all required tables exist in the database.
    Useful for validating database setup.
    
    Returns:
        bool: True if all required tables exist
    """
    required_tables = ['User', 'Group', 'UserGroups', 'Fixture', 'Prediction', 'Leaderboard']
    
    try:
        # Use stored procedure instead of raw SQL
        existing_tables_result = call_procedure('check_required_tables')
        existing_tables = {table['TABLE_NAME'] for table in existing_tables_result}
        
        missing_tables = set(required_tables) - existing_tables
        
        if missing_tables:
            logger.warning(f"Missing required tables: {missing_tables}")
            return False
            
        logger.info("All required tables found in database")
        return True
        
    except Exception as e:
        logger.error(f"Failed to check required tables: {e}")
        return False

def get_database_stats() -> Optional[dict]:
    """
    Get basic database statistics for monitoring.
    
    Returns:
        dict: Database statistics or None if failed
    """
    try:
        # Use stored procedure instead of raw SQL
        result = call_procedure('get_database_stats')
        
        if result:
            stats = result[0]
            return {
                'users': stats.get('users', 0),
                'groups': stats.get('groups', 0),
                'fixtures': stats.get('fixtures', 0),
                'predictions': stats.get('predictions', 0)
            }
            
        return None
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return None

# Railway deployment helper
def initialize_database_on_startup():
    """
    Initialize database connection and validate setup on application startup.
    Call this in main.py when the FastAPI app starts.
    
    Raises:
        RuntimeError: If database setup is invalid
    """
    logger.info("Initializing database connection...")
    
    # Test connection
    connection_status = test_database_connection()
    
    if connection_status['status'] != 'connected':
        raise RuntimeError(f"Database connection failed: {connection_status.get('error', 'Unknown error')}")
    
    # Check required tables
    if not check_required_tables():
        raise RuntimeError("Database setup incomplete - missing required tables")
    
    logger.info(f"Database initialized successfully - Found {connection_status['tables_count']} tables")
    logger.info(f"Connected to MySQL {connection_status['mysql_version']} at {connection_status['host']}")

# Export the commonly used functions
__all__ = [
    'get_database_connection',
    'get_db_cursor', 
    'test_database_connection',
    'execute_stored_procedure',
    'call_procedure',
    'check_required_tables',
    'get_database_stats',
    'initialize_database_on_startup',
    'DatabaseError'
]