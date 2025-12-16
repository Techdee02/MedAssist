"""
Message Processing API Router

Integrates: Intent Classification, Slot Filling, Conversation Management, Safety Validation
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import Dict, Any
import uuid

from app.models.schemas import (
    ProcessMessageRequest,
    ProcessMessageResponse,
    IntentType,
    TriageLevel,
    ErrorResponse
)
from app.services.intent_classifier import get_intent_classifier
from app.services.slot_filler import get_slot_filler
from app.services.conversation_manager import get_conversation_manager
from app.services.symptom_intake import get_symptom_intake_agent
from app.services.triage_scorer import get_triage_scorer
from app.config import settings

router = APIRouter(prefix="/api/v1/message", tags=["message"])


@router.post("/process", response_model=ProcessMessageResponse)
async def process_message(request: ProcessMessageRequest):
    """
    Process patient message through AI pipeline
    
    Pipeline:
    1. Intent Classification (Groq API + Llama)
    2. Emergency Detection
    3. Slot Filling (extract entities)
    4. Conversation Management
    5. Triage Scoring (if symptom inquiry)
    6. Response Generation
    
    Args:
        request: ProcessMessageRequest with message, patient_id, history
        
    Returns:
        ProcessMessageResponse with intent, response, extracted data, next action
    """
    logger.info(f"Processing message {request.message_id} for patient {request.patient_id}")
    
    try:
        # Step 1: Intent Classification
        intent_classifier = get_intent_classifier()
        intent_result = intent_classifier.classify(
            message=request.message,
            conversation_history=request.conversation_history,
            metadata=request.metadata
        )
        
        logger.info(f"Intent classified: {intent_result.intent.value} (confidence: {intent_result.confidence:.2f})")
        
        # Step 2: Check for emergency (skip other processing if emergency)
        if intent_result.intent == IntentType.EMERGENCY:
            logger.warning("Emergency detected - immediate escalation")
            return ProcessMessageResponse(
                message_id=request.message_id,
                intent=IntentType.EMERGENCY,
                confidence=1.0,
                response=(
                    "🚨 This appears to be a medical emergency. "
                    "Please call emergency services immediately or go to the nearest hospital. "
                    "Do not wait for a callback."
                ),
                next_action="escalate",
                requires_human_review=True,
                timestamp=request.timestamp
            )
        
        # Step 3: Slot Filling
        slot_filler = get_slot_filler()
        extracted_data = slot_filler.extract_slots(
            message=request.message,
            intent=intent_result.intent
        )
        
        logger.info(f"Extracted slots: {list(extracted_data.keys())}")
        
        # Step 4: Conversation Management
        conversation_manager = get_conversation_manager()
        conversation_manager.update_session(
            patient_id=request.patient_id,
            user_message=request.message,
            intent=intent_result.intent,
            slots=extracted_data
        )
        
        # Get missing slots
        missing_slots = slot_filler.get_missing_slots(intent_result.intent, extracted_data)
        
        # Step 5: Triage Scoring (for symptom inquiry)
        triage_level = None
        if intent_result.intent == IntentType.SYMPTOM_INQUIRY:
            symptom_intake = get_symptom_intake_agent()
            symptom_data = symptom_intake.extract_symptom_info(
                message=request.message,
                existing_data={}
            )
            
            # Check if we have enough information for triage
            if symptom_intake.is_complete(symptom_data):
                triage_scorer = get_triage_scorer()
                triage_result = triage_scorer.triage(symptom_data)
                triage_level = TriageLevel(triage_result["triage_level"])
                logger.info(f"Triage level: {triage_level.value}")
        
        # Step 6: Generate Response
        if missing_slots:
            # Ask for missing information
            response_text = _generate_slot_collection_response(
                intent_result.intent,
                missing_slots,
                extracted_data
            )
            next_action = "collect_more_info"
            requires_human_review = False
            
        else:
            # All required info collected
            response_text = _generate_completion_response(
                intent_result.intent,
                extracted_data,
                triage_level
            )
            next_action = "complete"
            requires_human_review = (
                triage_level in [TriageLevel.HIGH, TriageLevel.CRITICAL]
                if triage_level else False
            )
        
        # Add assistant response to conversation
        conversation_manager.update_session(
            patient_id=request.patient_id,
            assistant_message=response_text,
            slots=extracted_data,
            metadata={"extracted_data": extracted_data}
        )
        
        return ProcessMessageResponse(
            message_id=request.message_id,
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            response=response_text,
            extracted_data=extracted_data,
            next_action=next_action,
            triage_level=triage_level,
            requires_human_review=requires_human_review,
            timestamp=request.timestamp
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


def _generate_slot_collection_response(
    intent: IntentType,
    missing_slots: list,
    extracted_data: Dict[str, Any]
) -> str:
    """Generate response to collect missing slot information"""
    
    if intent == IntentType.APPOINTMENT_BOOKING:
        if "date" in missing_slots:
            return "What date would you like to schedule your appointment?"
        if "time" in missing_slots:
            return "What time works best for you?"
        if "reason" in missing_slots:
            return "What is the reason for your visit?"
            
    elif intent == IntentType.MEDICATION_REFILL:
        if "medication_name" in missing_slots:
            return "Which medication do you need to refill?"
        if "dosage" in missing_slots:
            return "What is the dosage of your medication?"
            
    elif intent == IntentType.SYMPTOM_INQUIRY:
        if "symptom" in missing_slots:
            return "Can you describe your main symptom?"
        if "duration" in missing_slots:
            return "How long have you been experiencing this?"
        if "severity" in missing_slots:
            return "On a scale of 1-10, how severe is it?"
    
    # Generic fallback
    return f"I need a bit more information. Can you tell me more about {missing_slots[0].replace('_', ' ')}?"


def _generate_completion_response(
    intent: IntentType,
    extracted_data: Dict[str, Any],
    triage_level: TriageLevel = None
) -> str:
    """Generate completion response when all info collected"""
    
    if intent == IntentType.APPOINTMENT_BOOKING:
        date = extracted_data.get("date", "your preferred date")
        time = extracted_data.get("time", "your preferred time")
        return (
            f"I'll help you book an appointment for {date} at {time}. "
            f"A staff member will confirm your appointment shortly."
        )
        
    elif intent == IntentType.MEDICATION_REFILL:
        medication = extracted_data.get("medication_name", "your medication")
        return (
            f"I've registered your request to refill {medication}. "
            f"Our pharmacy will prepare it and contact you when ready."
        )
        
    elif intent == IntentType.SYMPTOM_INQUIRY:
        if triage_level == TriageLevel.CRITICAL:
            return (
                "⚠️ Based on your symptoms, you should seek immediate medical attention. "
                "Please visit the emergency room or call emergency services."
            )
        elif triage_level == TriageLevel.HIGH:
            return (
                "Your symptoms require prompt medical attention. "
                "We recommend scheduling an appointment today or visiting urgent care."
            )
        elif triage_level == TriageLevel.MEDIUM:
            return (
                "Thank you for sharing your symptoms. "
                "We recommend scheduling an appointment within the next few days. "
                "A healthcare provider will review your case."
            )
        else:
            return (
                "Thank you for the information. Your symptoms appear manageable. "
                "We'll have a nurse review your case and provide guidance."
            )
            
    elif intent == IntentType.FEEDBACK_COMPLAINT:
        return (
            "Thank you for your feedback. We take all comments seriously. "
            "Your feedback has been forwarded to our management team."
        )
        
    elif intent == IntentType.GENERAL_INQUIRY:
        return (
            "Thank you for your question. A staff member will get back to you "
            "with the information you requested."
        )
    
    return "Thank you for contacting us. We'll be in touch soon."
