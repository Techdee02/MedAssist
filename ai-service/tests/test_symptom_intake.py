"""
Tests for Symptom Intake Agent
"""
import pytest
from app.services.symptom_intake import (
    SymptomIntakeAgent,
    SymptomIntakeStatus,
    get_symptom_intake_agent
)


@pytest.fixture
def agent():
    """Create symptom intake agent instance"""
    return SymptomIntakeAgent()


class TestSymptomExtraction:
    """Test symptom information extraction"""
    
    def test_extract_headache_symptom(self, agent):
        """Test extracting headache as primary symptom"""
        message = "I have a terrible headache"
        data = agent.extract_symptom_info(message)
        
        assert data["primary_symptom"] == "headache"
    
    def test_extract_pidgin_symptom(self, agent):
        """Test extracting symptom from Pidgin English"""
        message = "my belle dey pain me"
        data = agent.extract_symptom_info(message)
        
        assert data["primary_symptom"] == "stomach pain"
    
    def test_extract_onset(self, agent):
        """Test extracting onset timing"""
        message = "I started having this headache this morning"
        data = agent.extract_symptom_info(message)
        
        assert data.get("onset") == "this morning"
    
    def test_extract_duration(self, agent):
        """Test extracting symptom duration"""
        message = "I've had this headache for 3 days now"
        data = agent.extract_symptom_info(message)
        
        assert data.get("duration") == "3 days"
    
    def test_extract_severity_numeric(self, agent):
        """Test extracting numeric severity"""
        message = "The pain is about 7 out of 10"
        data = agent.extract_symptom_info(message)
        
        assert data.get("severity") == 7
    
    def test_extract_severity_descriptive(self, agent):
        """Test extracting descriptive severity"""
        message = "The pain is very severe"
        data = agent.extract_symptom_info(message)
        
        assert data.get("severity") == 9
    
    def test_extract_location(self, agent):
        """Test extracting pain location"""
        message = "The pain is in the center of my chest"
        data = agent.extract_symptom_info(message)
        
        assert data.get("location") == "chest center"
    
    def test_extract_character(self, agent):
        """Test extracting pain character"""
        message = "It's a sharp, stabbing pain"
        data = agent.extract_symptom_info(message)
        
        assert data.get("character") in ["sharp", "stabbing"]
    
    def test_extract_medications(self, agent):
        """Test extracting medications tried"""
        message = "I took paracetamol and ibuprofen but it didn't help"
        data = agent.extract_symptom_info(message)
        
        assert "medications_tried" in data
        assert len(data["medications_tried"]) > 0
        assert "paracetamol" in data["medications_tried"]
    
    def test_extract_previous_episodes_yes(self, agent):
        """Test extracting previous episodes (yes)"""
        message = "I've had this before"
        data = agent.extract_symptom_info(message)
        
        assert data.get("previous_episodes") is True
    
    def test_extract_previous_episodes_no(self, agent):
        """Test extracting previous episodes (no)"""
        message = "This is the first time"
        data = agent.extract_symptom_info(message)
        
        assert data.get("previous_episodes") is False


class TestMultiTurnConversation:
    """Test multi-turn conversation flow"""
    
    def test_incremental_data_collection(self, agent):
        """Test collecting data over multiple messages"""
        # First message
        data = agent.extract_symptom_info("I have a headache", {})
        assert data["primary_symptom"] == "headache"
        
        # Second message
        data = agent.extract_symptom_info("It started this morning", data)
        assert data["onset"] == "this morning"
        
        # Third message
        data = agent.extract_symptom_info("It's about 6 out of 10", data)
        assert data["severity"] == 6
        
        # Fourth message
        data = agent.extract_symptom_info("For few hours now", data)
        assert data["duration"] == "few hours"
    
    def test_complete_symptom_intake_flow(self, agent):
        """Test complete symptom intake workflow"""
        data = {}
        
        # Message 1: Primary symptom
        data = agent.extract_symptom_info("I have chest pain", data)
        assert not agent.is_complete(data)
        
        # Get next question
        question = agent.get_next_question(data)
        assert question is not None
        
        # Message 2: Onset
        data = agent.extract_symptom_info("It started suddenly about 2 hours ago", data)
        assert not agent.is_complete(data)
        
        # Message 3: Duration (might be extracted with onset)
        if "duration" not in data:
            data = agent.extract_symptom_info("It's been 2 hours", data)
        
        # Message 4: Severity
        data = agent.extract_symptom_info("The pain is about 8 out of 10", data)
        
        # Should now be complete
        assert agent.is_complete(data)


class TestQuestionGeneration:
    """Test targeted question generation"""
    
    def test_get_next_question_empty_data(self, agent):
        """Test getting first question with no data"""
        question = agent.get_next_question({})
        
        assert question is not None
        assert "symptom" in question.lower()
    
    def test_get_next_question_partial_data(self, agent):
        """Test getting next question with partial data"""
        data = {"primary_symptom": "headache"}
        question = agent.get_next_question(data)
        
        assert question is not None
    
    def test_get_next_question_complete_data(self, agent):
        """Test getting question when all required fields filled"""
        data = {
            "primary_symptom": "headache",
            "onset": "this morning",
            "duration": "few hours",
            "severity": 6
        }
        
        question = agent.get_next_question(data)
        # Should return optional field question or None
        assert question is None or any(field in question.lower() for field in ["location", "where", "character", "worse", "better"])
    
    def test_targeted_question_for_headache(self, agent):
        """Test targeted questions for headache"""
        data = {"primary_symptom": "headache"}
        question = agent.get_next_question(data)
        
        assert question is not None
    
    def test_targeted_question_for_chest_pain(self, agent):
        """Test targeted questions for chest pain"""
        data = {"primary_symptom": "chest pain"}
        question = agent.get_next_question(data)
        
        assert question is not None


class TestStatusTracking:
    """Test intake status tracking"""
    
    def test_incomplete_status(self, agent):
        """Test incomplete status"""
        data = {"primary_symptom": "headache"}
        status = agent.get_intake_status(data)
        
        assert status == SymptomIntakeStatus.INCOMPLETE
    
    def test_ready_for_triage_status(self, agent):
        """Test ready for triage status"""
        data = {
            "primary_symptom": "headache",
            "onset": "this morning",
            "duration": "few hours",
            "severity": 6
        }
        status = agent.get_intake_status(data)
        
        assert status == SymptomIntakeStatus.READY_FOR_TRIAGE
    
    def test_is_complete_missing_fields(self, agent):
        """Test completion check with missing fields"""
        data = {"primary_symptom": "headache"}
        
        assert not agent.is_complete(data)
    
    def test_is_complete_all_required_fields(self, agent):
        """Test completion check with all required fields"""
        data = {
            "primary_symptom": "headache",
            "onset": "this morning",
            "duration": "few hours",
            "severity": 6
        }
        
        assert agent.is_complete(data)
    
    def test_get_missing_fields(self, agent):
        """Test getting list of missing fields"""
        data = {"primary_symptom": "headache"}
        missing = agent.get_missing_fields(data)
        
        assert "onset" in missing
        assert "duration" in missing
        assert "severity" in missing


class TestSummaryGeneration:
    """Test symptom summary generation"""
    
    def test_format_basic_summary(self, agent):
        """Test formatting basic symptom summary"""
        data = {
            "primary_symptom": "headache",
            "onset": "this morning",
            "duration": "few hours",
            "severity": 6
        }
        
        summary = agent.format_summary(data)
        
        assert "headache" in summary
        assert "this morning" in summary
        assert "6/10" in summary
    
    def test_format_detailed_summary(self, agent):
        """Test formatting detailed symptom summary"""
        data = {
            "primary_symptom": "chest pain",
            "onset": "suddenly",
            "duration": "2 hours",
            "severity": 8,
            "location": "chest center",
            "character": "crushing",
            "medications_tried": ["paracetamol"]
        }
        
        summary = agent.format_summary(data)
        
        assert "chest pain" in summary
        assert "crushing" in summary
        assert "chest center" in summary
        assert "paracetamol" in summary
    
    def test_format_summary_minimal_data(self, agent):
        """Test formatting summary with minimal data"""
        data = {"primary_symptom": "fever"}
        summary = agent.format_summary(data)
        
        assert "fever" in summary
        assert len(summary) > 0


class TestComplexScenarios:
    """Test complex real-world scenarios"""
    
    def test_nigerian_pidgin_full_flow(self, agent):
        """Test full symptom intake in Nigerian Pidgin"""
        data = {}
        
        # Message 1
        data = agent.extract_symptom_info("My belle dey pain me", data)
        assert data["primary_symptom"] == "stomach pain"
        
        # Message 2
        data = agent.extract_symptom_info("E start this morning", data)
        assert data.get("onset") == "this morning"
        
        # Message 3
        data = agent.extract_symptom_info("E dey pain me like say na 7", data)
        assert data.get("severity") == 7
    
    def test_multiple_symptoms_extraction(self, agent):
        """Test extracting multiple pieces of information at once"""
        message = "I've had a severe headache for 2 days, started suddenly, about 8 out of 10"
        data = agent.extract_symptom_info(message)
        
        assert data["primary_symptom"] == "headache"
        assert data.get("duration") == "2 days"
        # Onset can be '2 days ago' or 'suddenly' - both are acceptable
        assert data.get("onset") in ["suddenly", "2 days ago"]
        assert data.get("severity") == 8
    
    def test_emergency_chest_pain_flow(self, agent):
        """Test emergency chest pain scenario"""
        data = {}
        
        data = agent.extract_symptom_info("I have crushing chest pain in the center", data)
        assert data["primary_symptom"] == "chest pain"
        assert data.get("character") == "crushing"
        assert data.get("location") == "chest center"
        
        # Get targeted follow-up questions
        question = agent.get_next_question(data)
        assert question is not None


class TestSingletonPattern:
    """Test singleton instance management"""
    
    def test_singleton_returns_same_instance(self):
        """Test that get_symptom_intake_agent returns same instance"""
        agent1 = get_symptom_intake_agent()
        agent2 = get_symptom_intake_agent()
        
        assert agent1 is agent2
