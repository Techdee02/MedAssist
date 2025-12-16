"""
Intent Classification Module

Identifies patient intent from messages using Llama LLM.
Supports: appointment_booking, medication_refill, symptom_inquiry, 
         feedback_complaint, general_inquiry, emergency
"""
from typing import Dict, Any, Optional, List
from loguru import logger
import json
import re
import os

from app.models.schemas import IntentType, IntentResult, ConversationMessage
from app.config import settings

# Import for Groq API
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK not available - will use rule-based fallback")


class IntentClassifier:
    """
    Classifies patient messages into predefined intents using Llama LLM
    """
    
    # Emergency keywords for immediate detection
    EMERGENCY_KEYWORDS = [
        "chest pain", "can't breathe", "can not breathe", "cannot breathe",
        "difficulty breathing", "heart attack", "stroke", "unconscious",
        "severe bleeding", "bleeding heavily", "suicide", "kill myself",
        "choking", "seizure", "collapsed", "unresponsive",
        # Nigerian Pidgin variants
        "i no fit breathe", "chest dey pain me well well", "blood dey commot plenty"
    ]
    
    def __init__(self, use_llm: bool = True, model_name: str = "llama-3.3-70b-versatile"):
        """
        Initialize the intent classifier
        
        Args:
            use_llm: Whether to use LLM via Groq API (True) or rule-based fallback (False)
            model_name: Groq model name (e.g., llama-3.3-70b-versatile, llama3-70b-8192)
        """
        self.use_llm = use_llm and GROQ_AVAILABLE
        self.groq_client = None
        self.model_name = model_name
        
        if self.use_llm:
            try:
                self._initialize_groq()
                logger.info(f"IntentClassifier initialized with Groq API: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq API: {e}. Falling back to rule-based.")
                self.use_llm = False
                logger.info("IntentClassifier initialized with rule-based fallback")
        else:
            logger.info("IntentClassifier initialized with rule-based classification")
    
    def _initialize_groq(self):
        """Initialize Groq API client"""
        logger.info(f"Initializing Groq API with model: {self.model_name}")
        
        # Get Groq API key from settings
        groq_api_key = settings.groq_api_key
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment. Get your free key at https://console.groq.com")
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=groq_api_key)
        
        logger.info("Groq API client initialized successfully")
    
    def _detect_emergency(self, message: str) -> bool:
        """
        Quick emergency detection before full classification
        
        Args:
            message: Patient's message text
            
        Returns:
            True if emergency keywords detected
        """
        message_lower = message.lower()
        for keyword in self.EMERGENCY_KEYWORDS:
            if keyword in message_lower:
                logger.warning(f"Emergency keyword detected: {keyword}")
                return True
        return False
    
    def _build_classification_prompt(
        self,
        message: str,
        conversation_history: Optional[List[ConversationMessage]] = None
    ) -> str:
        """
        Build prompt for LLM intent classification
        
        Args:
            message: Current patient message
            conversation_history: Previous messages for context
            
        Returns:
            Formatted prompt string
        """
        # Few-shot examples
        examples = """
Example 1:
Message: "I need to book an appointment for next week"
Output: {"intent": "appointment_booking", "confidence": 0.95, "reasoning": "Patient explicitly requesting appointment scheduling"}

Example 2:
Message: "My chest is hurting and I can't breathe well"
Output: {"intent": "emergency", "confidence": 0.98, "reasoning": "Life-threatening symptoms requiring immediate attention"}

Example 3:
Message: "I wan refill my BP drug"
Output: {"intent": "medication_refill", "confidence": 0.92, "reasoning": "Patient requesting prescription refill (Nigerian Pidgin)"}

Example 4:
Message: "My head dey pain me since morning"
Output: {"intent": "symptom_inquiry", "confidence": 0.94, "reasoning": "Patient reporting health symptom (headache in Pidgin)"}

Example 5:
Message: "The wait time was too long yesterday"
Output: {"intent": "feedback_complaint", "confidence": 0.90, "reasoning": "Patient providing feedback about service experience"}

Example 6:
Message: "What time do you open?"
Output: {"intent": "general_inquiry", "confidence": 0.96, "reasoning": "General question about clinic operations"}
"""
        
        # Build context from conversation history
        context = ""
        if conversation_history:
            context = "\n\nConversation History:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                context += f"{msg.role}: {msg.content}\n"
        
        prompt = f"""You are an AI assistant for a Nigerian healthcare clinic. 
Classify the patient's intent from their message.

Possible intents:
1. appointment_booking: Schedule, reschedule, or cancel appointments
2. medication_refill: Request prescription refills or medication renewals
3. symptom_inquiry: Report symptoms, health concerns, or seek medical guidance
4. feedback_complaint: Share reviews, complaints, or feedback about service
5. general_inquiry: Questions about services, hours, location, or general info
6. emergency: Urgent medical situations requiring immediate attention

Consider:
- Nigerian Pidgin English and code-switching
- Context from conversation history
- Urgency indicators
{context}

Current Message: "{message}"

Output JSON with intent, confidence (0-1), and brief reasoning:
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured format
        
        Args:
            response: Raw LLM output
            
        Returns:
            Parsed dictionary with intent, confidence, reasoning
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                # Fallback parsing
                logger.warning("Could not parse JSON from LLM response, using fallback")
                return {
                    "intent": "general_inquiry",
                    "confidence": 0.5,
                    "reasoning": "Failed to parse LLM response"
                }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "intent": "general_inquiry",
                "confidence": 0.5,
                "reasoning": "JSON parsing error"
            }
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call Groq API for Llama inference
        
        Args:
            prompt: Formatted prompt
            
        Returns:
            LLM response text
        """
        if not self.use_llm or self.groq_client is None:
            logger.warning("Groq API not available - using rule-based fallback")
            return self._rule_based_classification(prompt)
        
        try:
            logger.info("Calling Groq API for Llama inference...")
            
            # Call Groq API
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical intent classifier. Always respond with valid JSON containing intent, confidence, and reasoning fields."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model_name,
                temperature=0.1,
                max_tokens=150,
                top_p=0.95,
            )
            
            # Extract generated text
            generated_text = chat_completion.choices[0].message.content.strip()
            logger.info(f"Groq API response: {generated_text[:100]}...")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Groq API call failed: {e}. Using rule-based fallback.")
            return self._rule_based_classification(prompt)
    
    def _rule_based_classification(self, prompt: str) -> str:
        """
        Simple rule-based classification as fallback
        
        Args:
            prompt: The prompt containing the message
            
        Returns:
            JSON string with classification result
        """
        # Extract message from prompt
        message_match = re.search(r'Current Message: "(.+)"', prompt)
        if not message_match:
            return '{"intent": "general_inquiry", "confidence": 0.5, "reasoning": "Could not extract message"}'
        
        message = message_match.group(1).lower()
        
        # Emergency detection
        if self._detect_emergency(message):
            return '{"intent": "emergency", "confidence": 0.95, "reasoning": "Emergency keywords detected"}'
        
        # Appointment keywords (check before other keywords to avoid conflicts)
        appointment_keywords = ["appointment", "book", "schedule", "reschedule", "cancel", "see doctor", "see the doctor", "see a doctor", "wan see doctor", "checkup", "visit"]
        if any(kw in message for kw in appointment_keywords):
            return '{"intent": "appointment_booking", "confidence": 0.85, "reasoning": "Appointment-related keywords detected"}'
        
        # Medication keywords
        med_keywords = ["refill", "prescription", "medication", "medicine", "drug", "pills"]
        if any(kw in message for kw in med_keywords):
            return '{"intent": "medication_refill", "confidence": 0.85, "reasoning": "Medication-related keywords detected"}'
        
        # Symptom keywords
        symptom_keywords = ["pain", "hurt", "sick", "fever", "cough", "headache", "stomach", "dey pain", "belle"]
        if any(kw in message for kw in symptom_keywords):
            return '{"intent": "symptom_inquiry", "confidence": 0.80, "reasoning": "Symptom-related keywords detected"}'
        
        # Feedback keywords (but exclude if it's a question about services)
        feedback_keywords = ["wait", "long wait", "staff", "complaint", "review", "experience", "satisfied", "rude", "service", "great", "thank you", "thanks", "excellent", "poor", "good", "bad", "terrible", "wonderful"]
        # Check if it's a question (likely general inquiry)
        question_indicators = ["what", "where", "when", "how", "do you", "can you", "are you", "?"]
        is_question = any(q in message for q in question_indicators)
        
        if any(kw in message for kw in feedback_keywords) and not is_question:
            return '{"intent": "feedback_complaint", "confidence": 0.75, "reasoning": "Feedback-related keywords detected"}'
        
        # Default to general inquiry
        return '{"intent": "general_inquiry", "confidence": 0.70, "reasoning": "No specific intent pattern matched"}'
    
    def classify(
        self,
        message: str,
        conversation_history: Optional[List[ConversationMessage]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IntentResult:
        """
        Classify patient message intent
        
        Args:
            message: Patient's message text
            conversation_history: Previous conversation messages
            metadata: Additional context (language, channel, etc.)
            
        Returns:
            IntentResult with intent, confidence, reasoning
        """
        logger.info(f"Classifying message: '{message[:50]}...'")
        
        # Quick emergency check
        if self._detect_emergency(message):
            logger.warning("Emergency detected - bypassing normal classification")
            return IntentResult(
                intent=IntentType.EMERGENCY,
                confidence=0.98,
                reasoning="Emergency keywords detected in message"
            )
        
        # Build prompt
        prompt = self._build_classification_prompt(message, conversation_history)
        
        # Call LLM
        llm_response = self._call_llm(prompt)
        
        # Parse response
        parsed = self._parse_llm_response(llm_response)
        
        # Validate and convert to IntentResult
        intent_str = parsed.get("intent", "general_inquiry")
        try:
            intent = IntentType(intent_str)
        except ValueError:
            logger.error(f"Invalid intent '{intent_str}', defaulting to general_inquiry")
            intent = IntentType.GENERAL_INQUIRY
        
        confidence = float(parsed.get("confidence", 0.5))
        reasoning = parsed.get("reasoning", "No reasoning provided")
        
        result = IntentResult(
            intent=intent,
            confidence=confidence,
            reasoning=reasoning
        )
        
        logger.info(f"Classification result: {intent.value} (confidence: {confidence:.2f})")
        return result
    
    def batch_classify(
        self,
        messages: List[str]
    ) -> List[IntentResult]:
        """
        Classify multiple messages in batch
        
        Args:
            messages: List of message strings
            
        Returns:
            List of IntentResult objects
        """
        results = []
        for message in messages:
            result = self.classify(message)
            results.append(result)
        return results


# Singleton instance
_classifier_instance: Optional[IntentClassifier] = None


def get_intent_classifier(use_llm: Optional[bool] = None, model_name: Optional[str] = None) -> IntentClassifier:
    """
    Get or create singleton intent classifier instance
    
    Args:
        use_llm: Whether to use LLM. If None, uses settings.use_llm
        model_name: Hugging Face model name. If None, uses settings.model_name
    
    Returns:
        IntentClassifier instance
    """
    global _classifier_instance
    if _classifier_instance is None:
        _use_llm = use_llm if use_llm is not None else settings.use_llm
        _model_name = model_name if model_name is not None else settings.model_name
        _classifier_instance = IntentClassifier(use_llm=_use_llm, model_name=_model_name)
    return _classifier_instance
