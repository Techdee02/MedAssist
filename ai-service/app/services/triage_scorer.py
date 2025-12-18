"""
Triage Scoring System

Assigns urgency levels to patient cases based on symptoms, vital signs, and red flags.
Uses evidence-based triage algorithms adapted for Nigerian healthcare context.
"""
from typing import Dict, Any, Optional, List
from enum import Enum
from loguru import logger
import json
import re

from groq import Groq
from app.config import settings


class TriageLevel(str, Enum):
    """Triage urgency levels"""
    CRITICAL = "critical"      # Immediate attention - life-threatening
    HIGH = "high"              # Urgent - within 1 hour
    MEDIUM = "medium"          # Semi-urgent - within 4 hours
    LOW = "low"                # Non-urgent - within 24 hours


class TriageScorer:
    """
    Scores patient cases and assigns triage levels
    """
    
    # Critical red flags requiring immediate attention
    RED_FLAGS = {
        "cardiac": [
            "chest pain", "crushing pain", "chest pressure",
            "pain radiating to arm", "pain radiating to jaw",
            "chest dey pain me well well"
        ],
        "respiratory": [
            "can't breathe", "difficulty breathing", "shortness of breath",
            "severe difficulty breathing", "i no fit breathe", "gasping"
        ],
        "neurological": [
            "stroke", "sudden weakness", "face drooping", "slurred speech",
            "sudden severe headache", "worst headache", "confused",
            "unconscious", "seizure", "convulsion", "fit"
        ],
        "bleeding": [
            "severe bleeding", "bleeding heavily", "uncontrolled bleeding",
            "blood dey commot plenty", "vomiting blood", "coughing blood"
        ],
        "trauma": [
            "severe injury", "head injury", "accident", "fall from height",
            "stabbing", "gunshot"
        ],
        "mental_health": [
            "suicide", "want to kill myself", "suicidal thoughts",
            "want to harm myself"
        ],
        "pediatric": [
            "baby not breathing", "child not responding", "baby very weak",
            "pikin no fit breathe", "high fever in baby"
        ],
        "obstetric": [
            "severe bleeding pregnant", "severe abdominal pain pregnant",
            "water broke early", "baby not moving"
        ]
    }
    
    # Moderate warning signs
    AMBER_FLAGS = {
        "infection": [
            "high fever", "fever above 39", "persistent fever",
            "severe chills", "body hot well well"
        ],
        "pain": [
            "severe pain", "pain 8/10", "pain 9/10", "pain 10/10",
            "unbearable pain", "pain dey worry me"
        ],
        "gastrointestinal": [
            "severe vomiting", "vomiting for days", "bloody stool",
            "severe diarrhea", "severe abdominal pain"
        ],
        "dehydration": [
            "very weak", "dizzy", "fainting", "no urination",
            "dry mouth", "very thirsty"
        ]
    }
    
    # Common conditions (Nigerian context)
    COMMON_CONDITIONS = {
        "malaria": ["fever", "chills", "body aches", "headache", "sweating"],
        "typhoid": ["fever", "abdominal pain", "weakness", "loss of appetite"],
        "hypertension": ["headache", "dizziness", "blurred vision"],
        "upper_respiratory": ["cough", "sore throat", "runny nose", "mild fever"]
    }
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize triage scorer
        
        Args:
            use_llm: Whether to use LLM for intelligent triage scoring
        """
        self.use_llm = use_llm
        self.groq_client = None
        
        if self.use_llm:
            try:
                groq_api_key = settings.groq_api_key
                if groq_api_key:
                    self.groq_client = Groq(api_key=groq_api_key)
                    logger.info("TriageScorer initialized with LLM support")
                else:
                    logger.warning("GROQ_API_KEY not found, using rule-based triage")
                    self.use_llm = False
            except Exception as e:
                logger.error(f"Failed to initialize Groq: {e}")
                self.use_llm = False
        
        if not self.use_llm:
            logger.info("TriageScorer initialized with rule-based triage")
    
    def calculate_score(
        self,
        symptom_data: Dict[str, Any],
        vital_signs: Optional[Dict[str, Any]] = None,
        patient_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Calculate triage score (1-10) using LLM or rule-based fallback
        
        Args:
            symptom_data: Collected symptom information
            vital_signs: Optional vital signs (temp, BP, pulse, etc.)
            patient_metadata: Optional patient info (age, conditions, etc.)
            
        Returns:
            Score from 1 (low priority) to 10 (critical)
        """
        # Try LLM scoring first
        if self.use_llm and self.groq_client:
            try:
                score = self._calculate_score_with_llm(symptom_data, vital_signs, patient_metadata)
                logger.info(f"LLM calculated triage score: {score}/10")
                return score
            except Exception as e:
                logger.error(f"LLM triage failed, falling back to rules: {e}")
        
        # Fallback to rule-based scoring
        return self._calculate_score_rule_based(symptom_data, vital_signs, patient_metadata)
    
    def _calculate_score_with_llm(
        self,
        symptom_data: Dict[str, Any],
        vital_signs: Optional[Dict[str, Any]],
        patient_metadata: Optional[Dict[str, Any]]
    ) -> int:
        """
        Use LLM to intelligently assess triage urgency
        
        Returns:
            Triage score 1-10
        """
        # Build comprehensive patient picture
        prompt = f"""You are a medical triage AI assistant. Analyze the patient's symptoms and assign a triage score from 1-10.

TRIAGE SCORING GUIDE:
- 9-10: CRITICAL - Life-threatening (chest pain, stroke, severe bleeding, can't breathe, suicide risk)
- 7-8: HIGH - Urgent care needed within 1 hour (high fever >39°C, severe pain, moderate bleeding)
- 4-6: MEDIUM - Semi-urgent, within 4 hours (persistent symptoms, moderate pain)
- 1-3: LOW - Non-urgent, within 24 hours (minor symptoms, mild pain)

PATIENT INFORMATION:
Symptoms: {json.dumps(symptom_data, indent=2)}
Vital Signs: {json.dumps(vital_signs if vital_signs else {}, indent=2)}
Patient Info: {json.dumps(patient_metadata if patient_metadata else {}, indent=2)}

CRITICAL RED FLAGS (automatic score 9-10):
- Chest pain/pressure, especially with arm/jaw pain or shortness of breath
- Difficulty breathing, can't breathe, gasping
- Stroke symptoms: sudden weakness, face drooping, slurred speech
- Severe bleeding, vomiting/coughing blood
- Loss of consciousness, seizures
- Suicidal thoughts
- Severe head injury

IMPORTANT CONTEXT:
- This is for Nigerian healthcare setting
- Consider Pidgin English expressions (e.g., "my chest dey pain me well well" = severe chest pain)
- Fever with severe symptoms (>39°C with confusion/stiff neck) = higher priority
- Sudden onset = higher priority than gradual

Return ONLY a JSON object with:
{{
  "score": <number 1-10>,
  "reasoning": "<brief explanation>",
  "urgency_category": "<critical|high|medium|low>",
  "red_flags": ["<any critical findings>"]
}}"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical triage expert. Analyze symptoms and assign appropriate urgency scores. Be conservative - when in doubt, score higher for patient safety."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Low temperature for consistent medical decisions
                max_tokens=500
            )
            
            llm_output = response.choices[0].message.content.strip()
            logger.debug(f"LLM triage output: {llm_output}")
            
            # Parse JSON
            llm_output = re.sub(r'```json\s*|\s*```', '', llm_output)
            result = json.loads(llm_output)
            
            score = int(result.get("score", 5))
            reasoning = result.get("reasoning", "")
            red_flags = result.get("red_flags", [])
            
            logger.info(f"LLM triage: score={score}, reasoning={reasoning}")
            if red_flags:
                logger.warning(f"LLM detected red flags: {red_flags}")
            
            # Ensure score is within bounds
            return max(1, min(10, score))
            
        except Exception as e:
            logger.error(f"LLM triage error: {e}")
            raise
    
    def _calculate_score_rule_based(
        self,
        symptom_data: Dict[str, Any],
        vital_signs: Optional[Dict[str, Any]],
        patient_metadata: Optional[Dict[str, Any]]
    ) -> int:
        """
        Rule-based triage scoring (fallback)
        """
        score = 0
        
        # Extract primary symptom and associated data
        primary_symptom = symptom_data.get("primary_symptom", "").lower()
        severity = symptom_data.get("severity", 0)
        character = symptom_data.get("character", "").lower()
        associated_symptoms = symptom_data.get("associated_symptoms", [])
        
        # Convert associated_symptoms to list if string
        if isinstance(associated_symptoms, str):
            associated_symptoms = [associated_symptoms.lower()]
        elif isinstance(associated_symptoms, list):
            associated_symptoms = [str(s).lower() for s in associated_symptoms]
        
        # Combine all text for red flag checking
        all_text = f"{primary_symptom} {character} {' '.join(associated_symptoms)}".lower()
        
        # Check for red flags (automatic high score)
        red_flag_category = self._check_red_flags(all_text)
        if red_flag_category:
            logger.warning(f"Red flag detected: {red_flag_category}")
            score = 10  # Maximum urgency
            return min(score, 10)
        
        # Check for amber flags (elevated score)
        amber_flag = self._check_amber_flags(all_text)
        if amber_flag:
            logger.info(f"Amber flag detected: {amber_flag}")
            score += 5
        
        # Add severity score
        if isinstance(severity, (int, float)):
            score += int(severity * 0.5)  # Severity contributes up to 5 points
        
        # Onset-based scoring (sudden onset = higher priority)
        onset = symptom_data.get("onset", "").lower()
        if any(word in onset for word in ["sudden", "suddenly", "just now", "just started"]):
            score += 2
        
        # Duration-based scoring (persistent = higher priority)
        duration = symptom_data.get("duration", "").lower()
        if any(word in duration for word in ["days", "week", "weeks", "persistent"]):
            score += 1
        
        # Vital signs scoring
        if vital_signs:
            score += self._score_vital_signs(vital_signs)
        
        # Patient metadata scoring (age, comorbidities)
        if patient_metadata:
            score += self._score_patient_metadata(patient_metadata)
        
        # Ensure score is within range
        score = max(1, min(10, score))
        
        logger.info(f"Calculated triage score: {score}/10")
        return score
    
    def _check_red_flags(self, text: str) -> Optional[str]:
        """
        Check for critical red flags
        
        Args:
            text: Combined symptom text
            
        Returns:
            Red flag category if found, None otherwise
        """
        for category, flags in self.RED_FLAGS.items():
            for flag in flags:
                if flag in text:
                    return category
        return None
    
    def _check_amber_flags(self, text: str) -> Optional[str]:
        """
        Check for moderate warning signs
        
        Args:
            text: Combined symptom text
            
        Returns:
            Amber flag category if found, None otherwise
        """
        for category, flags in self.AMBER_FLAGS.items():
            for flag in flags:
                if flag in text:
                    return category
        return None
    
    def _score_vital_signs(self, vital_signs: Dict[str, Any]) -> int:
        """
        Score based on vital signs
        
        Args:
            vital_signs: Dictionary with temp, bp, pulse, resp_rate, etc.
            
        Returns:
            Additional score points (0-3)
        """
        score = 0
        
        # Temperature
        temp = vital_signs.get("temperature")
        if temp:
            if temp >= 39.5:  # High fever
                score += 2
            elif temp >= 38.5:
                score += 1
            elif temp <= 35:  # Hypothermia
                score += 2
        
        # Blood pressure
        bp_systolic = vital_signs.get("bp_systolic")
        if bp_systolic:
            if bp_systolic >= 180:  # Hypertensive crisis
                score += 2
            elif bp_systolic <= 90:  # Hypotension
                score += 2
        
        # Heart rate
        pulse = vital_signs.get("pulse")
        if pulse:
            if pulse >= 120:  # Tachycardia
                score += 1
            elif pulse <= 50:  # Bradycardia
                score += 1
        
        # Oxygen saturation
        spo2 = vital_signs.get("spo2")
        if spo2 and spo2 < 92:  # Low oxygen
            score += 2
        
        return min(score, 3)  # Cap at 3 points
    
    def _score_patient_metadata(self, metadata: Dict[str, Any]) -> int:
        """
        Score based on patient demographics and history
        
        Args:
            metadata: Patient information
            
        Returns:
            Additional score points (0-2)
        """
        score = 0
        
        # Age considerations
        age = metadata.get("age")
        if age:
            if age < 1:  # Infant
                score += 2
            elif age < 5 or age > 65:  # Young child or elderly
                score += 1
        
        # Comorbidities
        conditions = metadata.get("chronic_conditions", [])
        if isinstance(conditions, list):
            high_risk_conditions = ["diabetes", "heart disease", "hypertension", "asthma", "copd"]
            if any(cond in str(conditions).lower() for cond in high_risk_conditions):
                score += 1
        
        # Pregnancy
        if metadata.get("pregnant"):
            score += 1
        
        return min(score, 2)  # Cap at 2 points
    
    def get_triage_level(self, score: int) -> TriageLevel:
        """
        Convert score to triage level
        
        Args:
            score: Triage score (1-10)
            
        Returns:
            TriageLevel enum
        """
        if score >= 9:
            return TriageLevel.CRITICAL
        elif score >= 6:
            return TriageLevel.HIGH
        elif score >= 3:
            return TriageLevel.MEDIUM
        else:
            return TriageLevel.LOW
    
    def get_recommended_actions(
        self,
        triage_level: TriageLevel,
        symptom_data: Dict[str, Any],
        red_flag_category: Optional[str] = None
    ) -> List[str]:
        """
        Get recommended actions based on triage level
        
        Args:
            triage_level: Assigned triage level
            symptom_data: Symptom information
            red_flag_category: If red flag detected, specify category
            
        Returns:
            List of recommended action strings
        """
        actions = []
        
        if triage_level == TriageLevel.CRITICAL:
            actions.extend([
                "🚨 IMMEDIATE ATTENTION REQUIRED",
                "Call emergency services or go to ER immediately",
                "Do not wait for appointment",
                "Alert clinical staff immediately"
            ])
            
            if red_flag_category == "cardiac":
                actions.append("Possible heart attack - call ambulance")
            elif red_flag_category == "respiratory":
                actions.append("Severe breathing difficulty - immediate intervention needed")
            elif red_flag_category == "neurological":
                actions.append("Possible stroke - time-critical intervention")
            
        elif triage_level == TriageLevel.HIGH:
            actions.extend([
                "⚠️ URGENT: Should be seen within 1 hour",
                "Fast-track for next available appointment",
                "Monitor patient closely while waiting",
                "Notify on-duty clinician"
            ])
            
        elif triage_level == TriageLevel.MEDIUM:
            actions.extend([
                "Semi-urgent: Schedule within 4 hours",
                "Standard appointment booking process",
                "Provide symptom management advice",
                "Monitor for worsening symptoms"
            ])
            
        else:  # LOW
            actions.extend([
                "Non-urgent: Can wait up to 24 hours",
                "Schedule regular appointment",
                "Provide self-care guidance",
                "Home monitoring acceptable"
            ])
        
        return actions
    
    def get_wait_time_recommendation(self, triage_level: TriageLevel) -> str:
        """
        Get recommended maximum wait time
        
        Args:
            triage_level: Triage level
            
        Returns:
            Wait time recommendation string
        """
        wait_times = {
            TriageLevel.CRITICAL: "Immediate - 0 minutes",
            TriageLevel.HIGH: "Within 1 hour",
            TriageLevel.MEDIUM: "Within 4 hours",
            TriageLevel.LOW: "Within 24 hours"
        }
        return wait_times.get(triage_level, "Unknown")
    
    def triage(
        self,
        symptom_data: Dict[str, Any],
        vital_signs: Optional[Dict[str, Any]] = None,
        patient_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete triage assessment
        
        Args:
            symptom_data: Collected symptom information
            vital_signs: Optional vital signs
            patient_metadata: Optional patient information
            
        Returns:
            Complete triage result dictionary
        """
        # Calculate score
        score = self.calculate_score(symptom_data, vital_signs, patient_metadata)
        
        # Get triage level
        triage_level = self.get_triage_level(score)
        
        # Check for red flags
        all_text = f"{symptom_data.get('primary_symptom', '')} {symptom_data.get('character', '')}".lower()
        red_flag_category = self._check_red_flags(all_text)
        
        # Get recommendations
        actions = self.get_recommended_actions(triage_level, symptom_data, red_flag_category)
        wait_time = self.get_wait_time_recommendation(triage_level)
        
        result = {
            "score": score,
            "triage_level": triage_level.value,
            "red_flag_detected": red_flag_category is not None,
            "red_flag_category": red_flag_category,
            "recommended_actions": actions,
            "max_wait_time": wait_time,
            "requires_immediate_attention": triage_level == TriageLevel.CRITICAL
        }
        
        logger.info(f"Triage complete: Level {triage_level.value}, Score {score}/10")
        return result


# Singleton instance
_triage_scorer_instance: Optional[TriageScorer] = None


def get_triage_scorer() -> TriageScorer:
    """
    Get or create singleton triage scorer instance
    
    Returns:
        TriageScorer instance
    """
    global _triage_scorer_instance
    if _triage_scorer_instance is None:
        _triage_scorer_instance = TriageScorer()
    return _triage_scorer_instance
