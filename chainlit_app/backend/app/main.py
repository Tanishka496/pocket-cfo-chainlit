"""
AI Pocket CFO - Transaction Management Module
FastAPI main application file.

This is the entry point for the transaction management API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routes import transactions
from app.utils.supabase_client import SupabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for application lifecycle events.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup event
    logger.info("Starting up Transaction Management API")
    try:
        # Initialize Supabase client
        client = SupabaseManager.get_client()
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise
    
    yield
    
    # Shutdown event
    logger.info("Shutting down Transaction Management API")
    SupabaseManager.reset()


# Initialize FastAPI application
app = FastAPI(
    title="AI Pocket CFO - Transaction Management",
    description="Full-featured transaction management module for small business financial tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
# Adjust origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(transactions.router)


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - API information.
    
    Returns:
        dict: API information and available endpoints
    """
    return {
        "success": True,
        "data": {
            "api_name": "AI Pocket CFO - Transaction Management",
            "version": "1.0.0",
            "description": "Full-featured transaction management module",
            "endpoints": {
                "transactions": {
                    "GET /transactions": "List all transactions (paginated, searchable, filterable)",
                    "GET /transactions/{id}": "Get single transaction",
                    "POST /transactions": "Create new transaction",
                    "PUT /transactions/{id}": "Update transaction",
                    "DELETE /transactions/{id}": "Delete transaction",
                    "GET /transactions/export/csv": "Export to CSV",
                    "GET /transactions/export/pdf": "Export to PDF with summary"
                }
            }
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    try:
        # Attempt to get Supabase client
        client = SupabaseManager.get_client()
        return {
            "success": True,
            "status": "healthy",
            "message": "API is running and database connection is available"
        }
    except Exception as e:
        return {
            "success": False,
            "status": "degraded",
            "message": f"Database connection issue: {str(e)}"
        }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        dict: Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "success": False,
        "message": "An unexpected error occurred",
        "error_code": "INTERNAL_SERVER_ERROR"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
