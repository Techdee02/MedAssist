"""
Conversation Manager Module

Manages conversation state, history, and session management
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger
import json

from app.models.schemas import IntentType, ConversationMessage


class ConversationState:
    """Represents the state of a conversation"""
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.session_id = f"session_{patient_id}_{datetime.utcnow().timestamp()}"
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.intent: Optional[IntentType] = None
        self.filled_slots: Dict[str, Any] = {}
        self.history: List[ConversationMessage] = []
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "patient_id": self.patient_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "intent": self.intent.value if self.intent else None,
            "filled_slots": self.filled_slots,
            "history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in self.history
            ],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Create from dictionary"""
        state = cls(data["patient_id"])
        state.session_id = data["session_id"]
        state.created_at = datetime.fromisoformat(data["created_at"])
        state.last_updated = datetime.fromisoformat(data["last_updated"])
        state.intent = IntentType(data["intent"]) if data.get("intent") else None
        state.filled_slots = data.get("filled_slots", {})
        
        # Reconstruct history
        state.history = [
            ConversationMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"]) if msg.get("timestamp") else None
            )
            for msg in data.get("history", [])
        ]
        
        state.metadata = data.get("metadata", {})
        return state


class ConversationManager:
    """
    Manages conversation sessions and state
    
    In production, this would use Redis for persistence.
    For now, uses in-memory storage.
    """
    
    def __init__(self, session_expiry_seconds: int = 3600):
        """
        Initialize conversation manager
        
        Args:
            session_expiry_seconds: Time until session expires (default 1 hour)
        """
        self.sessions: Dict[str, ConversationState] = {}
        self.session_expiry = timedelta(seconds=session_expiry_seconds)
        logger.info(f"ConversationManager initialized (expiry: {session_expiry_seconds}s)")
    
    def get_or_create_session(self, patient_id: str) -> ConversationState:
        """
        Get existing session or create new one
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            ConversationState object
        """
        # Clean expired sessions first
        self._cleanup_expired_sessions()
        
        if patient_id in self.sessions:
            session = self.sessions[patient_id]
            
            # Check if session expired
            if datetime.utcnow() - session.last_updated > self.session_expiry:
                logger.info(f"Session expired for patient {patient_id}, creating new one")
                session = ConversationState(patient_id)
                self.sessions[patient_id] = session
            else:
                logger.info(f"Retrieved existing session for patient {patient_id}")
        else:
            logger.info(f"Creating new session for patient {patient_id}")
            session = ConversationState(patient_id)
            self.sessions[patient_id] = session
        
        return session
    
    def update_session(
        self,
        patient_id: str,
        intent: Optional[IntentType] = None,
        slots: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        assistant_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationState:
        """
        Update session with new information
        
        Args:
            patient_id: Patient identifier
            intent: New intent (if changed)
            slots: Updated slots
            user_message: User's message to add to history
            assistant_message: Assistant's response to add to history
            metadata: Additional metadata
            
        Returns:
            Updated ConversationState
        """
        session = self.get_or_create_session(patient_id)
        
        # Update intent if provided
        if intent is not None:
            session.intent = intent
            logger.info(f"Updated intent to {intent.value}")
        
        # Update slots if provided
        if slots is not None:
            session.filled_slots.update(slots)
            logger.info(f"Updated slots: {slots}")
        
        # Add user message to history
        if user_message:
            session.history.append(
                ConversationMessage(
                    role="user",
                    content=user_message,
                    timestamp=datetime.utcnow()
                )
            )
        
        # Add assistant message to history
        if assistant_message:
            session.history.append(
                ConversationMessage(
                    role="assistant",
                    content=assistant_message,
                    timestamp=datetime.utcnow()
                )
            )
        
        # Update metadata
        if metadata:
            session.metadata.update(metadata)
        
        # Update timestamp
        session.last_updated = datetime.utcnow()
        
        return session
    
    def get_session(self, patient_id: str) -> Optional[ConversationState]:
        """
        Get existing session without creating new one
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            ConversationState or None if not found
        """
        return self.sessions.get(patient_id)
    
    def clear_session(self, patient_id: str) -> bool:
        """
        Clear/delete a session
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            True if session was deleted
        """
        if patient_id in self.sessions:
            del self.sessions[patient_id]
            logger.info(f"Cleared session for patient {patient_id}")
            return True
        return False
    
    def reset_slot_filling(self, patient_id: str) -> None:
        """
        Reset slot filling for a session (keep history)
        
        Args:
            patient_id: Patient identifier
        """
        session = self.get_session(patient_id)
        if session:
            session.filled_slots = {}
            session.intent = None
            logger.info(f"Reset slot filling for patient {patient_id}")
    
    def get_conversation_history(
        self,
        patient_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """
        Get conversation history
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of ConversationMessage objects
        """
        session = self.get_session(patient_id)
        if not session:
            return []
        
        history = session.history
        if limit:
            history = history[-limit:]
        
        return history
    
    def _cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions
        
        Returns:
            Number of sessions removed
        """
        now = datetime.utcnow()
        expired_patients = [
            patient_id
            for patient_id, session in self.sessions.items()
            if now - session.last_updated > self.session_expiry
        ]
        
        for patient_id in expired_patients:
            del self.sessions[patient_id]
        
        if expired_patients:
            logger.info(f"Cleaned up {len(expired_patients)} expired sessions")
        
        return len(expired_patients)
    
    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        self._cleanup_expired_sessions()
        return len(self.sessions)
    
    def export_session(self, patient_id: str) -> Optional[str]:
        """
        Export session as JSON string
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            JSON string or None if session not found
        """
        session = self.get_session(patient_id)
        if session:
            return json.dumps(session.to_dict(), indent=2)
        return None
    
    def import_session(self, session_json: str) -> ConversationState:
        """
        Import session from JSON string
        
        Args:
            session_json: JSON string of session data
            
        Returns:
            ConversationState object
        """
        data = json.loads(session_json)
        session = ConversationState.from_dict(data)
        self.sessions[session.patient_id] = session
        logger.info(f"Imported session for patient {session.patient_id}")
        return session


# Singleton instance
_conversation_manager_instance: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """
    Get or create singleton conversation manager instance
    
    Returns:
        ConversationManager instance
    """
    global _conversation_manager_instance
    if _conversation_manager_instance is None:
        _conversation_manager_instance = ConversationManager()
    return _conversation_manager_instance
