import logging
import sys
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import enrich, classify
from app.database import engine

# Setup structured logging
logging.basicConfig(
    level=logging.INFO if settings.LOG_LEVEL.lower() == "info" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("==================================================")
    logger.info("Starting up AI Lead Automation System (Aviara Labs)")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Using Groq Model: {settings.GROQ_MODEL}")
    logger.info("Checking database connection...")
    
    # Try testing database engine
    try:
        async with engine.connect() as conn:
            logger.info("Successfully connected to the database!")
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        logger.warning("Application will continue running, but DB-dependent operations might fail.")
        
    logger.info("==================================================")
    yield
    # Shutdown tasks
    logger.info("Shutting down AI Lead Automation System...")
    await engine.dispose()
    logger.info("Database connection pool closed.")

app = FastAPI(
    title="AI Lead Automation System API",
    description="Backend services for lead enrichment and AI intent classification.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for n8n or external client requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred on the server.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )

# Include Routers
app.include_router(enrich.router)
app.include_router(classify.router)

# Health check route
@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["System Health"]
)
async def health_check():
    """
    Check API status and database availability.
    """
    db_status = "connected"
    try:
        async with engine.connect() as conn:
            pass
    except Exception:
        db_status = "disconnected"
        
    return {
        "status": "healthy",
        "database": db_status,
        "environment": settings.ENVIRONMENT
    }

# Root route
@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["System Health"]
)
async def index():
    return {
        "message": "Welcome to the AI Lead Automation System (Aviara Labs) API. Use /docs to view Swagger documentation."
    }
