"""
Tests for Slot Filling Module
"""
import pytest
from app.services.slot_filler import SlotFiller, SlotStatus, get_slot_filler
from app.models.schemas import IntentType


class TestSlotFiller:
    """Test suite for SlotFiller"""
    
    @pytest.fixture
    def slot_filler(self):
        """Create slot filler instance for testing"""
        return SlotFiller()
    
    def test_appointment_slot_extraction(self, slot_filler):
        """Test appointment slot extraction"""
        message = "I need an appointment tomorrow morning for a checkup"
        slots = slot_filler.extract_slots(message, IntentType.APPOINTMENT_BOOKING)
        
        assert "date" in slots
        assert slots["date"] == "tomorrow"
        assert "time" in slots
        assert slots["time"] == "morning"
        assert "reason" in slots
        assert "checkup" in slots["reason"]
    
    def test_medication_slot_extraction(self, slot_filler):
        """Test medication refill slot extraction"""
        message = "I need to refill my BP medication"
        slots = slot_filler.extract_slots(message, IntentType.MEDICATION_REFILL)
        
        assert "medication_name" in slots
        assert "blood pressure" in slots["medication_name"].lower()
    
    def test_symptom_slot_extraction(self, slot_filler):
        """Test symptom slot extraction"""
        message = "I have a headache for 2 days"
        slots = slot_filler.extract_slots(message, IntentType.SYMPTOM_INQUIRY)
        
        assert "primary_symptom" in slots
        assert "headache" in slots["primary_symptom"]
        assert "duration" in slots
        assert "2 days" in slots["duration"]
    
    def test_feedback_slot_extraction(self, slot_filler):
        """Test feedback slot extraction"""
        message = "The wait time was too long yesterday"
        slots = slot_filler.extract_slots(message, IntentType.FEEDBACK_COMPLAINT)
        
        assert "feedback_text" in slots
        assert slots["feedback_text"] == message
    
    def test_get_missing_slots_appointment(self, slot_filler):
        """Test missing slots identification for appointments"""
        # No slots filled
        missing = slot_filler.get_missing_slots(IntentType.APPOINTMENT_BOOKING, {})
        assert "date" in missing
        assert "time" in missing
        assert "reason" in missing
        
        # Some slots filled
        filled_slots = {"date": "tomorrow"}
        missing = slot_filler.get_missing_slots(IntentType.APPOINTMENT_BOOKING, filled_slots)
        assert "date" not in missing
        assert "time" in missing
        assert "reason" in missing
    
    def test_get_next_question(self, slot_filler):
        """Test next question generation"""
        # No slots filled - should ask for first required slot (date)
        question = slot_filler.get_next_question(IntentType.APPOINTMENT_BOOKING, {})
        assert question is not None
        assert "date" in question.lower()
        
        # Date filled - should ask for time
        filled_slots = {"date": "tomorrow"}
        question = slot_filler.get_next_question(IntentType.APPOINTMENT_BOOKING, filled_slots)
        assert question is not None
        assert "time" in question.lower()
        
        # All slots filled - should return None
        filled_slots = {"date": "tomorrow", "time": "morning", "reason": "checkup"}
        question = slot_filler.get_next_question(IntentType.APPOINTMENT_BOOKING, filled_slots)
        assert question is None
    
    def test_is_complete(self, slot_filler):
        """Test slot filling completion check"""
        # Incomplete
        filled_slots = {"date": "tomorrow"}
        assert not slot_filler.is_complete(IntentType.APPOINTMENT_BOOKING, filled_slots)
        
        # Complete
        filled_slots = {"date": "tomorrow", "time": "morning", "reason": "checkup"}
        assert slot_filler.is_complete(IntentType.APPOINTMENT_BOOKING, filled_slots)
    
    def test_get_slot_status(self, slot_filler):
        """Test slot status retrieval"""
        # Incomplete
        status = slot_filler.get_slot_status(IntentType.APPOINTMENT_BOOKING, {})
        assert status == SlotStatus.INCOMPLETE
        
        # Complete
        filled_slots = {"date": "tomorrow", "time": "morning", "reason": "checkup"}
        status = slot_filler.get_slot_status(IntentType.APPOINTMENT_BOOKING, filled_slots)
        assert status == SlotStatus.COMPLETE
    
    def test_format_confirmation(self, slot_filler):
        """Test confirmation message formatting"""
        filled_slots = {"date": "tomorrow", "time": "morning", "reason": "checkup"}
        confirmation = slot_filler.format_confirmation(IntentType.APPOINTMENT_BOOKING, filled_slots)
        
        assert "tomorrow" in confirmation
        assert "morning" in confirmation
        assert "checkup" in confirmation
        assert "confirm" in confirmation.lower()
    
    def test_incremental_slot_filling(self, slot_filler):
        """Test multi-turn slot filling"""
        # First message
        message1 = "I need an appointment"
        slots = slot_filler.extract_slots(message1, IntentType.APPOINTMENT_BOOKING)
        assert len(slots) == 0  # No specific info yet
        
        # Second message - patient provides date
        message2 = "Tomorrow"
        slots = slot_filler.extract_slots(message2, IntentType.APPOINTMENT_BOOKING, slots)
        assert "date" in slots
        assert slots["date"] == "tomorrow"
        
        # Third message - patient provides time
        message3 = "Morning"
        slots = slot_filler.extract_slots(message3, IntentType.APPOINTMENT_BOOKING, slots)
        assert "date" in slots
        assert "time" in slots
        assert slots["time"] == "morning"
        
        # Fourth message - patient provides reason
        message4 = "For a checkup"
        slots = slot_filler.extract_slots(message4, IntentType.APPOINTMENT_BOOKING, slots)
        assert "reason" in slots
        
        # Should now be complete
        assert slot_filler.is_complete(IntentType.APPOINTMENT_BOOKING, slots)
    
    def test_pidgin_slot_extraction(self, slot_filler):
        """Test slot extraction from Pidgin messages"""
        # Pidgin appointment request
        message = "I wan see doctor tomorrow"
        slots = slot_filler.extract_slots(message, IntentType.APPOINTMENT_BOOKING)
        assert "date" in slots
        
        # Pidgin symptom
        message = "My belle dey pain me"
        slots = slot_filler.extract_slots(message, IntentType.SYMPTOM_INQUIRY)
        assert "primary_symptom" in slots
    
    def test_emergency_slot_extraction(self, slot_filler):
        """Test emergency slot extraction"""
        message = "I can't breathe and have chest pain"
        slots = slot_filler.extract_slots(message, IntentType.EMERGENCY)
        
        assert "symptoms" in slots
        assert message in slots["symptoms"]
    
    def test_medication_name_extraction_variations(self, slot_filler):
        """Test various medication name formats"""
        messages = [
            ("I need my diabetes medication", "diabetes"),
            ("Refill my sugar pills", "diabetes"),
            ("My antibiotic is finished", "antibiotic"),
            ("I need more painkillers", "pain"),
        ]
        
        for message, expected_keyword in messages:
            slots = slot_filler.extract_slots(message, IntentType.MEDICATION_REFILL)
            assert "medication_name" in slots
            assert expected_keyword in slots["medication_name"].lower()
    
    def test_date_time_extraction_variations(self, slot_filler):
        """Test various date/time formats"""
        # Dates
        date_messages = [
            ("Book for today", "today"),
            ("Next Monday please", "monday"),
            ("I want next week", "next_week"),
        ]
        
        for message, expected in date_messages:
            slots = slot_filler.extract_slots(message, IntentType.APPOINTMENT_BOOKING)
            if "date" in slots:
                assert expected in slots["date"].lower()
        
        # Times
        time_messages = [
            ("In the afternoon", "afternoon"),
            ("Evening slot", "evening"),
            ("2 pm would be good", "2:00 PM"),
        ]
        
        for message, expected in time_messages:
            slots = slot_filler.extract_slots(message, IntentType.APPOINTMENT_BOOKING)
            if "time" in slots:
                assert expected in slots["time"]
    
    def test_singleton_instance(self):
        """Test singleton pattern for slot filler"""
        filler1 = get_slot_filler()
        filler2 = get_slot_filler()
        
        assert filler1 is filler2
    
    def test_empty_message_handling(self, slot_filler):
        """Test handling of empty messages"""
        slots = slot_filler.extract_slots("", IntentType.APPOINTMENT_BOOKING)
        assert isinstance(slots, dict)
    
    def test_slot_override(self, slot_filler):
        """Test that new slot values override old ones"""
        current_slots = {"date": "today", "time": "morning"}
        message = "Actually, make it tomorrow afternoon"
        
        new_slots = slot_filler.extract_slots(
            message,
            IntentType.APPOINTMENT_BOOKING,
            current_slots
        )
        
        assert new_slots["date"] == "tomorrow"
        assert new_slots["time"] == "afternoon"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
