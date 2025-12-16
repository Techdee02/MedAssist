"""
AI Safety Guardrails for MedAssist

Prevents inappropriate medical advice, ensures transparency,
and triggers human oversight when needed.
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from loguru import logger
from datetime import datetime, timezone


class ViolationType(str, Enum):
    """Types of safety violations"""
    MEDICAL_ADVICE = "medical_advice"
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"
    DANGEROUS_ADVICE = "dangerous_advice"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    PRIVACY_VIOLATION = "privacy_violation"
    SCOPE_EXCEEDED = "scope_exceeded"


class SafetyAction(str, Enum):
    """Actions to take when safety issue detected"""
    BLOCK = "block"  # Block response completely
    WARN = "warn"  # Add warning disclaimer
    ESCALATE = "escalate"  # Trigger human review
    LOG = "log"  # Log but allow


class SafetyResult:
    """Result of safety validation"""
    
    def __init__(
        self,
        is_safe: bool,
        violations: List[ViolationType],
        action: SafetyAction,
        modified_response: Optional[str] = None,
        disclaimer: Optional[str] = None,
        reasoning: Optional[str] = None
    ):
        self.is_safe = is_safe
        self.violations = violations
        self.action = action
        self.modified_response = modified_response
        self.disclaimer = disclaimer
        self.reasoning = reasoning
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "is_safe": self.is_safe,
            "violations": [v.value for v in self.violations],
            "action": self.action.value,
            "modified_response": self.modified_response,
            "disclaimer": self.disclaimer,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat()
        }


class SafetyValidator:
    """
    Validates AI responses for safety and ethical compliance.
    
    Prevents:
    - Medical diagnosis or advice
    - Prescription recommendations
    - Dangerous health advice
    - Privacy violations
    - Scope creep beyond triage/intake
    """
    
    # Keywords that indicate medical advice/diagnosis
    DIAGNOSIS_KEYWORDS = {
        # Direct diagnosis
        "you have malaria", "you have typhoid", "you have cancer",
        "you have diabetes", "you have covid", "you have stroke",
        "you are suffering from", "you've got",
        "diagnosed with", "condition is",
        "you probably have", "likely have", "definitely have",
        
        # Nigerian Pidgin equivalents
        "your sickness na", "your problem na",
        "e be like say you get", "you don get",
        
        # Confirmatory diagnosis
        "malaria confirmed", "typhoid confirmed", "covid confirmed",
        "cancer detected", "diabetes confirmed", "symptoms confirm"
    }
    
    # Keywords indicating prescription advice
    PRESCRIPTION_KEYWORDS = {
        # Direct prescriptions
        "take this drug", "you should take", "i recommend taking",
        "prescribe", "medication for you", "drug for you",
        "take paracetamol", "take amoxicillin", "take chloroquine",
        "use this medicine", "take these tablets",
        
        # Nigerian Pidgin
        "make you take", "use this drug", "drink this medicine",
        "this drug go help you", "take am", "use am",
        
        # Specific dosage instructions
        "mg daily", "mg three times", "times a day", "times daily",
        "before meals", "after meals",
        "continue for", "days treatment", "500mg"
    }
    
    # Keywords indicating dangerous advice
    DANGEROUS_KEYWORDS = {
        # Delay seeking care
        "don't go to hospital", "no need for doctor", "wait it out",
        "it will pass", "just rest", "self-medicate",
        
        # Nigerian Pidgin
        "no go hospital", "no need doctor", "e go pass",
        "just rest small", "use local medicine",
        
        # Home remedies for serious conditions
        "treat at home", "home remedy for chest pain",
        "natural cure for", "avoid hospital"
    }
    
    # Appropriate scope - what we SHOULD do
    APPROPRIATE_PHRASES = {
        # Triage/intake only
        "i'm collecting information", "to help the clinic prepare",
        "for the doctor to review", "nurse will assess",
        "clinician will determine", "medical professional will",
        
        # Nigerian Pidgin
        "make i collect information", "make doctor fit check you",
        "nurse go check you", "medical person go see you",
        
        # Transparency
        "i'm not a doctor", "i cannot diagnose", "cannot prescribe",
        "this is not medical advice", "seek immediate care",
        "go to the hospital", "see a doctor"
    }
    
    def __init__(self):
        """Initialize safety validator"""
        self.violation_log: List[Dict] = []
        logger.info("SafetyValidator initialized")
    
    def validate_response(
        self,
        user_message: str,
        ai_response: str,
        intent: Optional[str] = None,
        triage_level: Optional[str] = None
    ) -> SafetyResult:
        """
        Validate AI response for safety issues.
        
        Args:
            user_message: User's input message
            ai_response: AI's proposed response
            intent: Detected intent (optional)
            triage_level: Triage urgency level (optional)
            
        Returns:
            SafetyResult with validation outcome
        """
        violations = []
        reasoning_parts = []
        
        # Convert to lowercase for checking
        response_lower = ai_response.lower()
        message_lower = user_message.lower()
        
        # Check for diagnosis
        if self._contains_diagnosis(response_lower):
            violations.append(ViolationType.DIAGNOSIS)
            reasoning_parts.append("Response contains diagnostic language")
        
        # Check for prescription
        if self._contains_prescription(response_lower):
            violations.append(ViolationType.PRESCRIPTION)
            reasoning_parts.append("Response suggests medication")
        
        # Check for dangerous advice
        if self._contains_dangerous_advice(response_lower):
            violations.append(ViolationType.DANGEROUS_ADVICE)
            reasoning_parts.append("Response discourages seeking medical care")
        
        # Check if scope is appropriate
        if not self._is_within_scope(response_lower):
            violations.append(ViolationType.SCOPE_EXCEEDED)
            reasoning_parts.append("Response exceeds triage/intake scope")
        
        # Determine action
        if violations:
            action = self._determine_action(violations, triage_level)
            
            # Log violation
            self._log_violation(
                user_message=user_message,
                ai_response=ai_response,
                violations=violations,
                action=action
            )
            
            # Generate safe alternative if needed
            if action == SafetyAction.BLOCK:
                safe_response = self._generate_safe_alternative(
                    user_message,
                    violations,
                    triage_level
                )
                return SafetyResult(
                    is_safe=False,
                    violations=violations,
                    action=action,
                    modified_response=safe_response,
                    disclaimer=self._get_disclaimer(),
                    reasoning=" | ".join(reasoning_parts)
                )
            
            elif action == SafetyAction.WARN:
                # Add disclaimer to response
                modified = self._add_disclaimer(ai_response)
                return SafetyResult(
                    is_safe=True,
                    violations=violations,
                    action=action,
                    modified_response=modified,
                    disclaimer=self._get_disclaimer(),
                    reasoning=" | ".join(reasoning_parts)
                )
        
        # Response is safe
        # Add standard disclaimer anyway
        modified = self._add_disclaimer(ai_response)
        return SafetyResult(
            is_safe=True,
            violations=[],
            action=SafetyAction.LOG,
            modified_response=modified,
            disclaimer=self._get_disclaimer(),
            reasoning="Response passed all safety checks"
        )
    
    def _contains_diagnosis(self, text: str) -> bool:
        """Check if text contains diagnostic language"""
        for keyword in self.DIAGNOSIS_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def _contains_prescription(self, text: str) -> bool:
        """Check if text contains prescription advice"""
        for keyword in self.PRESCRIPTION_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def _contains_dangerous_advice(self, text: str) -> bool:
        """Check if text contains dangerous medical advice"""
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def _is_within_scope(self, text: str) -> bool:
        """
        Check if response stays within appropriate scope.
        
        Appropriate: Asking questions, collecting info, directing to care
        Inappropriate: Diagnosing, prescribing, giving medical advice
        """
        # If response contains appropriate phrases, likely safe
        appropriate_count = sum(
            1 for phrase in self.APPROPRIATE_PHRASES
            if phrase in text
        )
        
        # If no violations detected and has appropriate language, OK
        if appropriate_count > 0:
            return True
        
        # Check for question patterns (appropriate)
        question_markers = ["what", "when", "where", "how", "can you", "do you", "?"]
        has_questions = any(marker in text for marker in question_markers)
        
        if has_questions and len(text.split()) < 30:
            return True  # Short question is likely safe
        
        # Otherwise, flag for review
        return False
    
    def _determine_action(
        self,
        violations: List[ViolationType],
        triage_level: Optional[str]
    ) -> SafetyAction:
        """Determine what action to take for violations"""
        
        # Critical violations - always block
        critical_violations = {
            ViolationType.PRESCRIPTION,
            ViolationType.DANGEROUS_ADVICE,
            ViolationType.DIAGNOSIS  # Block all diagnosis attempts
        }
        
        if any(v in critical_violations for v in violations):
            # Emergency diagnosis gets escalated
            if (ViolationType.DIAGNOSIS in violations and 
                triage_level == "critical"):
                return SafetyAction.ESCALATE
            return SafetyAction.BLOCK
        
        # Scope issues - warn but allow
        if ViolationType.SCOPE_EXCEEDED in violations:
            return SafetyAction.WARN
        
        # Default - warn
        return SafetyAction.WARN
    
    def _generate_safe_alternative(
        self,
        user_message: str,
        violations: List[ViolationType],
        triage_level: Optional[str]
    ) -> str:
        """Generate safe alternative response when blocking"""
        
        # Emergency case
        if triage_level == "critical":
            return (
                "I've noted your symptoms. Based on what you've shared, "
                "this requires immediate medical attention. Please go to "
                "the nearest hospital emergency room or call emergency services. "
                "I cannot provide diagnosis or treatment - only a qualified "
                "medical professional can do that.\n\n"
                "**I am not a doctor. This is not medical advice.**"
            )
        
        # Prescription request
        if ViolationType.PRESCRIPTION in violations:
            return (
                "I cannot recommend or prescribe medications. Only licensed "
                "medical professionals can prescribe drugs. Please visit the "
                "clinic so a doctor can properly assess your condition and "
                "prescribe appropriate treatment if needed.\n\n"
                "**I am not a doctor. I cannot prescribe medication.**"
            )
        
        # General diagnosis attempt
        if ViolationType.DIAGNOSIS in violations:
            return (
                "I'm here to collect information about your symptoms to help "
                "prepare for your visit with a medical professional. I cannot "
                "diagnose medical conditions - that requires examination by "
                "a qualified doctor. Would you like to schedule an appointment "
                "or should I continue collecting symptom information?\n\n"
                "**I am not a doctor. This is not a diagnosis.**"
            )
        
        # Default safe response
        return (
            "I'm an AI assistant designed to help collect symptom information "
            "for triage purposes only. I cannot provide medical advice, "
            "diagnosis, or treatment recommendations. Please consult with "
            "a qualified healthcare professional at the clinic.\n\n"
            "**I am not a doctor. Please seek professional medical care.**"
        )
    
    def _add_disclaimer(self, response: str) -> str:
        """Add transparency disclaimer to response"""
        
        # Don't add if already has disclaimer
        if "not a doctor" in response.lower():
            return response
        
        # Add subtle disclaimer at end
        disclaimer = (
            "\n\n*Note: I'm an AI assistant collecting information "
            "for clinic staff. Not medical advice.*"
        )
        
        return response + disclaimer
    
    def _get_disclaimer(self) -> str:
        """Get standard disclaimer text"""
        return (
            "This is an AI triage assistant. Information collected is for "
            "healthcare professional review only. This is not medical advice, "
            "diagnosis, or treatment. Always consult qualified medical staff."
        )
    
    def _log_violation(
        self,
        user_message: str,
        ai_response: str,
        violations: List[ViolationType],
        action: SafetyAction
    ):
        """Log safety violation for audit"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": user_message[:200],  # Truncate for privacy
            "ai_response": ai_response[:200],
            "violations": [v.value for v in violations],
            "action": action.value
        }
        
        self.violation_log.append(log_entry)
        
        logger.warning(
            f"Safety violation detected: {violations} | Action: {action.value}"
        )
    
    def get_violation_stats(self) -> Dict:
        """Get statistics on safety violations"""
        if not self.violation_log:
            return {
                "total_violations": 0,
                "by_type": {},
                "by_action": {}
            }
        
        violation_counts = {}
        action_counts = {}
        
        for entry in self.violation_log:
            # Count violations
            for v in entry["violations"]:
                violation_counts[v] = violation_counts.get(v, 0) + 1
            
            # Count actions
            action = entry["action"]
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_violations": len(self.violation_log),
            "by_type": violation_counts,
            "by_action": action_counts
        }
    
    def clear_logs(self):
        """Clear violation logs"""
        self.violation_log = []
        logger.info("Safety violation logs cleared")


# Singleton instance
_safety_validator = None


def get_safety_validator() -> SafetyValidator:
    """Get or create singleton SafetyValidator instance"""
    global _safety_validator
    if _safety_validator is None:
        _safety_validator = SafetyValidator()
    return _safety_validator
