"""
Comprehensive API Endpoint Tests

Tests all API endpoints with proper mocking and error handling
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import io

from app.main import app
from app.models.schemas import IntentType, TriageLevel


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check_basic(self, client):
        """Test basic health check"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "MedAssist AI Service"
        assert data["version"] == "1.0.0"
        assert "components" in data
        
    def test_health_check_with_groq(self, client):
        """Test health check with Groq API enabled"""
        with patch("app.api.health.settings.groq_api_key", "test-key"):
            with patch("app.api.health.settings.use_llm", True):
                with patch("groq.Groq") as mock_groq:
                    # Mock successful Groq response
                    mock_client = Mock()
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_client.chat.completions.create.return_value = mock_response
                    mock_groq.return_value = mock_client
                    
                    response = client.get("/api/v1/health")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["components"]["groq_api"]["status"] == "healthy"


class TestMessageEndpoint:
    """Tests for message processing endpoint"""
    
    @patch("app.api.message.get_intent_classifier")
    @patch("app.api.message.get_slot_filler")
    @patch("app.api.message.get_conversation_manager")
    def test_process_message_appointment(
        self, mock_conv_mgr, mock_slot_filler, mock_intent_classifier, client
    ):
        """Test processing appointment booking message"""
        # Mock intent classifier
        mock_classifier = Mock()
        mock_result = Mock()
        mock_result.intent = IntentType.APPOINTMENT_BOOKING
        mock_result.confidence = 0.95
        mock_result.reasoning = "Patient requesting appointment"
        mock_classifier.classify.return_value = mock_result
        mock_intent_classifier.return_value = mock_classifier
        
        # Mock slot filler
        mock_filler = Mock()
        mock_filler.extract_slots.return_value = {
            "date": "next Tuesday",
            "time": "2pm"
        }
        mock_filler.get_missing_slots.return_value = []
        mock_slot_filler.return_value = mock_filler
        
        # Mock conversation manager
        mock_mgr = Mock()
        mock_conv_mgr.return_value = mock_mgr
        
        request_data = {
            "message_id": "test-001",
            "patient_id": "patient-123",
            "message": "I need to book an appointment for next Tuesday at 2pm",
            "conversation_history": []
        }
        
        response = client.post("/api/v1/message/process", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["intent"] == "appointment_booking"
        assert data["confidence"] == 0.95
        assert data["next_action"] == "complete"
        assert "appointment" in data["response"].lower()
        
    @patch("app.api.message.get_intent_classifier")
    @patch("app.api.message.get_slot_filler")
    @patch("app.api.message.get_conversation_manager")
    def test_process_message_emergency(
        self, mock_conv_mgr, mock_slot_filler, mock_intent_classifier, client
    ):
        """Test processing emergency message"""
        # Mock intent classifier
        mock_classifier = Mock()
        mock_result = Mock()
        mock_result.intent = IntentType.EMERGENCY
        mock_result.confidence = 0.99
        mock_classifier.classify.return_value = mock_result
        mock_intent_classifier.return_value = mock_classifier
        
        request_data = {
            "message_id": "test-002",
            "patient_id": "patient-456",
            "message": "I can't breathe and my chest hurts",
            "conversation_history": []
        }
        
        response = client.post("/api/v1/message/process", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["intent"] == "emergency"
        assert data["next_action"] == "escalate"
        assert data["requires_human_review"] is True
        assert "emergency" in data["response"].lower()
        
    @patch("app.api.message.get_intent_classifier")
    @patch("app.api.message.get_slot_filler")
    @patch("app.api.message.get_conversation_manager")
    @patch("app.api.message.get_symptom_intake_agent")
    @patch("app.api.message.get_triage_scorer")
    def test_process_message_symptom_with_triage(
        self, mock_triage, mock_symptom, mock_conv_mgr, 
        mock_slot_filler, mock_intent_classifier, client
    ):
        """Test processing symptom inquiry with triage"""
        # Mock intent classifier
        mock_classifier = Mock()
        mock_result = Mock()
        mock_result.intent = IntentType.SYMPTOM_INQUIRY
        mock_result.confidence = 0.92
        mock_classifier.classify.return_value = mock_result
        mock_intent_classifier.return_value = mock_classifier
        
        # Mock slot filler
        mock_filler = Mock()
        mock_filler.extract_slots.return_value = {
            "symptom": "headache",
            "duration": "2 days",
            "severity": 7
        }
        mock_filler.get_missing_slots.return_value = []
        mock_slot_filler.return_value = mock_filler
        
        # Mock conversation manager
        mock_mgr = Mock()
        mock_conv_mgr.return_value = mock_mgr
        
        # Mock symptom intake
        mock_intake = Mock()
        mock_intake.collect_symptom_info.return_value = {
            "primary_symptom": "headache",
            "completeness": 0.8
        }
        mock_symptom.return_value = mock_intake
        
        # Mock triage scorer
        mock_scorer = Mock()
        mock_scorer.calculate_triage_score.return_value = {
            "level": "medium",
            "urgency_score": 6,
            "red_flags": []
        }
        mock_triage.return_value = mock_scorer
        
        request_data = {
            "message_id": "test-003",
            "patient_id": "patient-789",
            "message": "I have a severe headache for 2 days",
            "conversation_history": []
        }
        
        response = client.post("/api/v1/message/process", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["intent"] == "symptom_inquiry"
        assert data["triage_level"] == "medium"
        assert data["next_action"] == "complete"


class TestSymptomEndpoint:
    """Tests for symptom report endpoint"""
    
    @patch("app.api.symptom.get_symptom_intake_agent")
    @patch("app.api.symptom.get_triage_scorer")
    @patch("app.api.symptom.get_report_generator")
    def test_generate_symptom_report(
        self, mock_report_gen, mock_triage, mock_intake, client
    ):
        """Test generating symptom report"""
        # Mock symptom intake
        mock_intake_obj = Mock()
        mock_intake_obj._assess_completeness.return_value = 0.85
        mock_intake.return_value = mock_intake_obj
        
        # Mock triage scorer
        mock_scorer = Mock()
        mock_scorer.calculate_triage_score.return_value = {
            "level": "high",
            "urgency_score": 8,
            "red_flags": ["severe pain", "sudden onset"]
        }
        mock_triage.return_value = mock_scorer
        
        # Mock report generator
        mock_generator = Mock()
        mock_generator.generate_report.return_value = {
            "chief_complaint": "chest pain",
            "assessment": "requires immediate evaluation"
        }
        mock_report_gen.return_value = mock_generator
        
        request_data = {
            "patient_id": "patient-001",
            "conversation_data": {
                "primary_symptom": "chest pain",
                "onset": "sudden",
                "duration": "30 minutes",
                "severity": 9,
                "location": "left side",
                "character": "crushing",
                "aggravating_factors": ["movement"],
                "relieving_factors": [],
                "associated_symptoms": ["shortness of breath"],
                "previous_episodes": False,
                "medications_tried": []
            }
        }
        
        response = client.post("/api/v1/symptom/report", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["patient_id"] == "patient-001"
        assert data["triage_level"] == "high"
        assert data["urgency_score"] == 8
        assert len(data["red_flags"]) == 2
        assert data["requires_immediate_attention"] is True
        assert "report_id" in data
        assert "human_summary" in data


class TestDocumentEndpoint:
    """Tests for document extraction endpoint"""
    
    @patch("app.api.document.get_document_extractor")
    def test_extract_document_success(self, mock_extractor, client):
        """Test successful document extraction"""
        # Mock document extractor
        mock_extractor_obj = Mock()
        mock_extractor_obj.extract_from_document.return_value = {
            "text": "Patient Name: John Doe",
            "key_value_pairs": {
                "patient_name": "John Doe",
                "dob": "1990-01-01"
            },
            "tables": []
        }
        mock_extractor.return_value = mock_extractor_obj
        
        # Create fake file
        file_content = b"Fake PDF content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        data = {"document_type": "medical_form"}
        
        response = client.post(
            "/api/v1/document/extract",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert result["filename"] == "test.pdf"
        assert result["document_type"] == "medical_form"
        assert "extracted_data" in result
        
    def test_extract_document_invalid_type(self, client):
        """Test document extraction with invalid file type"""
        file_content = b"test"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        data = {"document_type": "medical_form"}
        
        response = client.post(
            "/api/v1/document/extract",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
        
    def test_get_supported_document_types(self, client):
        """Test getting supported document types"""
        response = client.get("/api/v1/document/supported-types")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "supported_types" in data
        assert "medical_form" in data["supported_types"]
        assert "prescription" in data["supported_types"]
        assert "supported_formats" in data


class TestTranslationEndpoint:
    """Tests for translation endpoint"""
    
    @patch("app.api.translate.get_language_translator")
    def test_translate_text(self, mock_translator, client):
        """Test text translation"""
        # Mock translator
        mock_trans_obj = Mock()
        mock_trans_obj.translate.return_value = {
            "translated_text": "Bawo ni",
            "detected_language": "en",
            "confidence": 0.95
        }
        mock_translator.return_value = mock_trans_obj
        
        request_data = {
            "text": "How are you",
            "target_language": "yo"
        }
        
        response = client.post("/api/v1/translate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["translated_text"] == "Bawo ni"
        assert data["target_language"] == "yo"
        assert data["confidence"] == 0.95
        
    @patch("app.api.translate.get_language_translator")
    def test_translate_batch(self, mock_translator, client):
        """Test batch translation"""
        # Mock translator
        mock_trans_obj = Mock()
        mock_trans_obj.translate_batch.return_value = [
            {"translated_text": "Bawo ni", "source_language": "en"},
            {"translated_text": "E kaasan", "source_language": "en"}
        ]
        mock_translator.return_value = mock_trans_obj
        
        request_data = {
            "texts": ["How are you", "Good morning"],
            "target_language": "yo"
        }
        
        response = client.post("/api/v1/translate/batch", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 2
        assert len(data["translations"]) == 2
        
    @patch("app.api.translate.get_language_translator")
    def test_detect_language(self, mock_translator, client):
        """Test language detection"""
        # Mock translator
        mock_trans_obj = Mock()
        mock_trans_obj.detect_language.return_value = {
            "language": "yo",
            "confidence": 0.92,
            "alternatives": [{"language": "en", "confidence": 0.08}]
        }
        mock_translator.return_value = mock_trans_obj
        
        request_data = {
            "text": "Bawo ni o se wa"
        }
        
        response = client.post("/api/v1/translate/detect", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["detected_language"] == "yo"
        assert data["confidence"] == 0.92
        
    @patch("app.api.translate.get_language_translator")
    def test_get_supported_languages(self, mock_translator, client):
        """Test getting supported languages"""
        # Mock translator
        mock_trans_obj = Mock()
        mock_trans_obj.get_supported_languages.return_value = {
            "en": "English",
            "yo": "Yoruba",
            "ha": "Hausa",
            "ig": "Igbo"
        }
        mock_translator.return_value = mock_trans_obj
        
        response = client.get("/api/v1/translate/languages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "nigerian_languages" in data
        assert "yo" in data["nigerian_languages"]
        assert "ha" in data["nigerian_languages"]
        assert "ig" in data["nigerian_languages"]


class TestRootEndpoint:
    """Tests for root endpoint"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service info"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "MedAssist AI Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
