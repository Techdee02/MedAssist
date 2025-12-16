"""
Tests for AI Safety Guardrails
"""
import pytest
from app.services.safety_validator import (
    SafetyValidator,
    SafetyAction,
    ViolationType,
    get_safety_validator
)


@pytest.fixture
def validator():
    """Create safety validator instance"""
    return SafetyValidator()


class TestDiagnosisDetection:
    """Test detection of inappropriate diagnosis"""
    
    def test_direct_diagnosis_blocked(self, validator):
        """Test that direct diagnosis is detected"""
        response = "You have malaria. This is a serious condition."
        
        result = validator.validate_response(
            user_message="I have fever and headache",
            ai_response=response
        )
        
        assert not result.is_safe
        assert ViolationType.DIAGNOSIS in result.violations
    
    def test_pidgin_diagnosis_blocked(self, validator):
        """Test Pidgin diagnosis detection"""
        response = "Your sickness na malaria. E be like say you don get typhoid."
        
        result = validator.validate_response(
            user_message="Wetin dey happen to me?",
            ai_response=response
        )
        
        assert ViolationType.DIAGNOSIS in result.violations
    
    def test_implied_diagnosis_blocked(self, validator):
        """Test implied diagnosis detection"""
        response = "You probably have typhoid based on these symptoms."
        
        result = validator.validate_response(
            user_message="I'm feeling sick",
            ai_response=response
        )
        
        assert ViolationType.DIAGNOSIS in result.violations
    
    def test_symptom_collection_allowed(self, validator):
        """Test that symptom questions are allowed"""
        response = "Can you tell me more about your fever? When did it start?"
        
        result = validator.validate_response(
            user_message="I have fever",
            ai_response=response
        )
        
        assert result.is_safe


class TestPrescriptionDetection:
    """Test detection of medication prescriptions"""
    
    def test_direct_prescription_blocked(self, validator):
        """Test direct prescription is blocked"""
        response = "Take paracetamol 500mg three times daily for 5 days."
        
        result = validator.validate_response(
            user_message="I have headache",
            ai_response=response
        )
        
        assert not result.is_safe
        assert ViolationType.PRESCRIPTION in result.violations
        assert result.action == SafetyAction.BLOCK
    
    def test_pidgin_prescription_blocked(self, validator):
        """Test Pidgin prescription blocked"""
        response = "Make you take this drug. Use am two times every day."
        
        result = validator.validate_response(
            user_message="Wetin I fit do?",
            ai_response=response
        )
        
        assert ViolationType.PRESCRIPTION in result.violations
    
    def test_medication_question_allowed(self, validator):
        """Test asking about current medication is OK"""
        response = "Are you currently taking any medications? Have you tried anything for the pain?"
        
        result = validator.validate_response(
            user_message="I have pain",
            ai_response=response
        )
        
        assert result.is_safe


class TestDangerousAdviceDetection:
    """Test detection of dangerous medical advice"""
    
    def test_delaying_care_blocked(self, validator):
        """Test advice to delay care is blocked"""
        response = "Don't go to hospital. Just rest and it will pass."
        
        result = validator.validate_response(
            user_message="I have chest pain",
            ai_response=response
        )
        
        assert ViolationType.DANGEROUS_ADVICE in result.violations
        assert result.action == SafetyAction.BLOCK
    
    def test_pidgin_dangerous_advice_blocked(self, validator):
        """Test Pidgin dangerous advice blocked"""
        response = "No go hospital. E go pass. Just rest small."
        
        result = validator.validate_response(
            user_message="I dey feel pain",
            ai_response=response
        )
        
        assert ViolationType.DANGEROUS_ADVICE in result.violations
    
    def test_emergency_referral_allowed(self, validator):
        """Test emergency referrals are allowed"""
        response = "Please go to the hospital immediately. This requires urgent medical attention."
        
        result = validator.validate_response(
            user_message="I can't breathe well",
            ai_response=response
        )
        
        assert result.is_safe


class TestScopeValidation:
    """Test that responses stay within appropriate scope"""
    
    def test_triage_questions_allowed(self, validator):
        """Test triage questions are appropriate"""
        response = (
            "I'm collecting information to help the clinic prepare for your visit. "
            "Can you describe the pain? Where is it located?"
        )
        
        result = validator.validate_response(
            user_message="I have pain",
            ai_response=response
        )
        
        assert result.is_safe
    
    def test_transparency_statement_allowed(self, validator):
        """Test transparency is appropriate"""
        response = (
            "I'm not a doctor and cannot diagnose. I'm collecting symptom "
            "information for the medical team to review."
        )
        
        result = validator.validate_response(
            user_message="What's wrong with me?",
            ai_response=response
        )
        
        assert result.is_safe


