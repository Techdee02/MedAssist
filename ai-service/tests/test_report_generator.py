"""
Tests for Report Generator
"""
import pytest
import json
from app.services.report_generator import (
    ReportGenerator,
    get_report_generator
)
from app.models.schemas import IntentType


@pytest.fixture
def generator():
    """Create report generator instance"""
    return ReportGenerator()


@pytest.fixture
def sample_symptom_data():
    """Sample symptom data"""
    return {
        "primary_symptom": "headache",
        "onset": "suddenly",
        "duration": "2 days",
        "severity": 7,
        "location": "forehead",
        "character": "throbbing",
        "aggravating_factors": "bright light",
        "relieving_factors": "rest",
        "associated_symptoms": ["nausea", "sensitivity to light"],
        "previous_episodes": "yes, last month",
        "medications_tried": ["paracetamol"],
        "vital_signs": {
            "temperature": 37.2,
            "bp_systolic": 130,
            "bp_diastolic": 85,
            "pulse": 78,
            "spo2": 98
        },
        "is_complete": True
    }


@pytest.fixture
def sample_triage_result():
    """Sample triage result"""
    return {
        "score": 6,
        "triage_level": "high",
        "wait_time_recommendation": "Within 1 hour",
        "red_flag_detected": False,
        "red_flag_category": None,
        "requires_immediate_attention": False,
        "recommended_actions": [
            "Assess within 1 hour",
            "Monitor vital signs",
            "Prepare for physician evaluation"
        ]
    }


@pytest.fixture
def sample_conversation():
    """Sample conversation history"""
    return [
        {"role": "user", "content": "I have a bad headache"},
        {"role": "assistant", "content": "I'm sorry to hear that. When did the headache start?"},
        {"role": "user", "content": "2 days ago"},
        {"role": "assistant", "content": "How severe is the pain on a scale of 1-10?"},
        {"role": "user", "content": "About 7"}
    ]


