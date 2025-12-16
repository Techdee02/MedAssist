"""
Azure AI Document Intelligence Integration

Extracts structured data from medical documents:
- Prescriptions
- Lab results
- Medical records
- Insurance cards
- Referral letters
"""

from typing import Dict, List, Optional, Any, BinaryIO
from loguru import logger
import base64
from io import BytesIO

try:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import HttpResponseError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("Azure AI Document Intelligence SDK not installed")

from app.config import settings


class DocumentType:
    """Supported medical document types"""
    PRESCRIPTION = "prescription"
    LAB_RESULT = "lab_result"
    MEDICAL_RECORD = "medical_record"
    INSURANCE_CARD = "insurance_card"
    REFERRAL = "referral"
    GENERAL = "general"


class DocumentExtractor:
    """
    Extracts structured data from medical documents using Azure AI Document Intelligence.
    
    Features:
    - OCR for printed and handwritten text
    - Layout analysis
    - Table extraction
    - Key-value pair detection
    - Multi-language support (English + Nigerian languages)
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None
    ):
        """
        Initialize document extractor.
        
        Args:
            endpoint: Azure Document Intelligence endpoint
            key: Azure API key
        """
        self.endpoint = endpoint or settings.azure_document_intelligence_endpoint
        self.key = key or settings.azure_document_intelligence_key
        self.client = None
        
        if AZURE_AVAILABLE and self.endpoint and self.key:
            try:
                self.client = DocumentAnalysisClient(
                    endpoint=self.endpoint,
                    credential=AzureKeyCredential(self.key)
                )
                logger.info("Azure Document Intelligence client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure client: {e}")
        else:
            logger.warning(
                "Azure Document Intelligence not configured. "
                "Set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY"
            )
    
    def is_available(self) -> bool:
        """Check if Azure service is available"""
        return self.client is not None
    
    async def extract_from_image(
        self,
        image_data: bytes,
        document_type: str = DocumentType.GENERAL
    ) -> Dict:
        """
        Extract text and structure from image.
        
        Args:
            image_data: Image bytes
            document_type: Type of medical document
            
        Returns:
            Extracted data dictionary
        """
        if not self.is_available():
            return self._fallback_extraction(image_data, document_type)
        
        try:
            # Use prebuilt model for general document analysis
            poller = self.client.begin_analyze_document(
                "prebuilt-document",  # General document model
                document=BytesIO(image_data)
            )
            
            result = poller.result()
            
            # Extract structured data
            extracted_data = {
                "document_type": document_type,
                "text": self._extract_full_text(result),
                "key_value_pairs": self._extract_key_value_pairs(result),
                "tables": self._extract_tables(result),
                "entities": [],
                "confidence": self._calculate_confidence(result),
                "pages": len(result.pages),
                "language": self._detect_language(result)
            }
            
            # Post-process based on document type
            if document_type == DocumentType.PRESCRIPTION:
                extracted_data["prescription_data"] = self._parse_prescription(extracted_data)
            elif document_type == DocumentType.LAB_RESULT:
                extracted_data["lab_data"] = self._parse_lab_result(extracted_data)
            
            logger.info(
                f"Extracted {len(extracted_data['text'])} characters from {document_type} document"
            )
            
            return extracted_data
        
        except HttpResponseError as e:
            logger.error(f"Azure API error: {e}")
            return {"error": str(e), "fallback": True}
        except Exception as e:
            logger.error(f"Document extraction error: {e}")
            return {"error": str(e), "fallback": True}
    
    async def extract_from_pdf(
        self,
        pdf_data: bytes,
        document_type: str = DocumentType.GENERAL
    ) -> Dict:
        """
        Extract text and structure from PDF.
        
        Args:
            pdf_data: PDF bytes
            document_type: Type of medical document
            
        Returns:
            Extracted data dictionary
        """
        if not self.is_available():
            return self._fallback_extraction(pdf_data, document_type)
        
        try:
            poller = self.client.begin_analyze_document(
                "prebuilt-document",
                document=BytesIO(pdf_data)
            )
            
            result = poller.result()
            
            return {
                "document_type": document_type,
                "text": self._extract_full_text(result),
                "key_value_pairs": self._extract_key_value_pairs(result),
                "tables": self._extract_tables(result),
                "pages": len(result.pages),
                "confidence": self._calculate_confidence(result)
            }
        
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return {"error": str(e)}
    
    def _extract_full_text(self, result) -> str:
        """Extract all text from document"""
        text_parts = []
        for page in result.pages:
            for line in page.lines:
                text_parts.append(line.content)
        return "\n".join(text_parts)
    
    def _extract_key_value_pairs(self, result) -> Dict[str, str]:
        """Extract key-value pairs (e.g., Patient Name: John Doe)"""
        pairs = {}
        if hasattr(result, 'key_value_pairs'):
            for kv in result.key_value_pairs:
                if kv.key and kv.value:
                    key = kv.key.content if hasattr(kv.key, 'content') else str(kv.key)
                    value = kv.value.content if hasattr(kv.value, 'content') else str(kv.value)
                    pairs[key] = value
        return pairs
    
    def _extract_tables(self, result) -> List[Dict]:
        """Extract tables from document"""
        tables_data = []
        if hasattr(result, 'tables'):
            for table in result.tables:
                table_data = {
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": []
                }
                for cell in table.cells:
                    table_data["cells"].append({
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "content": cell.content,
                        "is_header": cell.kind == "columnHeader" if hasattr(cell, 'kind') else False
                    })
                tables_data.append(table_data)
        return tables_data
    
    def _calculate_confidence(self, result) -> float:
        """Calculate average confidence score"""
        if not hasattr(result, 'pages'):
            return 0.0
        
        confidences = []
        for page in result.pages:
            for line in page.lines:
                if hasattr(line, 'confidence'):
                    confidences.append(line.confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _detect_language(self, result) -> str:
        """Detect document language"""
        # Azure can detect language, check result metadata
        if hasattr(result, 'languages'):
            return result.languages[0].language_code if result.languages else "en"
        return "en"
    
    def _parse_prescription(self, extracted_data: Dict) -> Dict:
        """
        Parse prescription-specific data.
        
        Looks for:
        - Patient name
        - Doctor name
        - Medication names
        - Dosages
        - Instructions
        - Date
        """
        text = extracted_data.get("text", "").lower()
        kv_pairs = extracted_data.get("key_value_pairs", {})
        
        prescription = {
            "patient_name": None,
            "doctor_name": None,
            "medications": [],
            "date": None,
            "pharmacy": None
        }
        
        # Extract from key-value pairs
        for key, value in kv_pairs.items():
            key_lower = key.lower()
            if "patient" in key_lower and "name" in key_lower:
                prescription["patient_name"] = value
            elif "doctor" in key_lower or "physician" in key_lower:
                prescription["doctor_name"] = value
            elif "date" in key_lower:
                prescription["date"] = value
        
        # Look for medication patterns in text
        # Common Nigerian medications
        medications = [
            "paracetamol", "amoxicillin", "chloroquine", "artemether",
            "lumefantrine", "metronidazole", "ciprofloxacin", "azithromycin",
            "amoxicillin/clavulanate", "coartem", "lonart"
        ]
        
        for med in medications:
            if med in text:
                prescription["medications"].append({
                    "name": med,
                    "found": True
                })
        
        return prescription
    
    def _parse_lab_result(self, extracted_data: Dict) -> Dict:
        """
        Parse laboratory result data.
        
        Looks for:
        - Test name
        - Results
        - Reference ranges
        - Units
        """
        tables = extracted_data.get("tables", [])
        
        lab_data = {
            "test_type": None,
            "results": [],
            "date": None
        }
        
        # Lab results often in table format
        for table in tables:
            cells = table.get("cells", [])
            # Group cells by row
            rows = {}
            for cell in cells:
                row_idx = cell["row_index"]
                if row_idx not in rows:
                    rows[row_idx] = []
                rows[row_idx].append(cell)
            
            # Parse each row as potential test result
            for row_idx, row_cells in rows.items():
                if len(row_cells) >= 2:  # At least test name and value
                    row_cells.sort(key=lambda x: x["column_index"])
                    lab_data["results"].append({
                        "test": row_cells[0]["content"],
                        "value": row_cells[1]["content"] if len(row_cells) > 1 else None,
                        "unit": row_cells[2]["content"] if len(row_cells) > 2 else None,
                        "reference": row_cells[3]["content"] if len(row_cells) > 3 else None
                    })
        
        return lab_data
    
    def _fallback_extraction(self, data: bytes, document_type: str) -> Dict:
        """Fallback when Azure is not available"""
        logger.warning("Using fallback extraction (Azure not configured)")
        return {
            "document_type": document_type,
            "text": "[Document content - OCR not available]",
            "key_value_pairs": {},
            "tables": [],
            "confidence": 0.0,
            "fallback": True,
            "message": "Azure Document Intelligence not configured. Please set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and KEY."
        }


# Singleton instance
_document_extractor = None


def get_document_extractor() -> DocumentExtractor:
    """Get or create singleton DocumentExtractor instance"""
    global _document_extractor
    if _document_extractor is None:
        _document_extractor = DocumentExtractor()
    return _document_extractor
