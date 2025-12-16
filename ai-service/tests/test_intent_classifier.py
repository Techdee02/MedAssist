"""
Tests for Intent Classification Module
"""
import pytest
from app.services.intent_classifier import IntentClassifier, get_intent_classifier
from app.models.schemas import IntentType, ConversationMessage


class TestIntentClassifier:
    """Test suite for IntentClassifier"""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance for testing"""
        return IntentClassifier()
    
    def test_emergency_detection(self, classifier):
        """Test emergency keyword detection"""
        # English emergency messages
        assert classifier._detect_emergency("I have chest pain and can't breathe")
        assert classifier._detect_emergency("Someone is having a heart attack")
        assert classifier._detect_emergency("Severe bleeding, help!")
        
        # Pidgin emergency messages
        assert classifier._detect_emergency("I no fit breathe well")
        assert classifier._detect_emergency("Chest dey pain me well well")
        
        # Non-emergency messages
        assert not classifier._detect_emergency("I need an appointment")
        assert not classifier._detect_emergency("My head hurts a little")
    
    def test_appointment_booking_intent(self, classifier):
        """Test appointment booking classification"""
        messages = [
            "I need to book an appointment for next week",
            "Can I schedule a checkup?",
            "I want to see a doctor tomorrow",
            "I wan see doctor", # Pidgin
        ]
        
        for message in messages:
            result = classifier.classify(message)
            assert result.intent == IntentType.APPOINTMENT_BOOKING
            assert result.confidence > 0.7
    
    def test_medication_refill_intent(self, classifier):
        """Test medication refill classification"""
        messages = [
            "I need to refill my prescription",
            "Can I get more of my blood pressure medication?",
            "I wan refill my BP drug",  # Pidgin
            "My pills are finished",
        ]
        
        for message in messages:
            result = classifier.classify(message)
            assert result.intent == IntentType.MEDICATION_REFILL
            assert result.confidence > 0.7
    
    def test_symptom_inquiry_intent(self, classifier):
        """Test symptom inquiry classification"""
        messages = [
            "I have a headache for 2 days",
            "My stomach hurts",
            "I'm feeling sick with fever",
            "My belle dey pain me",  # Pidgin
            "Headache dey worry me",  # Pidgin
        ]
        
        for message in messages:
            result = classifier.classify(message)
            assert result.intent == IntentType.SYMPTOM_INQUIRY
            assert result.confidence > 0.7
    
    def test_emergency_intent(self, classifier):
        """Test emergency classification"""
        messages = [
            "I can't breathe properly!",
            "Having severe chest pain",
            "Someone collapsed here",
            "I no fit breathe at all",  # Pidgin
        ]
        
        for message in messages:
            result = classifier.classify(message)
            assert result.intent == IntentType.EMERGENCY
            assert result.confidence > 0.9  # High confidence for emergencies
    
    def test_feedback_complaint_intent(self, classifier):
        """Test feedback/complaint classification"""
        messages = [
            "The wait time was very long yesterday",
            "Great service, thank you!",
            "The staff was rude to me",
            "I'm satisfied with the treatment",
        ]
        
        for message in messages:
            result = classifier.classify(message)
            assert result.intent == IntentType.FEEDBACK_COMPLAINT
            assert result.confidence > 0.7
    
    def test_general_inquiry_intent(self, classifier):
        """Test general inquiry classification"""
        messages = [
            "What time do you open?",
            "Where is your clinic located?",
            "Do you accept insurance?",
            "What services do you offer?",
        ]
        
        for message in messages:
            result = classifier.classify(message)
            assert result.intent == IntentType.GENERAL_INQUIRY
            assert result.confidence > 0.5
    
    def test_with_conversation_history(self, classifier):
        """Test classification with conversation context"""
        history = [
            ConversationMessage(role="user", content="I need to see a doctor"),
            ConversationMessage(role="assistant", content="I can help you book an appointment"),
        ]
        
        result = classifier.classify("Tomorrow afternoon", conversation_history=history)
        # Should understand context (appointment booking)
        assert result.intent in [IntentType.APPOINTMENT_BOOKING, IntentType.GENERAL_INQUIRY]
    
    def test_batch_classification(self, classifier):
        """Test batch message classification"""
        messages = [
            "I need an appointment",
            "I have a headache",
            "What time do you open?",
        ]
        
        results = classifier.batch_classify(messages)
        
        assert len(results) == 3
        assert all(isinstance(r.intent, IntentType) for r in results)
        assert all(0 <= r.confidence <= 1 for r in results)
    
    def test_confidence_scores(self, classifier):
        """Test that confidence scores are in valid range"""
        messages = [
            "I need an appointment",
            "Emergency! Chest pain!",
            "Hello",
        ]
        
        for message in messages:
            result = classifier.classify(message)
            assert 0 <= result.confidence <= 1
            assert isinstance(result.confidence, float)
    
    def test_singleton_instance(self):
        """Test singleton pattern for classifier"""
        classifier1 = get_intent_classifier()
        classifier2 = get_intent_classifier()
        
        assert classifier1 is classifier2
    
    def test_empty_message(self, classifier):
        """Test handling of empty messages"""
        result = classifier.classify("")
        assert result.intent == IntentType.GENERAL_INQUIRY
        assert result.confidence > 0
    
    def test_very_long_message(self, classifier):
        """Test handling of very long messages"""
        long_message = "I need to book an appointment " * 50
        result = classifier.classify(long_message)
        assert result.intent == IntentType.APPOINTMENT_BOOKING
    
    def test_mixed_intent_message(self, classifier):
        """Test message with multiple possible intents"""
        # This message could be appointment or symptom
        message = "I have a headache, can I see a doctor tomorrow?"
        result = classifier.classify(message)
        
        # Should choose the more specific intent (appointment booking)
        assert result.intent in [IntentType.APPOINTMENT_BOOKING, IntentType.SYMPTOM_INQUIRY]
        assert result.confidence > 0.6
    
    def test_reasoning_provided(self, classifier):
        """Test that reasoning is provided for classifications"""
        result = classifier.classify("I need an appointment")
        assert result.reasoning is not None
        assert len(result.reasoning) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
