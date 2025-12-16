"""
Tests for Conversation Manager Module
"""
import pytest
from datetime import datetime, timedelta
import time

from app.services.conversation_manager import (
    ConversationManager,
    ConversationState,
    get_conversation_manager
)
from app.models.schemas import IntentType, ConversationMessage


class TestConversationState:
    """Test suite for ConversationState"""
    
    def test_conversation_state_creation(self):
        """Test creating a conversation state"""
        state = ConversationState("patient_123")
        
        assert state.patient_id == "patient_123"
        assert state.session_id.startswith("session_patient_123")
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.last_updated, datetime)
        assert state.intent is None
        assert len(state.filled_slots) == 0
        assert len(state.history) == 0
    
    def test_to_dict_conversion(self):
        """Test converting state to dictionary"""
        state = ConversationState("patient_123")
        state.intent = IntentType.APPOINTMENT_BOOKING
        state.filled_slots = {"date": "tomorrow"}
        
        state_dict = state.to_dict()
        
        assert state_dict["patient_id"] == "patient_123"
        assert state_dict["intent"] == "appointment_booking"
        assert state_dict["filled_slots"]["date"] == "tomorrow"
    
    def test_from_dict_conversion(self):
        """Test creating state from dictionary"""
        data = {
            "patient_id": "patient_123",
            "session_id": "session_123_456",
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "intent": "appointment_booking",
            "filled_slots": {"date": "tomorrow"},
            "history": [],
            "metadata": {}
        }
        
        state = ConversationState.from_dict(data)
        
        assert state.patient_id == "patient_123"
        assert state.intent == IntentType.APPOINTMENT_BOOKING
        assert state.filled_slots["date"] == "tomorrow"