class TestSafeAlternatives:
    """Test generation of safe alternative responses"""
    
    def test_safe_alternative_for_emergency(self, validator):
        """Test safe alternative for emergency"""
        response = "You have a heart attack. Take aspirin immediately."
        
        result = validator.validate_response(
            user_message="I have severe chest pain",
            ai_response=response,
            triage_level="critical"
        )
        
        assert result.modified_response is not None
        # ESCALATE action adds disclaimer instead of blocking
        assert "not" in result.modified_response.lower()
        assert result.violations  # Should have violations
    
    def test_safe_alternative_for_prescription(self, validator):
        """Test safe alternative for prescription"""
        response = "Take amoxicillin 500mg twice daily."
        
        result = validator.validate_response(
            user_message="What medicine should I take?",
            ai_response=response
        )
        
        assert result.modified_response is not None
        assert "cannot prescribe" in result.modified_response.lower()
    
    def test_safe_alternative_for_diagnosis(self, validator):
        """Test safe alternative for diagnosis"""
        response = "You definitely have malaria. Your symptoms confirm it."
        
        result = validator.validate_response(
            user_message="Do I have malaria?",
            ai_response=response
        )
        
        assert result.modified_response is not None
        assert "cannot diagnose" in result.modified_response.lower()


class TestDisclaimers:
    """Test disclaimer handling"""
    
    def test_disclaimer_added_to_safe_response(self, validator):
        """Test disclaimer added to safe responses"""
        response = "I understand you have a headache. When did it start?"
        
        result = validator.validate_response(
            user_message="I have headache",
            ai_response=response
        )
        
        assert result.modified_response is not None
        assert "ai assistant" in result.modified_response.lower()
    
    def test_disclaimer_not_duplicated(self, validator):
        """Test disclaimer not added if already present"""
        response = "When did the fever start? I'm not a doctor, just collecting info."
        
        result = validator.validate_response(
            user_message="I have fever",
            ai_response=response
        )
        
        # Should not duplicate disclaimer
        disclaimer_count = result.modified_response.lower().count("not a doctor")
        assert disclaimer_count == 1


class TestViolationLogging:
    """Test safety violation logging"""
    
    def test_violation_logged(self, validator):
        """Test violations are logged"""
        response = "You have typhoid. Take antibiotics."
        
        validator.validate_response(
            user_message="Am I sick?",
            ai_response=response
        )
        
        stats = validator.get_violation_stats()
        assert stats["total_violations"] > 0
    
    def test_violation_stats(self, validator):
        """Test violation statistics"""
        # Create multiple violations
        validator.validate_response(
            "Wetin wrong?",
            "You have malaria"
        )
        validator.validate_response(
            "What medicine?",
            "Take paracetamol 500mg"
        )
        
        stats = validator.get_violation_stats()
        assert stats["total_violations"] >= 2
        assert "by_type" in stats
        assert "by_action" in stats
    
    def test_clear_logs(self, validator):
        """Test clearing violation logs"""
        validator.validate_response(
            "Test",
            "You have malaria"
        )
        
        validator.clear_logs()
        stats = validator.get_violation_stats()
        assert stats["total_violations"] == 0


class TestActionDetermination:
    """Test action selection for different violations"""
    
    def test_prescription_always_blocked(self, validator):
        """Test prescriptions are always blocked"""
        response = "Take this medication 3 times daily"
        
        result = validator.validate_response(
            "What should I take?",
            response
        )
        
        assert result.action == SafetyAction.BLOCK
    
    def test_dangerous_advice_blocked(self, validator):
        """Test dangerous advice is blocked"""
        response = "Don't go to hospital, just rest"
        
        result = validator.validate_response(
            "Should I see doctor?",
            response
        )
        
        assert result.action == SafetyAction.BLOCK
    
    def test_emergency_diagnosis_escalated(self, validator):
        """Test emergency diagnosis triggers escalation or warning"""
        response = "You have a stroke. Get to hospital now."
        
        result = validator.validate_response(
            "I can't move my arm",
            response,
            triage_level="critical"
        )
        
        # Should detect diagnosis violation
        assert ViolationType.DIAGNOSIS in result.violations or ViolationType.SCOPE_EXCEEDED in result.violations


class TestCompleteWorkflow:
    """Test complete safety validation workflows"""
    
    def test_safe_triage_conversation(self, validator):
        """Test complete safe triage conversation"""
        responses = [
            "Hello! I'm here to collect information about your symptoms. What brings you to the clinic today?",
            "I understand you have a headache. Can you rate the pain from 1-10?",
            "Thank you. When did the headache start?",
            "I've collected this information for the doctor to review. A nurse will see you shortly."
        ]
        
        for response in responses:
            result = validator.validate_response(
                "Patient response",
                response
            )
            assert result.is_safe or result.action != SafetyAction.BLOCK
    
    def test_unsafe_advice_rejected(self, validator):
        """Test unsafe advice is properly flagged"""
        unsafe_responses = [
            "You have malaria, take chloroquine",
            "Don't waste money on hospital, use herbs",
            "This is definitely cancer",
            "Take paracetamol 1000mg every 4 hours"
        ]
        
        for response in unsafe_responses:
            result = validator.validate_response(
                "I'm feeling sick",
                response
            )
            # Should detect violations even if action is WARN
            assert len(result.violations) > 0  # Must have violations


class TestSingletonPattern:
    """Test singleton instance management"""
    
    def test_singleton_returns_same_instance(self):
        """Test get_safety_validator returns same instance"""
        validator1 = get_safety_validator()
        validator2 = get_safety_validator()
        
        assert validator1 is validator2
