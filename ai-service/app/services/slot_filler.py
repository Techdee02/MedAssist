"""
Slot Filling and Conversation Management Module

Extracts entities from patient messages and manages multi-turn conversations
to collect all required information for different intents.
"""
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from loguru import logger
from enum import Enum
import json
import re

from groq import Groq
from app.models.schemas import IntentType
from app.config import settings


class SlotStatus(str, Enum):
    """Status of slot filling process"""
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"
    NEEDS_CONFIRMATION = "needs_confirmation"


class SlotFiller:
    """
    Extracts entities and manages slot filling for different intents
    """
    
    # Define required slots for each intent
    INTENT_SLOTS = {
        IntentType.APPOINTMENT_BOOKING: {
            "required": ["date", "time", "reason"],
            "optional": ["doctor_name", "patient_name", "phone"]
        },
        IntentType.MEDICATION_REFILL: {
            "required": ["medication_name"],
            "optional": ["prescription_id", "pharmacy", "quantity"]
        },
        IntentType.SYMPTOM_INQUIRY: {
            "required": ["primary_symptom"],
            "optional": ["duration", "severity", "location"]
        },
        IntentType.FEEDBACK_COMPLAINT: {
            "required": ["feedback_text"],
            "optional": ["rating", "visit_date"]
        },
        IntentType.GENERAL_INQUIRY: {
            "required": ["question"],
            "optional": []
        },
        IntentType.EMERGENCY: {
            "required": ["symptoms", "location"],
            "optional": ["phone"]
        }
    }
    
    # Follow-up questions for missing slots
    SLOT_QUESTIONS = {
        "date": "What date would you like to schedule? (e.g., tomorrow, next Monday, Dec 20)",
        "time": "What time works best for you? (e.g., morning, afternoon, 2 PM)",
        "reason": "What is the reason for your visit?",
        "doctor_name": "Do you have a preferred doctor?",
        "patient_name": "May I have your full name?",
        "phone": "What's the best phone number to reach you?",
        "medication_name": "Which medication do you need to refill?",
        "prescription_id": "Do you have your prescription ID or number?",
        "pharmacy": "Which pharmacy would you like to use?",
        "quantity": "How much do you need?",
        "primary_symptom": "What symptoms are you experiencing?",
        "duration": "How long have you had these symptoms?",
        "severity": "On a scale of 1-10, how severe is it?",
        "location": "Where exactly do you feel the pain/discomfort?",
        "feedback_text": "Please share your feedback or complaint.",
        "rating": "How would you rate your experience? (1-5 stars)",
        "visit_date": "When was your visit?",
        "question": "What would you like to know?",
        "symptoms": "What symptoms are you experiencing right now?",
    }
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize slot filler
        
        Args:
            use_llm: Whether to use LLM for slot extraction (default: True)
        """
        self.use_llm = use_llm
        self.groq_client = None
        
        if self.use_llm:
            try:
                groq_api_key = settings.groq_api_key
                if groq_api_key:
                    self.groq_client = Groq(api_key=groq_api_key)
                    logger.info("SlotFiller initialized with LLM support")
                else:
                    logger.warning("GROQ_API_KEY not found, using rule-based extraction")
                    self.use_llm = False
            except Exception as e:
                logger.error(f"Failed to initialize Groq: {e}")
                self.use_llm = False
        
        if not self.use_llm:
            logger.info("SlotFiller initialized with rule-based extraction")
    
    def extract_slots(
        self,
        message: str,
        intent: IntentType,
        current_slots: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract slot values from message using LLM or rule-based fallback
        
        Args:
            message: Patient's message
            intent: Classified intent
            current_slots: Already filled slots
            
        Returns:
            Dictionary of extracted slots
        """
        if current_slots is None:
            current_slots = {}
        
        # Try LLM extraction first
        if self.use_llm and self.groq_client:
            try:
                extracted = self._extract_slots_with_llm(message, intent, current_slots)
                logger.info(f"LLM extracted slots: {extracted}")
                return extracted
            except Exception as e:
                logger.error(f"LLM extraction failed, falling back to rules: {e}")
        
        # Fallback to rule-based extraction
        message_lower = message.lower()
        extracted = {}
        
        # Extract based on intent type
        if intent == IntentType.APPOINTMENT_BOOKING:
            extracted.update(self._extract_appointment_slots(message_lower))
        elif intent == IntentType.MEDICATION_REFILL:
            extracted.update(self._extract_medication_slots(message_lower))
        elif intent == IntentType.SYMPTOM_INQUIRY:
            extracted.update(self._extract_symptom_slots(message_lower))
        elif intent == IntentType.FEEDBACK_COMPLAINT:
            extracted.update(self._extract_feedback_slots(message))
        elif intent == IntentType.GENERAL_INQUIRY:
            extracted.update(self._extract_inquiry_slots(message))
        elif intent == IntentType.EMERGENCY:
            extracted.update(self._extract_emergency_slots(message))
        
        # Merge with current slots (new values override)
        current_slots.update(extracted)
        
        logger.info(f"Rule-based extracted slots: {extracted}")
        return current_slots
    
    def _extract_slots_with_llm(
        self,
        message: str,
        intent: IntentType,
        current_slots: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to extract slots from message
        
        Args:
            message: Patient's message
            intent: Classified intent
            current_slots: Already filled slots
            
        Returns:
            Dictionary with all slots (current + newly extracted)
        """
        # Get required and optional slots for this intent
        intent_config = self.INTENT_SLOTS.get(intent, {})
        required_slots = intent_config.get("required", [])
        optional_slots = intent_config.get("optional", [])
        
        # Build prompt for LLM
        prompt = f"""You are a medical assistant extracting information from patient messages.

Intent: {intent.value}
Patient message: "{message}"

Required information to extract:
{', '.join(required_slots)}

Optional information to extract:
{', '.join(optional_slots)}

Already collected information:
{json.dumps(current_slots, indent=2)}

Extract ONLY new information from the current message. Return JSON with extracted values.
If information is already collected, include it in the response.
Use null for missing values.

Examples:
- "tomorrow at 2pm" → {{"date": "tomorrow", "time": "2pm"}}
- "I need paracetamol" → {{"medication_name": "paracetamol"}}
- "headache since yesterday" → {{"primary_symptom": "headache", "duration": "since yesterday"}}

Return ONLY valid JSON, no explanation."""

        try:
            # Call Groq API
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You extract structured medical information from patient messages. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            llm_output = response.choices[0].message.content.strip()
            logger.debug(f"LLM output: {llm_output}")
            
            # Parse JSON response
            # Remove markdown code blocks if present
            llm_output = re.sub(r'```json\s*|\s*```', '', llm_output)
            
            extracted_slots = json.loads(llm_output)
            
            # Merge with current slots (LLM output takes precedence for non-null values)
            result = {**current_slots}
            for key, value in extracted_slots.items():
                if value is not None and value != "":
                    result[key] = value
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"LLM raw output: {llm_output}")
            raise
        except Exception as e:
            logger.error(f"LLM slot extraction error: {e}")
            raise
    
    def _extract_appointment_slots(self, message: str) -> Dict[str, Any]:
        """Extract appointment-related slots"""
        slots = {}
        
        # Date detection
        date_keywords = {
            "today": "today",
            "tomorrow": "tomorrow",
            "next week": "next_week",
            "monday": "monday",
            "tuesday": "tuesday",
            "wednesday": "wednesday",
            "thursday": "thursday",
            "friday": "friday",
        }
        for keyword, value in date_keywords.items():
            if keyword in message:
                slots["date"] = value
                break
        
        # Time detection
        time_keywords = {
            "morning": "morning",
            "afternoon": "afternoon",
            "evening": "evening",
            "10": "10:00 AM",
            "11": "11:00 AM",
            "2 pm": "2:00 PM",
            "3 pm": "3:00 PM",
            "4 pm": "4:00 PM",
        }
        for keyword, value in time_keywords.items():
            if keyword in message:
                slots["time"] = value
                break
        
        # Reason detection (simple keywords)
        reason_keywords = {
            "checkup": "general checkup",
            "check up": "general checkup",
            "consultation": "consultation",
            "follow up": "follow-up visit",
            "review": "review",
            "test": "testing",
            "vaccination": "vaccination",
            "vaccine": "vaccination",
        }
        for keyword, value in reason_keywords.items():
            if keyword in message:
                slots["reason"] = value
                break
        
        return slots
    
    def _extract_medication_slots(self, message: str) -> Dict[str, Any]:
        """Extract medication refill slots"""
        slots = {}
        
        # Common medication keywords
        medication_keywords = {
            "bp": "blood pressure medication",
            "blood pressure": "blood pressure medication",
            "diabetes": "diabetes medication",
            "sugar": "diabetes medication",
            "pain": "pain medication",
            "painkiller": "pain medication",
            "antibiotic": "antibiotic",
        }
        
        for keyword, value in medication_keywords.items():
            if keyword in message:
                slots["medication_name"] = value
                break
        
        # If no keyword matched, use the whole message as medication name
        if "medication_name" not in slots and len(message.split()) <= 5:
            slots["medication_name"] = message.strip()
        
        return slots
    
    def _extract_symptom_slots(self, message: str) -> Dict[str, Any]:
        """Extract symptom-related slots"""
        slots = {}
        
        # Symptom keywords
        symptom_keywords = {
            "headache": "headache",
            "head": "headache",
            "fever": "fever",
            "cough": "cough",
            "cold": "cold",
            "stomach": "stomach pain",
            "belly": "stomach pain",
            "belle": "stomach pain",  # Pidgin
            "pain": "pain",
            "hurt": "pain",
            "sick": "general illness",
        }
        
        for keyword, value in symptom_keywords.items():
            if keyword in message:
                slots["primary_symptom"] = value
                break
        
        # Duration detection
        duration_keywords = {
            "today": "today",
            "yesterday": "since yesterday",
            "2 days": "2 days",
            "3 days": "3 days",
            "week": "about a week",
            "days": "several days",
        }
        
        for keyword, value in duration_keywords.items():
            if keyword in message:
                slots["duration"] = value
                break
        
        return slots
    
    def _extract_feedback_slots(self, message: str) -> Dict[str, Any]:
        """Extract feedback/complaint slots"""
        slots = {}
        slots["feedback_text"] = message  # Full message is the feedback
        return slots
    
    def _extract_inquiry_slots(self, message: str) -> Dict[str, Any]:
        """Extract general inquiry slots"""
        slots = {}
        slots["question"] = message  # Full message is the question
        return slots
    
    def _extract_emergency_slots(self, message: str) -> Dict[str, Any]:
        """Extract emergency slots"""
        slots = {}
        slots["symptoms"] = message  # Full message describes emergency
        return slots
    
    def get_missing_slots(
        self,
        intent: IntentType,
        filled_slots: Dict[str, Any]
    ) -> List[str]:
        """
        Get list of missing required slots
        
        Args:
            intent: Current intent
            filled_slots: Already filled slots
            
        Returns:
            List of missing slot names
        """
        if intent not in self.INTENT_SLOTS:
            return []
        
        required_slots = self.INTENT_SLOTS[intent]["required"]
        missing = [slot for slot in required_slots if slot not in filled_slots or not filled_slots[slot]]
        
        logger.info(f"Missing slots for {intent.value}: {missing}")
        return missing
    
    def get_next_question(
        self,
        intent: IntentType,
        filled_slots: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get next follow-up question for missing slots
        
        Args:
            intent: Current intent
            filled_slots: Already filled slots
            
        Returns:
            Follow-up question or None if all slots filled
        """
        missing_slots = self.get_missing_slots(intent, filled_slots)
        
        if not missing_slots:
            return None
        
        # Ask for the first missing slot
        next_slot = missing_slots[0]
        question = self.SLOT_QUESTIONS.get(
            next_slot,
            f"Could you provide information about {next_slot.replace('_', ' ')}?"
        )
        
        logger.info(f"Next question for slot '{next_slot}': {question}")
        return question
    
    def is_complete(
        self,
        intent: IntentType,
        filled_slots: Dict[str, Any]
    ) -> bool:
        """
        Check if all required slots are filled
        
        Args:
            intent: Current intent
            filled_slots: Current filled slots
            
        Returns:
            True if all required slots filled
        """
        missing = self.get_missing_slots(intent, filled_slots)
        is_complete = len(missing) == 0
        
        logger.info(f"Slot filling complete: {is_complete}")
        return is_complete
    
    def get_slot_status(
        self,
        intent: IntentType,
        filled_slots: Dict[str, Any]
    ) -> SlotStatus:
        """
        Get current status of slot filling
        
        Args:
            intent: Current intent
            filled_slots: Current filled slots
            
        Returns:
            SlotStatus enum
        """
        if self.is_complete(intent, filled_slots):
            return SlotStatus.COMPLETE
        else:
            return SlotStatus.INCOMPLETE
    
    def format_confirmation(
        self,
        intent: IntentType,
        filled_slots: Dict[str, Any]
    ) -> str:
        """
        Format a confirmation message with filled slots
        
        Args:
            intent: Current intent
            filled_slots: Filled slots
            
        Returns:
            Formatted confirmation message
        """
        if intent == IntentType.APPOINTMENT_BOOKING:
            return (
                f"Let me confirm: You want to book an appointment "
                f"on {filled_slots.get('date', 'N/A')} "
                f"at {filled_slots.get('time', 'N/A')} "
                f"for {filled_slots.get('reason', 'N/A')}. Is that correct?"
            )
        elif intent == IntentType.MEDICATION_REFILL:
            return (
                f"Let me confirm: You need a refill for "
                f"{filled_slots.get('medication_name', 'N/A')}. Is that correct?"
            )
        elif intent == IntentType.SYMPTOM_INQUIRY:
            return (
                f"You mentioned {filled_slots.get('primary_symptom', 'symptoms')} "
                f"for {filled_slots.get('duration', 'some time')}. "
                f"A healthcare provider will review this. Is there anything else?"
            )
        else:
            return "Is this information correct?"


# Singleton instance
_slot_filler_instance: Optional[SlotFiller] = None


def get_slot_filler() -> SlotFiller:
    """
    Get or create singleton slot filler instance
    
    Returns:
        SlotFiller instance
    """
    global _slot_filler_instance
    if _slot_filler_instance is None:
        _slot_filler_instance = SlotFiller()
    return _slot_filler_instance
