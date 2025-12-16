"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class IntentType(str, Enum):
    """Supported intent types"""
    APPOINTMENT_BOOKING = "appointment_booking"
    MEDICATION_REFILL = "medication_refill"
    SYMPTOM_INQUIRY = "symptom_inquiry"
    FEEDBACK_COMPLAINT = "feedback_complaint"
    GENERAL_INQUIRY = "general_inquiry"
    EMERGENCY = "emergency"


class TriageLevel(str, Enum):
    """Triage urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "english"
    PIDGIN = "pidgin"
    YORUBA = "yoruba"
    HAUSA = "hausa"
    IGBO = "igbo"
    MIXED = "mixed"


# Health Check
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Message Processing
class ConversationMessage(BaseModel):
    """Single conversation message"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None


class ProcessMessageRequest(BaseModel):
    """Request to process a patient message"""
    message_id: str = Field(..., description="Unique message identifier")
    patient_id: str = Field(..., description="Patient identifier")
    message: str = Field(..., description="Patient's message text")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conversation_history: List[ConversationMessage] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (language, channel, etc.)"
    )


class IntentResult(BaseModel):
    """Intent classification result"""
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class ProcessMessageResponse(BaseModel):
    """Response from message processing"""
    message_id: str
    intent: IntentType
    confidence: float
    response: str = Field(..., description="AI response to patient")
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted entities and slots"
    )
    next_action: str = Field(
        ...,
        description="Next action: 'collect_more_info', 'complete', 'escalate'"
    )
    triage_level: Optional[TriageLevel] = None
    requires_human_review: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Symptom Report
class SymptomData(BaseModel):
    """Collected symptom information"""
    primary_symptom: str
    onset: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[int] = Field(None, ge=0, le=10)
    location: Optional[str] = None
    character: Optional[str] = None
    aggravating_factors: Optional[List[str]] = None
    relieving_factors: Optional[List[str]] = None
    associated_symptoms: Optional[List[str]] = None
    previous_episodes: Optional[bool] = None
    medications_tried: Optional[List[str]] = None


class GenerateSymptomReportRequest(BaseModel):
    """Request to generate symptom report"""
    patient_id: str
    conversation_data: SymptomData


class SymptomReport(BaseModel):
    """Generated symptom report"""
    report_id: str
    patient_id: str
    structured_report: Dict[str, Any]
    human_summary: str
    triage_level: TriageLevel
    urgency_score: int = Field(..., ge=1, le=10)
    red_flags: List[str] = Field(default_factory=list)
    recommended_action: str
    requires_immediate_attention: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Error Response
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
