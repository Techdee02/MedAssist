"""
Symptom Intake Agent Module

Collects detailed symptom information through targeted questioning.
Generates structured reports for healthcare providers.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from enum import Enum

from app.models.schemas import SymptomData


class SymptomIntakeStatus(str, Enum):
    """Status of symptom intake process"""
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"
    READY_FOR_TRIAGE = "ready_for_triage"


class SymptomIntakeAgent:
    """
    Manages symptom collection workflow with targeted follow-up questions
    """
    
    # Core symptom information to collect
    REQUIRED_FIELDS = [
        "primary_symptom",
        "onset",
        "duration",
        "severity"
    ]
    
    OPTIONAL_FIELDS = [
        "location",
        "character",
        "aggravating_factors",
        "relieving_factors",
        "associated_symptoms",
        "previous_episodes",
        "medications_tried"
    ]
    
    # Symptom-specific follow-up questions
    SYMPTOM_QUESTIONS = {
        "primary_symptom": "What symptoms are you experiencing?",
        "onset": "When did this start? (e.g., this morning, 2 days ago, last week)",
        "duration": "How long have you had this symptom?",
        "severity": "On a scale of 1-10, how severe is it? (1=mild, 10=worst pain imaginable)",
        "location": "Where exactly do you feel the pain/discomfort?",
        "character": "How would you describe it? (e.g., sharp, dull, throbbing, burning)",
        "aggravating_factors": "What makes it worse?",
        "relieving_factors": "What makes it better?",
        "associated_symptoms": "Are you experiencing any other symptoms along with this?",
        "previous_episodes": "Have you had this before?",
        "medications_tried": "Have you taken any medication for this? If yes, which ones?"
    }
    
    # Symptom-specific targeted questions
    TARGETED_QUESTIONS = {
        "headache": {
            "location": "Where is the headache? (front, back, sides, all over)",
            "character": "Is it sharp, throbbing, dull, or pressure-like?",
            "associated_symptoms": "Do you have nausea, vomiting, sensitivity to light, or vision changes?",
            "aggravating_factors": "Does it get worse with movement, light, or noise?"
        },
        "chest pain": {
            "location": "Where exactly in your chest?",
            "character": "Is it crushing, sharp, burning, or pressure?",
            "associated_symptoms": "Do you have shortness of breath, sweating, or arm/jaw pain?",
            "aggravating_factors": "Does it worsen with breathing, exertion, or lying down?"
        },
        "stomach pain": {
            "location": "Which part of your stomach/abdomen?",
            "character": "Is it cramping, sharp, burning, or aching?",
            "associated_symptoms": "Do you have nausea, vomiting, diarrhea, or constipation?",
            "aggravating_factors": "Does eating make it better or worse?"
        },
        "fever": {
            "severity": "How high is your temperature if measured?",
            "associated_symptoms": "Do you have chills, sweating, body aches, or fatigue?",
            "onset": "Did it come on suddenly or gradually?"
        },
        "cough": {
            "character": "Is it dry or producing mucus/phlegm?",
            "associated_symptoms": "Do you have fever, shortness of breath, or chest tightness?",
            "aggravating_factors": "Is it worse at night or when lying down?"
        }
    }
    
    def __init__(self):
        """Initialize symptom intake agent"""
        logger.info("SymptomIntakeAgent initialized")
    
    def extract_symptom_info(
        self,
        message: str,
        current_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract symptom information from patient message
        
        Args:
            message: Patient's message
            current_data: Already collected symptom data
            
        Returns:
            Updated symptom data dictionary
        """
        if current_data is None:
            current_data = {}
        
        message_lower = message.lower()
        extracted = {}
        
        # Extract primary symptom if not already set
        if "primary_symptom" not in current_data:
            extracted.update(self._extract_primary_symptom(message_lower))
        
        # Extract onset/timing
        onset = self._extract_onset(message_lower)
        if onset:
            extracted["onset"] = onset
        
        # Extract duration
        duration = self._extract_duration(message_lower)
        if duration:
            extracted["duration"] = duration
        
        # Extract severity (1-10 scale or descriptive)
        severity = self._extract_severity(message_lower)
        if severity is not None:
            extracted["severity"] = severity
        
        # Extract location
        location = self._extract_location(message_lower)
        if location:
            extracted["location"] = location
        
        # Extract character/description
        character = self._extract_character(message_lower)
        if character:
            extracted["character"] = character
        
        # Extract aggravating factors
        if any(word in message_lower for word in ["worse", "worsen", "aggravate", "trigger"]):
            extracted["aggravating_factors"] = self._extract_factors(message_lower, is_aggravating=True)
        
        # Extract relieving factors
        if any(word in message_lower for word in ["better", "relief", "help", "ease"]):
            extracted["relieving_factors"] = self._extract_factors(message_lower, is_relieving=True)
        
        # Extract medications tried
        if any(word in message_lower for word in ["took", "tried", "medication", "drug", "pill", "paracetamol", "ibuprofen"]):
            meds = self._extract_medications(message_lower)
            if meds:
                extracted["medications_tried"] = meds
        
        # Extract yes/no for previous episodes
        if any(word in message_lower for word in ["before", "previous", "again", "first time"]):
            extracted["previous_episodes"] = self._extract_previous_episodes(message_lower)
        
        # Merge with current data
        current_data.update(extracted)
        
        logger.info(f"Extracted symptom info: {extracted}")
        return current_data
    
    def _extract_primary_symptom(self, message: str) -> Dict[str, str]:
        """Extract primary symptom from message"""
        symptom_keywords = {
            "headache": ["headache", "head pain", "head dey pain", "head ache"],
            "fever": ["fever", "temperature", "hot body", "body hot"],
            "cough": ["cough", "coughing"],
            "chest pain": ["chest pain", "chest hurt", "chest dey pain"],
            "stomach pain": ["stomach pain", "belly pain", "belle pain", "belle dey pain", "abdominal pain"],
            "back pain": ["back pain", "back hurt", "back ache"],
            "sore throat": ["sore throat", "throat pain", "throat hurt"],
            "shortness of breath": ["shortness of breath", "can't breathe", "difficulty breathing", "no fit breathe"],
            "nausea": ["nausea", "feel sick", "want to vomit"],
            "vomiting": ["vomit", "vomiting", "throwing up"],
            "diarrhea": ["diarrhea", "loose stool", "running stomach"],
            "dizziness": ["dizzy", "light headed", "spinning"],
            "fatigue": ["tired", "fatigue", "weak", "weakness", "no strength"],
        }
        
        for symptom, keywords in symptom_keywords.items():
            if any(kw in message for kw in keywords):
                return {"primary_symptom": symptom}
        
        # If no keyword match, use the message as-is
        return {"primary_symptom": message.strip()}
    
    def _extract_onset(self, message: str) -> Optional[str]:
        """Extract when symptoms started"""
        onset_patterns = {
            "this morning": ["this morning", "today morning", "morning time"],
            "today": ["today", "this day"],
            "yesterday": ["yesterday", "last night"],
            "2 days ago": ["2 days", "two days", "since 2 days"],
            "3 days ago": ["3 days", "three days"],
            "this week": ["this week", "few days"],
            "last week": ["last week", "week ago"],
            "suddenly": ["sudden", "suddenly", "all of a sudden"],
            "gradually": ["gradual", "gradually", "over time"],
        }
        
        for onset, patterns in onset_patterns.items():
            if any(p in message for p in patterns):
                return onset
        
        return None
    
    def _extract_duration(self, message: str) -> Optional[str]:
        """Extract how long symptoms have lasted"""
        # Check 'for X days/hours' patterns first
        import re
        for_pattern = re.search(r'for (\d+) (day|days|hour|hours)', message)
        if for_pattern:
            num = for_pattern.group(1)
            unit = for_pattern.group(2)
            if 'day' in unit:
                return f"{num} days" if int(num) > 1 else "1 day"
            else:
                return f"{num} hours" if int(num) > 1 else "1 hour"
        
        # Check 'X days/hours' patterns (with 'been')
        been_pattern = re.search(r'been (\d+) (day|days|hour|hours)', message)
        if been_pattern:
            num = been_pattern.group(1)
            unit = been_pattern.group(2)
            if 'day' in unit:
                return f"{num} days" if int(num) > 1 else "1 day"
            else:
                return f"{num} hours" if int(num) > 1 else "1 hour"
        
        duration_patterns = {
            "few hours": ["few hours", "some hours", "hours now"],
            "all day": ["all day", "whole day", "entire day"],
            "2 days": ["2 days", "two days"],
            "3 days": ["3 days", "three days"],
            "about a week": ["week", "7 days"],
            "several days": ["several days", "many days", "days now"],
            "persistent": ["persistent", "constant", "won't stop", "not stopping"],
        }
        
        for duration, patterns in duration_patterns.items():
            if any(p in message for p in patterns):
                return duration
        
        return None
    
    def _extract_severity(self, message: str) -> Optional[int]:
        """Extract severity score"""
        # Check for numeric scale (1-10) - look for 'out of 10' or '/10' patterns first
        import re
        scale_match = re.search(r'(\d+)\s*(?:out of 10|/10)', message)
        if scale_match:
            num = int(scale_match.group(1))
            if 1 <= num <= 10:
                return num
        
        # Check for Pidgin patterns: "like say na 7", "e be like 8"
        pidgin_match = re.search(r'(?:like say na|e be like|na like)\s+(\d+)', message)
        if pidgin_match:
            num = int(pidgin_match.group(1))
            if 1 <= num <= 10:
                return num
        
        # Check for standalone numbers in severity context
        severity_context = re.search(r'(?:pain|severity|about|around|like)\s+(\d+)', message)
        if severity_context:
            num = int(severity_context.group(1))
            if 1 <= num <= 10:
                return num
        
        # Check for descriptive severity (order matters - check longer phrases first)
        severity_map = [
            ("very severe", 9),
            ("unbearable", 10),
            ("worst", 10),
            ("severe", 8),
            ("moderate", 5),
            ("medium", 5),
            ("mild", 3),
            ("little", 2),
            ("small", 2),
        ]
        
        for desc, score in severity_map:
            if desc in message:
                return score
        
        return None
    
    def _extract_location(self, message: str) -> Optional[str]:
        """Extract location of pain/discomfort"""
        location_keywords = {
            "forehead": ["forehead", "front of head"],
            "temples": ["temple", "side of head", "sides"],
            "back of head": ["back of head", "back"],
            "chest center": ["center of chest", "middle chest", "in the center", "center"],
            "left chest": ["left chest", "left side"],
            "right chest": ["right chest", "right side"],
            "upper abdomen": ["upper stomach", "upper belly", "upper abdomen"],
            "lower abdomen": ["lower stomach", "lower belly", "lower abdomen"],
            "all over": ["all over", "everywhere", "whole", "entire"],
        }
        
        for location, keywords in location_keywords.items():
            if any(kw in message for kw in keywords):
                return location
        
        return None
    
    def _extract_character(self, message: str) -> Optional[str]:
        """Extract character/quality of symptom"""
        character_keywords = [
            "sharp", "dull", "throbbing", "pulsating", "aching",
            "burning", "stabbing", "cramping", "crushing",
            "pressure", "tight", "squeezing"
        ]
        
        for char in character_keywords:
            if char in message:
                return char
        
        return None
    
    def _extract_factors(self, message: str, is_aggravating: bool = True, is_relieving: bool = False) -> List[str]:
        """Extract aggravating or relieving factors"""
        factors = []
        
        if is_relieving or not is_aggravating:
            keywords = ["rest", "lying down", "medication", "sleep", "dark room", "quiet"]
        else:
            keywords = ["movement", "exercise", "light", "noise", "eating", "lying down", "standing", "walking"]
        
        for factor in keywords:
            if factor in message:
                factors.append(factor)
        
        return factors if factors else []
    
    def _extract_medications(self, message: str) -> List[str]:
        """Extract medications tried"""
        medications = []
        med_keywords = [
            "paracetamol", "ibuprofen", "aspirin", "tylenol",
            "pain killer", "painkiller", "antibiotic"
        ]
        
        for med in med_keywords:
            if med in message:
                medications.append(med)
        
        return medications if medications else []
    
    def _extract_previous_episodes(self, message: str) -> bool:
        """Extract if patient had this before"""
        yes_indicators = ["yes", "before", "again", "previous", "happened before"]
        no_indicators = ["no", "never", "first time", "never before"]
        
        if any(ind in message for ind in yes_indicators):
            return True
        elif any(ind in message for ind in no_indicators):
            return False
        
        return False  # Default to False if unclear
    
    def get_missing_fields(self, symptom_data: Dict[str, Any]) -> List[str]:
        """
        Get list of missing required fields
        
        Args:
            symptom_data: Current symptom data
            
        Returns:
            List of missing field names
        """
        missing = [
            field for field in self.REQUIRED_FIELDS
            if field not in symptom_data or not symptom_data[field]
        ]
        
        logger.info(f"Missing fields: {missing}")
        return missing
    
    def get_next_question(
        self,
        symptom_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get next question based on missing fields and symptom type
        
        Args:
            symptom_data: Current symptom data
            
        Returns:
            Next question to ask or None if complete
        """
        # Check required fields first
        missing_required = self.get_missing_fields(symptom_data)
        
        if missing_required:
            next_field = missing_required[0]
            
            # Use targeted question if available for this symptom
            primary_symptom = symptom_data.get("primary_symptom", "").lower()
            if primary_symptom in self.TARGETED_QUESTIONS:
                symptom_questions = self.TARGETED_QUESTIONS[primary_symptom]
                if next_field in symptom_questions:
                    return symptom_questions[next_field]
            
            # Otherwise use generic question
            return self.SYMPTOM_QUESTIONS.get(next_field)
        
        # All required fields filled - ask optional questions
        for field in self.OPTIONAL_FIELDS:
            if field not in symptom_data or not symptom_data[field]:
                # Use targeted question if available
                primary_symptom = symptom_data.get("primary_symptom", "").lower()
                if primary_symptom in self.TARGETED_QUESTIONS:
                    symptom_questions = self.TARGETED_QUESTIONS[primary_symptom]
                    if field in symptom_questions:
                        return symptom_questions[field]
                
                # Use generic question
                return self.SYMPTOM_QUESTIONS.get(field)
        
        # All fields collected
        return None
    
    def is_complete(self, symptom_data: Dict[str, Any]) -> bool:
        """
        Check if symptom intake is complete
        
        Args:
            symptom_data: Current symptom data
            
        Returns:
            True if all required fields are filled
        """
        missing = self.get_missing_fields(symptom_data)
        is_complete = len(missing) == 0
        
        logger.info(f"Symptom intake complete: {is_complete}")
        return is_complete
    
    def get_intake_status(self, symptom_data: Dict[str, Any]) -> SymptomIntakeStatus:
        """
        Get current status of symptom intake
        
        Args:
            symptom_data: Current symptom data
            
        Returns:
            SymptomIntakeStatus enum
        """
        if self.is_complete(symptom_data):
            return SymptomIntakeStatus.READY_FOR_TRIAGE
        else:
            return SymptomIntakeStatus.INCOMPLETE
    
    def format_summary(self, symptom_data: Dict[str, Any]) -> str:
        """
        Format a human-readable summary of collected symptoms
        
        Args:
            symptom_data: Collected symptom data
            
        Returns:
            Formatted summary string
        """
        summary_parts = []
        
        # Primary symptom
        primary = symptom_data.get("primary_symptom", "Unknown symptom")
        summary_parts.append(f"Patient reports {primary}")
        
        # Onset
        if "onset" in symptom_data:
            summary_parts.append(f"starting {symptom_data['onset']}")
        
        # Duration
        if "duration" in symptom_data:
            summary_parts.append(f"lasting {symptom_data['duration']}")
        
        # Severity
        if "severity" in symptom_data:
            severity = symptom_data["severity"]
            if isinstance(severity, int):
                summary_parts.append(f"with severity {severity}/10")
            else:
                summary_parts.append(f"described as {severity}")
        
        # Location
        if "location" in symptom_data:
            summary_parts.append(f"located in {symptom_data['location']}")
        
        # Character
        if "character" in symptom_data:
            summary_parts.append(f"characterized as {symptom_data['character']}")
        
        # Medications tried
        if "medications_tried" in symptom_data and symptom_data["medications_tried"]:
            meds = symptom_data["medications_tried"]
            if isinstance(meds, list):
                meds_str = ", ".join(meds)
            else:
                meds_str = str(meds)
            summary_parts.append(f"Patient has tried: {meds_str}")
        
        summary = ". ".join(summary_parts) + "."
        
        logger.info(f"Generated summary: {summary}")
        return summary


# Singleton instance
_symptom_intake_agent_instance: Optional[SymptomIntakeAgent] = None


def get_symptom_intake_agent() -> SymptomIntakeAgent:
    """
    Get or create singleton symptom intake agent instance
    
    Returns:
        SymptomIntakeAgent instance
    """
    global _symptom_intake_agent_instance
    if _symptom_intake_agent_instance is None:
        _symptom_intake_agent_instance = SymptomIntakeAgent()
    return _symptom_intake_agent_instance
