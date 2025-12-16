"""
Symptom Report API Router

Generates comprehensive medical reports from symptom data
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
import uuid
from datetime import datetime

from app.models.schemas import (
    GenerateSymptomReportRequest,
    SymptomReport,
    SymptomData,
    TriageLevel,
    IntentType,
    ErrorResponse
)
from app.services.symptom_intake import get_symptom_intake_agent
from app.services.triage_scorer import get_triage_scorer
from app.services.report_generator import get_report_generator

router = APIRouter(prefix="/api/v1/symptom", tags=["symptom"])


@router.post("/report", response_model=SymptomReport)
async def generate_symptom_report(request: GenerateSymptomReportRequest):
    """
    Generate comprehensive symptom report
    
    Pipeline:
    1. Validate symptom data completeness
    2. Calculate triage score
    3. Identify red flags
    4. Generate structured report
    5. Create human-readable summary
    
    Args:
        request: GenerateSymptomReportRequest with patient_id and symptom data
        
    Returns:
        SymptomReport with structured data, summary, triage level, recommendations
    """
    logger.info(f"Generating symptom report for patient {request.patient_id}")
    
    try:
        # Convert SymptomData to dict for processing
        symptom_data = {
            "primary_symptom": request.conversation_data.primary_symptom,
            "onset": request.conversation_data.onset,
            "duration": request.conversation_data.duration,
            "severity": request.conversation_data.severity,
            "location": request.conversation_data.location,
            "character": request.conversation_data.character,
            "aggravating_factors": request.conversation_data.aggravating_factors or [],
            "relieving_factors": request.conversation_data.relieving_factors or [],
            "associated_symptoms": request.conversation_data.associated_symptoms or [],
            "previous_episodes": request.conversation_data.previous_episodes,
            "medications_tried": request.conversation_data.medications_tried or []
        }
        
        # Step 1: Validate completeness
        symptom_intake = get_symptom_intake_agent()
        is_data_complete = symptom_intake.is_complete(symptom_data)
        missing_fields = symptom_intake.get_missing_fields(symptom_data)
        
        if not is_data_complete:
            logger.warning(f"Incomplete symptom data. Missing fields: {missing_fields}")
            # Still generate report but flag it
        
        # Step 2: Calculate triage score
        triage_scorer = get_triage_scorer()
        triage_result = triage_scorer.triage(symptom_data)
        
        triage_level = TriageLevel(triage_result["triage_level"])
        urgency_score = triage_result["score"]
        red_flags = [triage_result["red_flag_category"]] if triage_result.get("red_flag_category") else []
        
        logger.info(f"Triage: {triage_level.value}, Score: {urgency_score}, Red flags: {len(red_flags)}")
        
        # Step 3: Generate structured report
        report_generator = get_report_generator()
        report_data = report_generator.generate_report(
            patient_id=request.patient_id,
            intent=IntentType.SYMPTOM_INQUIRY,
            symptom_data=symptom_data,
            triage_result=triage_result,
            conversation_history=[],
            safety_issues=red_flags if red_flags else None
        )
        
        # Step 4: Create human summary
        human_summary = _generate_human_summary(
            symptom_data=symptom_data,
            triage_level=triage_level,
            urgency_score=urgency_score,
            red_flags=red_flags
        )
        
        # Step 5: Determine recommended action
        recommended_action = _get_recommended_action(triage_level, urgency_score)
        
        report_id = str(uuid.uuid4())
        
        return SymptomReport(
            report_id=report_id,
            patient_id=request.patient_id,
            structured_report=report_data,
            human_summary=human_summary,
            triage_level=triage_level,
            urgency_score=urgency_score,
            red_flags=red_flags,
            recommended_action=recommended_action,
            requires_immediate_attention=(triage_level in [TriageLevel.HIGH, TriageLevel.CRITICAL]),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error generating symptom report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate symptom report: {str(e)}"
        )


def _generate_human_summary(
    symptom_data: dict,
    triage_level: TriageLevel,
    urgency_score: int,
    red_flags: list
) -> str:
    """Generate human-readable summary of symptom report"""
    
    primary = symptom_data.get("primary_symptom", "unspecified symptom")
    duration = symptom_data.get("duration", "unknown duration")
    severity = symptom_data.get("severity", "unknown severity")
    location = symptom_data.get("location", "")
    
    summary = f"Patient presents with {primary}"
    
    if location:
        summary += f" in the {location}"
    
    summary += f", ongoing for {duration}"
    
    if isinstance(severity, int):
        summary += f" with severity rated {severity}/10"
    
    summary += "."
    
    # Add associated symptoms
    associated = symptom_data.get("associated_symptoms", [])
    if associated:
        summary += f" Associated symptoms include: {', '.join(associated)}."
    
    # Add aggravating/relieving factors
    aggravating = symptom_data.get("aggravating_factors", [])
    if aggravating:
        summary += f" Worsened by: {', '.join(aggravating)}."
    
    relieving = symptom_data.get("relieving_factors", [])
    if relieving:
        summary += f" Relieved by: {', '.join(relieving)}."
    
    # Add triage assessment
    summary += f"\n\nTriage Assessment: {triage_level.value.upper()} priority (score: {urgency_score}/10)."
    
    # Add red flags if any
    if red_flags:
        summary += f"\n\n⚠️ RED FLAGS IDENTIFIED: {', '.join(red_flags)}."
    
    return summary


def _get_recommended_action(triage_level: TriageLevel, urgency_score: int) -> str:
    """Determine recommended clinical action based on triage"""
    
    if triage_level == TriageLevel.CRITICAL or urgency_score >= 9:
        return (
            "IMMEDIATE ACTION REQUIRED: Call emergency services (ambulance) or "
            "direct patient to emergency room immediately. Do not delay."
        )
    
    elif triage_level == TriageLevel.HIGH or urgency_score >= 7:
        return (
            "URGENT: Schedule same-day appointment or direct to urgent care clinic. "
            "Patient should be seen within 2-4 hours."
        )
    
    elif triage_level == TriageLevel.MEDIUM or urgency_score >= 5:
        return (
            "SEMI-URGENT: Schedule appointment within 24-48 hours. "
            "Monitor symptoms and escalate if condition worsens."
        )
    
    else:
        return (
            "ROUTINE: Schedule appointment within 3-7 days. "
            "Provide self-care guidance and monitoring instructions."
        )