class TestReportGeneration:
    """Test complete report generation"""
    
    def test_generate_complete_report(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test generation of complete report"""
        report = generator.generate_report(
            patient_id="P123456",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation,
            metadata={"age": 35, "gender": "Female"}
        )
        
        assert report["patient_id"] == "P123456"
        assert "report_id" in report
        assert report["report_id"].startswith("RPT-P123456-")
        assert "generated_at" in report
        assert report["report_version"] == "1.0"
    
    def test_report_contains_intent(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test report includes intent information"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        assert report["intent"]["type"] == "symptom_inquiry"
        assert "description" in report["intent"]
    
    def test_report_contains_triage(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test report includes triage information"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        assert report["triage"]["level"] == "high"
        assert report["triage"]["score"] == 6
        assert report["triage"]["wait_time"] == "Within 1 hour"
        assert report["triage"]["red_flag_detected"] is False
        assert len(report["triage"]["recommended_actions"]) > 0
    
    def test_report_contains_symptoms(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test report includes formatted symptom data"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        assert report["symptoms"]["primary_symptom"] == "headache"
        assert report["symptoms"]["severity"] == 7
        assert report["symptoms"]["duration"] == "2 days"
        assert "vital_signs" in report["symptoms"]


class TestRedFlagReporting:
    """Test red flag detection in reports"""
    
    def test_red_flag_in_report(
        self,
        generator,
        sample_symptom_data,
        sample_conversation
    ):
        """Test red flag detection appears in report"""
        triage_result = {
            "score": 10,
            "triage_level": "critical",
            "wait_time_recommendation": "Immediate",
            "red_flag_detected": True,
            "red_flag_category": "cardiac",
            "requires_immediate_attention": True,
            "recommended_actions": ["IMMEDIATE emergency care required"]
        }
        
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.EMERGENCY,
            symptom_data=sample_symptom_data,
            triage_result=triage_result,
            conversation_history=sample_conversation
        )
        
        assert report["triage"]["red_flag_detected"] is True
        assert report["triage"]["red_flag_category"] == "cardiac"
        assert report["triage"]["requires_immediate_attention"] is True


class TestClinicianSummary:
    """Test clinician-facing summary generation"""
    
    def test_clinician_summary_generated(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test clinician summary is generated"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        summary = report["summaries"]["clinician"]
        assert "CLINICIAN SUMMARY" in summary
        assert "CHIEF COMPLAINT" in summary
        assert "headache" in summary.lower()
    
    def test_clinician_summary_includes_vitals(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test vital signs appear in clinician summary"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        summary = report["summaries"]["clinician"]
        assert "VITAL SIGNS" in summary
        assert "37.2" in summary  # Temperature
        assert "130/85" in summary  # BP
    
    def test_clinician_summary_red_flag_highlighted(
        self,
        generator,
        sample_symptom_data,
        sample_conversation
    ):
        """Test red flags are highlighted in clinician summary"""
        triage_result = {
            "score": 10,
            "triage_level": "critical",
            "wait_time_recommendation": "Immediate",
            "red_flag_detected": True,
            "red_flag_category": "cardiac",
            "requires_immediate_attention": True,
            "recommended_actions": ["Emergency care"]
        }
        
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.EMERGENCY,
            symptom_data=sample_symptom_data,
            triage_result=triage_result,
            conversation_history=sample_conversation
        )
        
        summary = report["summaries"]["clinician"]
        assert "RED FLAG" in summary
        assert "CRITICAL" in summary
        assert "cardiac" in summary.lower()
    
    def test_clinician_summary_includes_patient_metadata(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test patient metadata in clinician summary"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation,
            metadata={
                "age": 65,
                "gender": "Male",
                "chronic_conditions": ["diabetes", "hypertension"],
                "pregnant": False
            }
        )
        
        summary = report["summaries"]["clinician"]
        assert "65yo" in summary
        assert "Male" in summary
        assert "diabetes" in summary
        assert "hypertension" in summary


class TestPatientSummary:
    """Test patient-facing summary generation"""
    
    def test_patient_summary_generated(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test patient summary is generated"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        summary = report["summaries"]["patient"]
        assert "Thank you" in summary
        assert len(summary) > 0
    
    def test_patient_summary_includes_pidgin(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test patient summary includes Nigerian Pidgin"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        summary = report["summaries"]["patient"]
        assert "Tank you" in summary or "Wetin go happen" in summary
    
    def test_patient_summary_critical_case(
        self,
        generator,
        sample_symptom_data,
        sample_conversation
    ):
        """Test patient summary for critical case"""
        triage_result = {
            "score": 10,
            "triage_level": "critical",
            "wait_time_recommendation": "Immediate",
            "red_flag_detected": True,
            "red_flag_category": "cardiac",
            "requires_immediate_attention": True,
            "recommended_actions": ["Emergency care"]
        }
        
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.EMERGENCY,
            symptom_data=sample_symptom_data,
            triage_result=triage_result,
            conversation_history=sample_conversation
        )
        
        summary = report["summaries"]["patient"]
        assert "IMMEDIATE" in summary
        assert "emergency" in summary.lower()


class TestMinimalReport:
    """Test minimal report generation for non-symptom intents"""
    
    def test_minimal_report_for_appointment(self, generator):
        """Test minimal report for appointment booking"""
        report = generator.generate_minimal_report(
            patient_id="P123",
            intent=IntentType.APPOINTMENT_BOOKING,
            message="I need to book an appointment for next week"
        )
        
        assert report["patient_id"] == "P123"
        assert report["intent"]["type"] == "appointment_booking"
        assert report["message"] == "I need to book an appointment for next week"
        assert report["triage"] is None
        assert report["requires_medical_attention"] is False
    
    def test_minimal_report_for_general_inquiry(self, generator):
        """Test minimal report for general inquiry"""
        report = generator.generate_minimal_report(
            patient_id="P456",
            intent=IntentType.GENERAL_INQUIRY,
            message="What are your opening hours?"
        )
        
        assert report["intent"]["type"] == "general_inquiry"
        assert "opening hours" in report["message"]


class TestExportFunctions:
    """Test report export functions"""
    
    def test_export_to_json(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test JSON export"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        json_str = generator.export_to_json(report)
        
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["patient_id"] == "P123"
    
    def test_export_to_ehr_format(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test EHR format export"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        ehr = generator.export_to_ehr_format(report)
        
        assert ehr["patient_id"] == "P123"
        assert ehr["chief_complaint"] == "headache"
        assert ehr["triage_level"] == "high"
        assert ehr["triage_score"] == 6
        assert "vital_signs" in ehr
        assert ehr["urgent"] is False


class TestSafetyIntegration:
    """Test safety issue reporting"""
    
    def test_safety_issues_in_report(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test safety issues appear in report"""
        safety_issues = [
            "Diagnosis attempt detected",
            "Prescription recommendation blocked"
        ]
        
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation,
            safety_issues=safety_issues
        )
        
        assert report["safety"]["issues_detected"] is True
        assert len(report["safety"]["issues"]) == 2
        assert "Diagnosis attempt" in report["safety"]["issues"][0]
    
    def test_no_safety_issues(
        self,
        generator,
        sample_symptom_data,
        sample_triage_result,
        sample_conversation
    ):
        """Test report with no safety issues"""
        report = generator.generate_report(
            patient_id="P123",
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=sample_symptom_data,
            triage_result=sample_triage_result,
            conversation_history=sample_conversation
        )
        
        assert report["safety"]["issues_detected"] is False
        assert len(report["safety"]["issues"]) == 0


class TestSingletonPattern:
    """Test singleton instance management"""
    
    def test_singleton_returns_same_instance(self):
        """Test get_report_generator returns same instance"""
        gen1 = get_report_generator()
        gen2 = get_report_generator()
        
        assert gen1 is gen2
