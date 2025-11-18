from fastapi import FastAPI
from fastapi.exceptions import ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# Import modules
from app.database import initialize_database_on_startup, test_database_connection, get_database_stats
from app.auth import initialize_auth_on_startup, get_token_info, auth_config
from app.routers import auth, fixtures, groups, predictions, leaderboard

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting NBA Prediction API...")
    
    try:
        # Initialize database
        initialize_database_on_startup()
        
        # Initialize authentication system
        initialize_auth_on_startup()
        
        logger.info("Application startup completed successfully!")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise RuntimeError(f"Failed to start application: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NBA Prediction API...")

# Create FastAPI application
app = FastAPI(
    title="NBA Basketball Prediction API",
    description="A FastAPI-based application for NBA game score predictions with group competitions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware (for frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(fixtures.router)
app.include_router(groups.router)
app.include_router(predictions.router) 
app.include_router(leaderboard.router)

@app.get("/")
async def root():
    """API welcome message"""
    return {
        "message": "Welcome to NBA Basketball Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Complete system health check"""
    try:
        # Check database health
        db_status = test_database_connection()
        db_stats = get_database_stats()
        
        # Check authentication system
        auth_info = get_token_info()
        
        # Overall health status
        is_healthy = (
            db_status.get('status') == 'connected' and
            auth_info.get('secret_configured', False)
        )
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "database": {
                "status": db_status.get('status', 'unknown'),
                "host": db_status.get('host', 'unknown'),
                "database": db_status.get('database', 'unknown'),
                "mysql_version": db_status.get('mysql_version', 'unknown'),
                "tables_count": db_status.get('tables_count', 0),
                "statistics": db_stats
            },
            "authentication": {
                "jwt_configured": auth_info.get('secret_configured', False),
                "algorithm": auth_info.get('algorithm', 'unknown'),
                "token_expire_hours": auth_info.get('expire_hours', 0)
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "System health check failed"
        }

@app.get("/info")
async def api_info():
    """Get detailed API information"""
    try:
        db_stats = get_database_stats()
        
        return {
            "api": {
                "name": "NBA Basketball Prediction API",
                "version": "1.0.0",
                "description": "FastAPI-based NBA score prediction platform"
            },
            "features": [
                "User authentication with JWT tokens",
                "Group-based predictions",
                "NBA fixture integration", 
                "Leaderboard rankings",
                "Real-time score updates"
            ],
            "statistics": db_stats,
            "endpoints": {
                "authentication": "/auth/*",
                "health": "/health",
                "docs": "/docs"
            }
        }
        
    except Exception as e:
        logger.error(f"API info failed: {e}")
        return {
            "error": "Failed to retrieve API information",
            "message": str(e)
        }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested endpoint was not found",
            "suggestion": "Check /docs for available endpoints"
        }
    )

@app.exception_handler(ResponseValidationError)
async def response_validation_error_handler(request, exc):
    """Handle response validation errors (our code returned wrong format)"""
    logger.error(f"Response validation error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle all other exceptions"""
    logger.error(f"Internal server error: {exc}")
    
    # Check if it has status_code and detail attributes
    if hasattr(exc, 'status_code') and hasattr(exc, 'detail'):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # Otherwise return generic 500
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )