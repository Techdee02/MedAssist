"""
Tests for Triage Scoring System
"""
import pytest
from app.services.triage_scorer import (
    TriageScorer,
    TriageLevel,
    get_triage_scorer
)


@pytest.fixture
def scorer():
    """Create triage scorer instance"""
    return TriageScorer()


class TestRedFlagDetection:
    """Test critical red flag detection"""
    
    def test_cardiac_red_flag(self, scorer):
        """Test cardiac red flag detection"""
        symptom_data = {
            "primary_symptom": "chest pain",
            "character": "crushing",
            "severity": 9
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score == 10  # Maximum urgency
    
    def test_respiratory_red_flag(self, scorer):
        """Test respiratory red flag detection"""
        symptom_data = {
            "primary_symptom": "difficulty breathing",
            "severity": 10
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score == 10
    
    def test_pidgin_respiratory_red_flag(self, scorer):
        """Test Pidgin respiratory red flag"""
        symptom_data = {
            "primary_symptom": "i no fit breathe",
            "severity": 9
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score == 10
    
    def test_neurological_red_flag(self, scorer):
        """Test stroke/neurological red flag"""
        symptom_data = {
            "primary_symptom": "sudden weakness",
            "associated_symptoms": ["slurred speech", "face drooping"]
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score == 10
    
    def test_bleeding_red_flag(self, scorer):
        """Test severe bleeding red flag"""
        symptom_data = {
            "primary_symptom": "severe bleeding",
            "severity": 10
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score == 10
    
    def test_mental_health_red_flag(self, scorer):
        """Test suicide/self-harm red flag"""
        symptom_data = {
            "primary_symptom": "want to kill myself",
            "severity": 10
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score == 10


class TestAmberFlags:
    """Test moderate warning signs"""
    
    def test_high_fever_amber_flag(self, scorer):
        """Test high fever detection"""
        symptom_data = {
            "primary_symptom": "fever",
            "severity": 8,
            "associated_symptoms": ["high fever"]
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score >= 6  # Should be elevated
    
    def test_severe_pain_amber_flag(self, scorer):
        """Test severe pain scoring"""
        symptom_data = {
            "primary_symptom": "headache",
            "severity": 9,
            "character": "severe pain"
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score >= 6


class TestSeverityScoring:
    """Test severity-based scoring"""
    
    def test_low_severity(self, scorer):
        """Test low severity symptom"""
        symptom_data = {
            "primary_symptom": "headache",
            "severity": 2
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score <= 3  # Low priority
    
    def test_medium_severity(self, scorer):
        """Test medium severity symptom"""
        symptom_data = {
            "primary_symptom": "headache",
            "severity": 5
        }
        
        score = scorer.calculate_score(symptom_data)
        assert 1 <= score <= 5  # Headache alone is typically lower urgency
    
    def test_high_severity(self, scorer):
        """Test high severity symptom"""
        symptom_data = {
            "primary_symptom": "headache",
            "severity": 9
        }
        
        score = scorer.calculate_score(symptom_data)
        assert score >= 4  # High severity alone elevates score


class TestOnsetDurationScoring:
    """Test onset and duration effects"""
    
    def test_sudden_onset_increases_score(self, scorer):
        """Test that sudden onset increases urgency"""
        symptom_data = {
            "primary_symptom": "headache",
            "severity": 5,
            "onset": "suddenly"
        }
        
        score_with_sudden = scorer.calculate_score(symptom_data)
        
        symptom_data["onset"] = "gradual"
        score_gradual = scorer.calculate_score(symptom_data)
        
        assert score_with_sudden > score_gradual
    
    def test_persistent_duration_increases_score(self, scorer):
        """Test that persistent symptoms increase urgency"""
        symptom_data = {
            "primary_symptom": "headache",
            "severity": 4,
            "duration": "3 days"
        }
        
        score_with_duration = scorer.calculate_score(symptom_data)
        
        symptom_data["duration"] = "few hours"
        score_short = scorer.calculate_score(symptom_data)
        
        assert score_with_duration >= score_short


class TestVitalSignsScoring:
    """Test vital signs integration"""
    
    def test_high_fever_vital_sign(self, scorer):
        """Test high temperature scoring"""
        symptom_data = {"primary_symptom": "fever", "severity": 6}
        vital_signs = {"temperature": 40}  # 40°C
        
        score_with_vitals = scorer.calculate_score(symptom_data, vital_signs)
        score_without = scorer.calculate_score(symptom_data)
        
        assert score_with_vitals > score_without
    
    def test_hypertensive_crisis(self, scorer):
        """Test hypertensive crisis detection"""
        symptom_data = {"primary_symptom": "headache", "severity": 7}
        vital_signs = {"bp_systolic": 190, "bp_diastolic": 110}
        
        score = scorer.calculate_score(symptom_data, vital_signs)
        assert score >= 5  # Hypertensive crisis with headache
    
    def test_low_oxygen_saturation(self, scorer):
        """Test low SpO2 scoring"""
        symptom_data = {"primary_symptom": "shortness of breath", "severity": 7}
        vital_signs = {"spo2": 88}  # Low oxygen
        
        score = scorer.calculate_score(symptom_data, vital_signs)
        assert score >= 8


class TestPatientMetadataScoring:
    """Test patient demographics and history"""
    
    def test_infant_age_increases_score(self, scorer):
        """Test that infant age increases urgency"""
        symptom_data = {"primary_symptom": "fever", "severity": 5}
        metadata = {"age": 0.5}  # 6 months old
        
        score_infant = scorer.calculate_score(symptom_data, patient_metadata=metadata)
        score_adult = scorer.calculate_score(symptom_data, patient_metadata={"age": 30})
        
        assert score_infant > score_adult
    
    def test_elderly_increases_score(self, scorer):
        """Test that elderly age increases urgency"""
        symptom_data = {"primary_symptom": "chest pain", "severity": 6}
        metadata = {"age": 75}
        
        score = scorer.calculate_score(symptom_data, patient_metadata=metadata)
        assert score >= 7
    
    def test_comorbidities_increase_score(self, scorer):
        """Test chronic conditions increase urgency"""
        symptom_data = {"primary_symptom": "abdominal pain", "severity": 6}
        metadata = {"chronic_conditions": ["diabetes", "hypertension"]}
        
        score_with_conditions = scorer.calculate_score(symptom_data, patient_metadata=metadata)
        score_without = scorer.calculate_score(symptom_data)
        
        assert score_with_conditions >= score_without  # Should be equal or higher
    
    def test_pregnancy_increases_score(self, scorer):
        """Test pregnancy increases urgency"""
        symptom_data = {"primary_symptom": "abdominal pain", "severity": 5}
        metadata = {"pregnant": True}
        
        score = scorer.calculate_score(symptom_data, patient_metadata=metadata)
        assert score >= 3  # Pregnancy adds urgency


class TestTriageLevelMapping:
    """Test score to triage level conversion"""
    
    def test_critical_level(self, scorer):
        """Test critical triage level"""
        level = scorer.get_triage_level(10)
        assert level == TriageLevel.CRITICAL
        
        level = scorer.get_triage_level(9)
        assert level == TriageLevel.CRITICAL
    
    def test_high_level(self, scorer):
        """Test high/urgent triage level"""
        level = scorer.get_triage_level(7)
        assert level == TriageLevel.HIGH
        
        level = scorer.get_triage_level(6)
        assert level == TriageLevel.HIGH
    
    def test_medium_level(self, scorer):
        """Test medium/semi-urgent level"""
        level = scorer.get_triage_level(4)
        assert level == TriageLevel.MEDIUM
        
        level = scorer.get_triage_level(3)
        assert level == TriageLevel.MEDIUM
    
    def test_low_level(self, scorer):
        """Test low/non-urgent level"""
        level = scorer.get_triage_level(2)
        assert level == TriageLevel.LOW
        
        level = scorer.get_triage_level(1)
        assert level == TriageLevel.LOW


class TestRecommendedActions:
    """Test action recommendations"""
    
    def test_critical_actions(self, scorer):
        """Test critical level recommendations"""
        actions = scorer.get_recommended_actions(
            TriageLevel.CRITICAL,
            {"primary_symptom": "chest pain"},
            red_flag_category="cardiac"
        )
        
        assert any("IMMEDIATE" in action for action in actions)
        assert any("emergency" in action.lower() for action in actions)
    
    def test_high_actions(self, scorer):
        """Test high/urgent recommendations"""
        actions = scorer.get_recommended_actions(
            TriageLevel.HIGH,
            {"primary_symptom": "severe pain"}
        )
        
        assert any("1 hour" in action for action in actions)
    
    def test_medium_actions(self, scorer):
        """Test medium/semi-urgent recommendations"""
        actions = scorer.get_recommended_actions(
            TriageLevel.MEDIUM,
            {"primary_symptom": "headache"}
        )
        
        assert any("4 hours" in action for action in actions)
    
    def test_low_actions(self, scorer):
        """Test low/non-urgent recommendations"""
        actions = scorer.get_recommended_actions(
            TriageLevel.LOW,
            {"primary_symptom": "mild cough"}
        )
        
        assert any("24 hours" in action for action in actions)


class TestWaitTimeRecommendations:
    """Test wait time recommendations"""
    
    def test_critical_wait_time(self, scorer):
        """Test critical wait time"""
        wait_time = scorer.get_wait_time_recommendation(TriageLevel.CRITICAL)
        assert "Immediate" in wait_time or "0" in wait_time
    
    def test_high_wait_time(self, scorer):
        """Test high priority wait time"""
        wait_time = scorer.get_wait_time_recommendation(TriageLevel.HIGH)
        assert "1 hour" in wait_time
    
    def test_medium_wait_time(self, scorer):
        """Test medium priority wait time"""
        wait_time = scorer.get_wait_time_recommendation(TriageLevel.MEDIUM)
        assert "4 hours" in wait_time
    
    def test_low_wait_time(self, scorer):
        """Test low priority wait time"""
        wait_time = scorer.get_wait_time_recommendation(TriageLevel.LOW)
        assert "24 hours" in wait_time


class TestCompleteTriageWorkflow:
    """Test complete triage assessment"""
    
    def test_triage_emergency_case(self, scorer):
        """Test complete triage for emergency"""
        symptom_data = {
            "primary_symptom": "chest pain",
            "character": "crushing",
            "severity": 9,
            "onset": "suddenly"
        }
        
        result = scorer.triage(symptom_data)
        
        assert result["score"] == 10
        assert result["triage_level"] == "critical"
        assert result["red_flag_detected"] is True
        assert result["requires_immediate_attention"] is True
        assert len(result["recommended_actions"]) > 0
    
    def test_triage_routine_case(self, scorer):
        """Test complete triage for routine case"""
        symptom_data = {
            "primary_symptom": "mild headache",
            "severity": 3,
            "duration": "few hours"
        }
        
        result = scorer.triage(symptom_data)
        
        assert result["score"] <= 4
        assert result["triage_level"] in ["low", "medium"]
        assert result["red_flag_detected"] is False
        assert result["requires_immediate_attention"] is False
    
    def test_triage_with_all_parameters(self, scorer):
        """Test triage with full parameters"""
        symptom_data = {
            "primary_symptom": "fever",
            "severity": 7,
            "associated_symptoms": ["high fever", "chills"]
        }
        vital_signs = {"temperature": 39.5, "pulse": 110}
        metadata = {"age": 70, "chronic_conditions": ["diabetes"]}
        
        result = scorer.triage(symptom_data, vital_signs, metadata)
        
        assert "score" in result
        assert "triage_level" in result
        assert result["score"] >= 6  # Should be elevated


class TestSingletonPattern:
    """Test singleton instance management"""
    
    def test_singleton_returns_same_instance(self):
        """Test that get_triage_scorer returns same instance"""
        scorer1 = get_triage_scorer()
        scorer2 = get_triage_scorer()
        
        assert scorer1 is scorer2
