"""
Translation API Router

Multi-language translation using Azure AI Translator
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import List, Optional
from pydantic import BaseModel, Field

from app.services.language_translator import get_language_translator

router = APIRouter(prefix="/api/v1/translate", tags=["translation"])


class TranslateRequest(BaseModel):
    """Translation request"""
    text: str = Field(..., description="Text to translate", min_length=1)
    target_language: str = Field(..., description="Target language code (e.g., 'yo', 'ha', 'ig', 'en')")
    source_language: Optional[str] = Field(None, description="Source language code (auto-detected if not provided)")


class TranslateResponse(BaseModel):
    """Translation response"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: Optional[float] = None


class BatchTranslateRequest(BaseModel):
    """Batch translation request"""
    texts: List[str] = Field(..., description="List of texts to translate")
    target_language: str
    source_language: Optional[str] = None


@router.post("", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """
    Translate text to target language
    
    Supports Nigerian languages:
    - Yoruba (yo)
    - Hausa (ha)
    - Igbo (ig)
    - English (en)
    - And 100+ other languages
    
    Args:
        request: TranslateRequest with text and target language
        
    Returns:
        TranslateResponse with translated text
    """
    logger.info(f"Translating text to {request.target_language}")
    
    try:
        translator = get_language_translator()
        
        result = translator.translate(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language
        )
        
        return TranslateResponse(
            original_text=request.text,
            translated_text=result["translated_text"],
            source_language=result.get("detected_language") or request.source_language or "auto",
            target_language=request.target_language,
            confidence=result.get("confidence")
        )
        
    except Exception as e:
        logger.error(f"Translation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/batch")
async def translate_batch(request: BatchTranslateRequest):
    """
    Translate multiple texts in a single request
    
    Args:
        request: BatchTranslateRequest with list of texts
        
    Returns:
        List of translations
    """
    logger.info(f"Batch translating {len(request.texts)} texts to {request.target_language}")
    
    if len(request.texts) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 texts per batch request"
        )
    
    try:
        translator = get_language_translator()
        
        results = translator.translate_batch(
            texts=request.texts,
            target_language=request.target_language,
            source_language=request.source_language
        )
        
        return {
            "translations": results,
            "count": len(results),
            "target_language": request.target_language
        }
        
    except Exception as e:
        logger.error(f"Batch translation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch translation failed: {str(e)}"
        )


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    
    Returns:
        Dict of language codes and names
    """
    translator = get_language_translator()
    
    try:
        languages = translator.get_supported_languages()
        
        # Highlight Nigerian languages
        nigerian_languages = {
            "yo": "Yoruba",
            "ha": "Hausa",
            "ig": "Igbo"
        }
        
        return {
            "nigerian_languages": nigerian_languages,
            "all_languages": languages,
            "total_count": len(languages)
        }
        
    except Exception as e:
        logger.error(f"Error fetching supported languages: {e}")
        # Return default Nigerian languages if API fails
        return {
            "nigerian_languages": {
                "yo": "Yoruba",
                "ha": "Hausa",
                "ig": "Igbo",
                "en": "English"
            },
            "note": "Full language list unavailable"
        }


class DetectLanguageRequest(BaseModel):
    """Language detection request"""
    text: str = Field(..., min_length=1, description="Text to analyze")


@router.post("/detect")
async def detect_language(request: DetectLanguageRequest):
    """
    Detect language of input text
    
    Args:
        request: DetectLanguageRequest with text
        
    Returns:
        Detected language code and confidence
    """
    logger.info(f"Detecting language for text: {request.text[:50]}...")
    
    try:
        translator = get_language_translator()
        
        result = translator.detect_language(request.text)
        
        return {
            "text": request.text[:100],  # Return first 100 chars
            "detected_language": result["language"],
            "confidence": result.get("confidence"),
            "alternatives": result.get("alternatives", [])
        }
        
    except Exception as e:
        logger.error(f"Language detection error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Language detection failed: {str(e)}"
        )
