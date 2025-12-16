"""
Tests for Azure Document Intelligence Integration
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.document_extractor import (
    DocumentExtractor,
    DocumentType,
    get_document_extractor
)


@pytest.fixture
def extractor():
    """Create document extractor instance (without Azure)"""
    return DocumentExtractor(endpoint=None, key=None)


@pytest.fixture
def mock_azure_result():
    """Mock Azure analysis result"""
    result = Mock()
    
    # Mock pages
    page = Mock()
    line1 = Mock()
    line1.content = "PRESCRIPTION"
    line1.confidence = 0.95
    line2 = Mock()
    line2.content = "Patient: John Doe"
    line2.confidence = 0.92
    line3 = Mock()
    line3.content = "Medication: Paracetamol 500mg"
    line3.confidence = 0.90
    
    page.lines = [line1, line2, line3]
    result.pages = [page]
    
    # Mock key-value pairs
    kv1 = Mock()
    kv1.key = Mock()
    kv1.key.content = "Patient Name"
    kv1.value = Mock()
    kv1.value.content = "John Doe"
    
    kv2 = Mock()
    kv2.key = Mock()
    kv2.key.content = "Doctor"
    kv2.value = Mock()
    kv2.value.content = "Dr. Smith"
    
    result.key_value_pairs = [kv1, kv2]
    
    # Mock tables
    result.tables = []
    
    return result


class TestDocumentExtractorInitialization:
    """Test initialization and availability"""
    
    def test_initialization_without_credentials(self):
        """Test initialization without Azure credentials"""
        extractor = DocumentExtractor(endpoint=None, key=None)
        assert not extractor.is_available()
        assert extractor.client is None
    
    def test_initialization_with_credentials(self):
        """Test initialization with credentials"""
        # Even with credentials, client may not initialize if SDK not available
        extractor = DocumentExtractor(
            endpoint="https://test.cognitiveservices.azure.com/",
            key="test_key"
        )
        # Don't assert client exists as it depends on SDK availability
        assert extractor.endpoint is not None
        assert extractor.key is not None


class TestFallbackExtraction:
    """Test fallback behavior when Azure not available"""
    
    @pytest.mark.asyncio
    async def test_fallback_for_image(self, extractor):
        """Test fallback extraction for images"""
        image_data = b"fake_image_data"
        
        result = await extractor.extract_from_image(
            image_data,
            DocumentType.PRESCRIPTION
        )
        
        assert result["fallback"] is True
        assert "message" in result
        assert result["document_type"] == DocumentType.PRESCRIPTION
    
    @pytest.mark.asyncio
    async def test_fallback_for_pdf(self, extractor):
        """Test fallback extraction for PDFs"""
        pdf_data = b"fake_pdf_data"
        
        result = await extractor.extract_from_pdf(
            pdf_data,
            DocumentType.LAB_RESULT
        )
        
        assert result["fallback"] is True
        assert result["document_type"] == DocumentType.LAB_RESULT


class TestTextExtraction:
    """Test text extraction from results"""
    
    def test_extract_full_text(self, extractor, mock_azure_result):
        """Test full text extraction"""
        text = extractor._extract_full_text(mock_azure_result)
        
        assert "PRESCRIPTION" in text
        assert "Patient: John Doe" in text
        assert "Paracetamol" in text
    
    def test_extract_key_value_pairs(self, extractor, mock_azure_result):
        """Test key-value pair extraction"""
        pairs = extractor._extract_key_value_pairs(mock_azure_result)
        
        assert pairs["Patient Name"] == "John Doe"
        assert pairs["Doctor"] == "Dr. Smith"
    
    def test_calculate_confidence(self, extractor, mock_azure_result):
        """Test confidence calculation"""
        confidence = extractor._calculate_confidence(mock_azure_result)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8  # Should be high based on mock data


class TestTableExtraction:
    """Test table extraction"""
    
    def test_extract_tables(self, extractor):
        """Test table extraction from result"""
        result = Mock()
        
        # Mock table
        table = Mock()
        table.row_count = 2
        table.column_count = 3
        
        cell1 = Mock()
        cell1.row_index = 0
        cell1.column_index = 0
        cell1.content = "Test"
        cell1.kind = "columnHeader"
        
        cell2 = Mock()
        cell2.row_index = 0
        cell2.column_index = 1
        cell2.content = "Value"
        cell2.kind = "columnHeader"
        
        cell3 = Mock()
        cell3.row_index = 1
        cell3.column_index = 0
        cell3.content = "Hemoglobin"
        cell3.kind = "content"
        
        cell4 = Mock()
        cell4.row_index = 1
        cell4.column_index = 1
        cell4.content = "14.5"
        cell4.kind = "content"
        
        table.cells = [cell1, cell2, cell3, cell4]
        result.tables = [table]
        
        tables = extractor._extract_tables(result)
        
        assert len(tables) == 1
        assert tables[0]["row_count"] == 2
        assert tables[0]["column_count"] == 3
        assert len(tables[0]["cells"]) == 4


class TestPrescriptionParsing:
    """Test prescription-specific parsing"""
    
    def test_parse_prescription_with_patient_name(self, extractor):
        """Test prescription parsing with patient data"""
        extracted_data = {
            "text": "prescription for patient john doe paracetamol 500mg",
            "key_value_pairs": {
                "Patient Name": "John Doe",
                "Doctor": "Dr. Smith",
                "Date": "2025-12-16"
            }
        }
        
        prescription = extractor._parse_prescription(extracted_data)
        
        assert prescription["patient_name"] == "John Doe"
        assert prescription["doctor_name"] == "Dr. Smith"
        assert prescription["date"] == "2025-12-16"
    
    def test_parse_prescription_medication_detection(self, extractor):
        """Test medication detection in prescription"""
        extracted_data = {
            "text": "paracetamol 500mg three times daily amoxicillin 250mg",
            "key_value_pairs": {}
        }
        
        prescription = extractor._parse_prescription(extracted_data)
        
        # Should detect both medications
        med_names = [m["name"] for m in prescription["medications"]]
        assert "paracetamol" in med_names
        assert "amoxicillin" in med_names
    
    def test_parse_prescription_nigerian_medications(self, extractor):
        """Test detection of Nigerian-specific medications"""
        extracted_data = {
            "text": "coartem for malaria treatment lonart alternative chloroquine",
            "key_value_pairs": {}
        }
        
        prescription = extractor._parse_prescription(extracted_data)
        
        med_names = [m["name"] for m in prescription["medications"]]
        assert "coartem" in med_names
        assert "lonart" in med_names
        assert "chloroquine" in med_names


class TestLabResultParsing:
    """Test lab result parsing"""
    
    def test_parse_lab_result_from_table(self, extractor):
        """Test lab result parsing from table data"""
        extracted_data = {
            "text": "Laboratory Results",
            "tables": [{
                "row_count": 3,
                "column_count": 4,
                "cells": [
                    {"row_index": 0, "column_index": 0, "content": "Test"},
                    {"row_index": 0, "column_index": 1, "content": "Result"},
                    {"row_index": 0, "column_index": 2, "content": "Unit"},
                    {"row_index": 0, "column_index": 3, "content": "Reference"},
                    {"row_index": 1, "column_index": 0, "content": "Hemoglobin"},
                    {"row_index": 1, "column_index": 1, "content": "14.5"},
                    {"row_index": 1, "column_index": 2, "content": "g/dL"},
                    {"row_index": 1, "column_index": 3, "content": "12-16"},
                    {"row_index": 2, "column_index": 0, "content": "WBC"},
                    {"row_index": 2, "column_index": 1, "content": "7.2"},
                    {"row_index": 2, "column_index": 2, "content": "10^9/L"},
                    {"row_index": 2, "column_index": 3, "content": "4-11"}
                ]
            }]
        }
        
        lab_data = extractor._parse_lab_result(extracted_data)
        
        assert len(lab_data["results"]) > 0
        # Should find test results
        tests = [r["test"] for r in lab_data["results"]]
        assert any("Hemoglobin" in str(t) or "WBC" in str(t) for t in tests)


class TestDocumentTypes:
    """Test different document type handling"""
    
    @pytest.mark.asyncio
    async def test_prescription_document_type(self, extractor):
        """Test prescription document processing"""
        result = await extractor.extract_from_image(
            b"test_data",
            DocumentType.PRESCRIPTION
        )
        
        assert result["document_type"] == DocumentType.PRESCRIPTION
        # Fallback mode, but should have prescription_data key
        # (even if empty due to fallback)
    
    @pytest.mark.asyncio
    async def test_lab_result_document_type(self, extractor):
        """Test lab result document processing"""
        result = await extractor.extract_from_image(
            b"test_data",
            DocumentType.LAB_RESULT
        )
        
        assert result["document_type"] == DocumentType.LAB_RESULT
    
    @pytest.mark.asyncio
    async def test_general_document_type(self, extractor):
        """Test general document processing"""
        result = await extractor.extract_from_image(
            b"test_data",
            DocumentType.GENERAL
        )
        
        assert result["document_type"] == DocumentType.GENERAL


class TestLanguageDetection:
    """Test language detection"""
    
    def test_detect_language_default(self, extractor):
        """Test default language detection"""
        result = Mock()
        result.pages = []
        
        language = extractor._detect_language(result)
        assert language == "en"  # Default to English


class TestSingletonPattern:
    """Test singleton instance management"""
    
    def test_singleton_returns_same_instance(self):
        """Test get_document_extractor returns same instance"""
        extractor1 = get_document_extractor()
        extractor2 = get_document_extractor()
        
        assert extractor1 is extractor2