class TestConversationManager:
    """Test suite for ConversationManager"""
    
    @pytest.fixture
    def manager(self):
        """Create conversation manager for testing"""
        return ConversationManager(session_expiry_seconds=60)
    
    def test_create_new_session(self, manager):
        """Test creating a new session"""
        session = manager.get_or_create_session("patient_123")
        
        assert session.patient_id == "patient_123"
        assert len(session.history) == 0
        assert session.intent is None
    
    def test_retrieve_existing_session(self, manager):
        """Test retrieving an existing session"""
        # Create session
        session1 = manager.get_or_create_session("patient_123")
        session1.intent = IntentType.APPOINTMENT_BOOKING
        
        # Retrieve same session
        session2 = manager.get_or_create_session("patient_123")
        
        assert session1.session_id == session2.session_id
        assert session2.intent == IntentType.APPOINTMENT_BOOKING
    
    def test_update_session_intent(self, manager):
        """Test updating session intent"""
        manager.get_or_create_session("patient_123")
        
        updated = manager.update_session(
            "patient_123",
            intent=IntentType.APPOINTMENT_BOOKING
        )
        
        assert updated.intent == IntentType.APPOINTMENT_BOOKING
    
    def test_update_session_slots(self, manager):
        """Test updating session slots"""
        manager.get_or_create_session("patient_123")
        
        updated = manager.update_session(
            "patient_123",
            slots={"date": "tomorrow", "time": "morning"}
        )
        
        assert updated.filled_slots["date"] == "tomorrow"
        assert updated.filled_slots["time"] == "morning"
    
    def test_update_session_messages(self, manager):
        """Test adding messages to session history"""
        manager.get_or_create_session("patient_123")
        
        updated = manager.update_session(
            "patient_123",
            user_message="I need an appointment",
            assistant_message="Sure, what date works for you?"
        )
        
        assert len(updated.history) == 2
        assert updated.history[0].role == "user"
        assert updated.history[0].content == "I need an appointment"
        assert updated.history[1].role == "assistant"
    
    def test_get_conversation_history(self, manager):
        """Test retrieving conversation history"""
        manager.get_or_create_session("patient_123")
        
        manager.update_session(
            "patient_123",
            user_message="Hello",
            assistant_message="Hi! How can I help?"
        )
        
        manager.update_session(
            "patient_123",
            user_message="I need an appointment"
        )
        
        history = manager.get_conversation_history("patient_123")
        
        assert len(history) == 3
        assert history[0].content == "Hello"
        assert history[1].content == "Hi! How can I help?"
        assert history[2].content == "I need an appointment"
    
    def test_get_conversation_history_with_limit(self, manager):
        """Test retrieving limited conversation history"""
        manager.get_or_create_session("patient_123")
        
        for i in range(10):
            manager.update_session(
                "patient_123",
                user_message=f"Message {i}"
            )
        
        history = manager.get_conversation_history("patient_123", limit=5)
        
        assert len(history) == 5
        assert history[-1].content == "Message 9"  # Last message
    
    def test_clear_session(self, manager):
        """Test clearing a session"""
        manager.get_or_create_session("patient_123")
        assert manager.get_session("patient_123") is not None
        
        result = manager.clear_session("patient_123")
        
        assert result is True
        assert manager.get_session("patient_123") is None
    
    def test_reset_slot_filling(self, manager):
        """Test resetting slot filling while keeping history"""
        session = manager.get_or_create_session("patient_123")
        
        manager.update_session(
            "patient_123",
            intent=IntentType.APPOINTMENT_BOOKING,
            slots={"date": "tomorrow"},
            user_message="I need an appointment"
        )
        
        manager.reset_slot_filling("patient_123")
        
        session = manager.get_session("patient_123")
        assert len(session.filled_slots) == 0
        assert session.intent is None
        assert len(session.history) > 0  # History preserved
    
    def test_session_expiry(self):
        """Test session expiration"""
        # Create manager with 1 second expiry
        manager = ConversationManager(session_expiry_seconds=1)
        
        session = manager.get_or_create_session("patient_123")
        original_session_id = session.session_id
        
        # Wait for expiry
        time.sleep(1.1)
        
        # Try to get session again - should create new one
        new_session = manager.get_or_create_session("patient_123")
        
        assert new_session.session_id != original_session_id
    
    def test_multiple_patients(self, manager):
        """Test managing multiple patient sessions"""
        session1 = manager.get_or_create_session("patient_1")
        session2 = manager.get_or_create_session("patient_2")
        session3 = manager.get_or_create_session("patient_3")
        
        manager.update_session("patient_1", intent=IntentType.APPOINTMENT_BOOKING)
        manager.update_session("patient_2", intent=IntentType.MEDICATION_REFILL)
        manager.update_session("patient_3", intent=IntentType.SYMPTOM_INQUIRY)
        
        # Verify sessions are independent
        s1 = manager.get_session("patient_1")
        s2 = manager.get_session("patient_2")
        s3 = manager.get_session("patient_3")
        
        assert s1.intent == IntentType.APPOINTMENT_BOOKING
        assert s2.intent == IntentType.MEDICATION_REFILL
        assert s3.intent == IntentType.SYMPTOM_INQUIRY
    
    def test_get_active_sessions_count(self, manager):
        """Test counting active sessions"""
        assert manager.get_active_sessions_count() == 0
        
        manager.get_or_create_session("patient_1")
        manager.get_or_create_session("patient_2")
        manager.get_or_create_session("patient_3")
        
        assert manager.get_active_sessions_count() == 3
        
        manager.clear_session("patient_1")
        
        assert manager.get_active_sessions_count() == 2
    
    def test_export_import_session(self, manager):
        """Test exporting and importing session"""
        # Create and populate session
        manager.get_or_create_session("patient_123")
        manager.update_session(
            "patient_123",
            intent=IntentType.APPOINTMENT_BOOKING,
            slots={"date": "tomorrow", "time": "morning"},
            user_message="I need an appointment",
            assistant_message="Sure, what date?"
        )
        
        # Export
        session_json = manager.export_session("patient_123")
        assert session_json is not None
        
        # Clear session
        manager.clear_session("patient_123")
        assert manager.get_session("patient_123") is None
        
        # Import
        imported_session = manager.import_session(session_json)
        
        assert imported_session.patient_id == "patient_123"
        assert imported_session.intent == IntentType.APPOINTMENT_BOOKING
        assert imported_session.filled_slots["date"] == "tomorrow"
        assert len(imported_session.history) == 2
    
    def test_metadata_storage(self, manager):
        """Test storing custom metadata"""
        manager.get_or_create_session("patient_123")
        
        manager.update_session(
            "patient_123",
            metadata={
                "language": "pidgin",
                "channel": "whatsapp",
                "priority": "high"
            }
        )
        
        session = manager.get_session("patient_123")
        assert session.metadata["language"] == "pidgin"
        assert session.metadata["channel"] == "whatsapp"
        assert session.metadata["priority"] == "high"
    
    def test_incremental_metadata_update(self, manager):
        """Test updating metadata incrementally"""
        manager.get_or_create_session("patient_123")
        
        manager.update_session("patient_123", metadata={"key1": "value1"})
        manager.update_session("patient_123", metadata={"key2": "value2"})
        
        session = manager.get_session("patient_123")
        assert session.metadata["key1"] == "value1"
        assert session.metadata["key2"] == "value2"
    
    def test_singleton_instance(self):
        """Test singleton pattern for conversation manager"""
        manager1 = get_conversation_manager()
        manager2 = get_conversation_manager()
        
        assert manager1 is manager2
    
    def test_get_nonexistent_session(self, manager):
        """Test getting a session that doesn't exist"""
        session = manager.get_session("nonexistent_patient")
        assert session is None
    
    def test_clear_nonexistent_session(self, manager):
        """Test clearing a session that doesn't exist"""
        result = manager.clear_session("nonexistent_patient")
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
