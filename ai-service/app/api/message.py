"""
Message Processing API Router

Integrates: Intent Classification, Slot Filling, Conversation Management, Safety Validation
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import Dict, Any
import uuid
import json
import re

from groq import Groq
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
        
        # Step 3: Get existing conversation state
        conversation_manager = get_conversation_manager()
        session = conversation_manager.get_session(request.patient_id)
        current_slots = session.filled_slots if session else {}
        
        # Step 4: Slot Filling (merge with existing slots)
        slot_filler = get_slot_filler()
        new_slots = slot_filler.extract_slots(
            message=request.message,
            intent=intent_result.intent,
            current_slots=current_slots
        )
        
        # Merge new slots with existing ones
        extracted_data = {**current_slots, **new_slots}
        
        logger.info(f"Extracted slots: {list(extracted_data.keys())}")
        
        # Step 5: Update Conversation Management
        conversation_manager.update_session(
            patient_id=request.patient_id,
            user_message=request.message,
            intent=intent_result.intent,
            slots=extracted_data
        )
        
        # Get missing slots
        missing_slots = slot_filler.get_missing_slots(intent_result.intent, extracted_data)
        
        # Step 6: Triage Scoring (for symptom inquiry)
        triage_level = None
        if intent_result.intent == IntentType.SYMPTOM_INQUIRY:
            symptom_intake = get_symptom_intake_agent()
            symptom_data = symptom_intake.extract_symptom_info(
                message=request.message,
                current_data={}
            )
            
            # Check if we have enough information for triage
            if symptom_intake.is_complete(symptom_data):
                triage_scorer = get_triage_scorer()
                triage_result = triage_scorer.triage(symptom_data)
                triage_level = TriageLevel(triage_result["triage_level"])
                logger.info(f"Triage level: {triage_level.value}")
        
        # Step 7: Generate Response
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
    """Generate intelligent response to collect missing slot information using LLM"""
    
    try:
        groq_client = Groq(api_key=settings.groq_api_key)
        
        prompt = f"""You are a friendly medical assistant collecting patient information for a clinic.

Intent: {intent.value}
Already collected: {json.dumps(extracted_data, indent=2)}
Still need: {', '.join(missing_slots)}

Generate a natural, empathetic question to collect the FIRST missing piece of information.

GUIDELINES:
- Ask about ONE thing at a time (the first item in the missing list)
- Be conversational and warm
- Use simple, clear language
- Consider Nigerian context (some patients speak Pidgin)
- Don't sound robotic or repetitive

EXAMPLES:
Missing "date" → "What date works best for you? You can say something like 'tomorrow' or 'next Monday'"
Missing "severity" → "On a scale of 1 to 10, how bad is the pain? (1 is very mild, 10 is the worst pain you've ever felt)"
Missing "primary_symptom" → "I'd like to help you. Can you tell me what symptoms you're experiencing?"

Return ONLY the question text, nothing else."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a compassionate medical intake assistant. Ask clear, friendly questions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"LLM response generation failed, using template: {e}")
        # Fallback to templates
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
    """Generate intelligent completion response using LLM"""
    
    try:
        groq_client = Groq(api_key=settings.groq_api_key)
        
        prompt = f"""You are a medical assistant who has finished collecting patient information.

Intent: {intent.value}
Collected information: {json.dumps(extracted_data, indent=2)}
Triage urgency: {triage_level.value if triage_level else 'not assessed'}

Generate a warm, professional closing message that:
1. Acknowledges the information received
2. Explains what happens next
3. Provides appropriate urgency guidance if triage_level is CRITICAL or HIGH
4. Reassures the patient

SAFETY RULES (CRITICAL):
- NEVER diagnose ("you have malaria", "this is typhoid")
- NEVER prescribe medication ("take paracetamol", "use this drug")
- ONLY say what the next steps are (appointment, nurse review, emergency visit)

EXAMPLES:

For CRITICAL triage:
"Thank you for sharing this information. Based on what you've described, this needs immediate medical attention. Please go to the nearest emergency room or call emergency services right away. Do not delay."

For appointment booking:
"Perfect! I've registered your appointment request for [date] at [time] for [reason]. One of our staff will confirm the details with you shortly via WhatsApp."

For symptom inquiry (LOW/MEDIUM):
"Thank you for providing these details about your symptoms. A nurse will review your case and get back to you with guidance. If your symptoms worsen, please contact us immediately."

Return ONLY the response text, nothing else."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional medical assistant. Be warm but never diagnose or prescribe."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.6,
            max_tokens=250
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"LLM completion response failed, using template: {e}")
        # Fallback to templates
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
