"""
MedAssist AI Service - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from loguru import logger

from app.config import settings
from app.models.schemas import HealthCheckResponse

# Import API routers
from app.api import health, message, symptom, document, translate

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # TODO: Initialize AI models here
    # TODO: Connect to Redis
    # TODO: Connect to MongoDB
    
    logger.info("AI Service ready to accept requests")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Service...")
    # TODO: Cleanup resources


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered healthcare assistant for patient communication and clinical insights",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthCheckResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment
    )


# Register API routers
app.include_router(health.router)
app.include_router(message.router)
app.include_router(symptom.router)
app.include_router(document.router)
app.include_router(translate.router)

logger.info("API routers registered successfully")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
