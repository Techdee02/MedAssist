"""
Document Extraction API Router

Upload and process medical documents using Azure Document Intelligence
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from loguru import logger
from typing import Optional
import uuid

from app.services.document_extractor import get_document_extractor

router = APIRouter(prefix="/api/v1/document", tags=["document"])


@router.post("/extract")
async def extract_document(
    file: UploadFile = File(..., description="Medical document (PDF, PNG, JPG, JPEG)"),
    document_type: str = Form("medical_form", description="Type of document: medical_form, prescription, lab_result, insurance_card"),
    patient_id: Optional[str] = Form(None, description="Optional patient identifier")
):
    """
    Extract structured data from uploaded medical document
    
    Uses Azure Document Intelligence (Form Recognizer) to:
    - Extract text via OCR
    - Identify key-value pairs
    - Extract tables
    - Recognize document structure
    
    Supported formats: PDF, PNG, JPG, JPEG
    Max size: 10MB
    
    Args:
        file: Uploaded document file
        document_type: Type of document for specialized extraction
        patient_id: Optional patient identifier for tracking
        
    Returns:
        Extracted document data with text, key-value pairs, tables
    """
    logger.info(f"Processing document upload: {file.filename} (type: {document_type})")
    
    # Validate file type
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (10MB max)
    max_size = 10 * 1024 * 1024  # 10MB
    
    try:
        # Read file content
        content = await file.read()
        
        if len(content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {len(content) / 1024 / 1024:.1f}MB. Maximum: 10MB"
            )
        
        # Extract document data
        document_extractor = get_document_extractor()
        
        extracted_data = document_extractor.extract_from_document(
            document_bytes=content,
            document_type=document_type
        )
        
        # Add metadata
        extraction_id = str(uuid.uuid4())
        result = {
            "extraction_id": extraction_id,
            "filename": file.filename,
            "document_type": document_type,
            "patient_id": patient_id,
            "extracted_data": extracted_data,
            "content_length": len(content),
            "success": True
        }
        
        logger.info(f"Document extraction complete: {extraction_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract document: {str(e)}"
        )
    finally:
        await file.close()


@router.get("/supported-types")
async def get_supported_document_types():
    """
    Get list of supported document types and their descriptions
    
    Returns:
        Dict of document types with descriptions
    """
    return {
        "supported_types": {
            "medical_form": {
                "description": "General medical forms (intake, history, consent)",
                "fields": ["patient_name", "dob", "address", "phone", "medical_history"]
            },
            "prescription": {
                "description": "Prescription documents",
                "fields": ["medication_name", "dosage", "frequency", "prescriber", "date"]
            },
            "lab_result": {
                "description": "Laboratory test results",
                "fields": ["test_name", "result_value", "reference_range", "date", "lab_name"]
            },
            "insurance_card": {
                "description": "Insurance/health card information",
                "fields": ["member_id", "group_number", "plan_name", "coverage_dates"]
            }
        },
        "supported_formats": [".pdf", ".png", ".jpg", ".jpeg"],
        "max_file_size_mb": 10
    }
