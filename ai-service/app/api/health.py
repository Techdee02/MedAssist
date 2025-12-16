"""
Health Check API Router
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from datetime import datetime
from typing import Dict, Any

from app.models.schemas import HealthCheckResponse
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Comprehensive health check endpoint
    
    Checks:
    - Service status
    - Groq API connectivity
    - Azure Document Intelligence availability
    - Azure Translator availability
    
    Returns:
        Dict with service health status
    """
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check Groq API
    try:
        if settings.groq_api_key and settings.use_llm:
            from groq import Groq
            client = Groq(api_key=settings.groq_api_key)
            # Quick ping test
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "ping"}],
                model=settings.model_name,
                max_tokens=5
            )
            health_status["components"]["groq_api"] = {
                "status": "healthy",
                "model": settings.model_name
            }
        else:
            health_status["components"]["groq_api"] = {
                "status": "disabled",
                "reason": "LLM disabled or no API key"
            }
    except Exception as e:
        logger.error(f"Groq API health check failed: {e}")
        health_status["components"]["groq_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Azure Document Intelligence
    try:
        if settings.azure_document_intelligence_endpoint and settings.azure_document_intelligence_key:
            health_status["components"]["azure_document_intelligence"] = {
                "status": "configured",
                "endpoint": settings.azure_document_intelligence_endpoint[:50] + "..."
            }
        else:
            health_status["components"]["azure_document_intelligence"] = {
                "status": "not_configured"
            }
    except Exception as e:
        logger.error(f"Azure Document Intelligence check failed: {e}")
        health_status["components"]["azure_document_intelligence"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check Azure Translator
    try:
        if settings.azure_translator_endpoint and settings.azure_translator_key:
            health_status["components"]["azure_translator"] = {
                "status": "configured",
                "endpoint": settings.azure_translator_endpoint[:50] + "...",
                "region": settings.azure_translator_region
            }
        else:
            health_status["components"]["azure_translator"] = {
                "status": "not_configured"
            }
    except Exception as e:
        logger.error(f"Azure Translator check failed: {e}")
        health_status["components"]["azure_translator"] = {
            "status": "error",
            "error": str(e)
        }
    
    return health_status
