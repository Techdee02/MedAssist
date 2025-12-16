"""
Report Generator for MedAssist

Generates structured JSON reports and human-readable summaries
for clinicians and patients.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from loguru import logger

from app.models.schemas import IntentType


class ReportGenerator:
    """
    Generates comprehensive medical intake reports.
    
    Combines outputs from:
    - Intent classification
    - Symptom intake
    - Triage scoring
    - Safety validation
    
    Produces:
    - Structured JSON (for database/EHR)
    - Clinician summary (professional format)
    - Patient summary (plain language)
    """
    
    def __init__(self):
        """Initialize report generator"""
        logger.info("ReportGenerator initialized")
    
    def generate_report(
        self,
        patient_id: str,
        intent: IntentType,
        symptom_data: Dict,
        triage_result: Dict,
        conversation_history: List[Dict],
        safety_issues: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Generate complete structured report.
        
        Args:
            patient_id: Unique patient identifier
            intent: Classified intent type
            symptom_data: Collected symptom information
            triage_result: Triage scoring outcome
            conversation_history: Full conversation log
            safety_issues: Any safety violations detected
            metadata: Additional metadata (age, gender, etc.)
            
        Returns:
            Complete report dictionary
        """
        report = {
            # Report metadata
            "report_id": self._generate_report_id(patient_id),
            "patient_id": patient_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_version": "1.0",
            
            # Classification
            "intent": {
                "type": intent.value,
                "description": self._get_intent_description(intent)
            },
            
            # Triage
            "triage": {
                "level": triage_result.get("triage_level"),
                "score": triage_result.get("score"),
                "wait_time": triage_result.get("wait_time_recommendation"),
                "red_flag_detected": triage_result.get("red_flag_detected", False),
                "red_flag_category": triage_result.get("red_flag_category"),
                "requires_immediate_attention": triage_result.get("requires_immediate_attention", False),
                "recommended_actions": triage_result.get("recommended_actions", [])
            },
            
            # Symptoms
            "symptoms": self._format_symptom_data(symptom_data),
            
            # Patient metadata
            "patient_metadata": metadata or {},
            
            # Conversation
            "conversation": {
                "message_count": len(conversation_history),
                "history": conversation_history[-10:]  # Last 10 messages
            },
            
            # Safety
            "safety": {
                "issues_detected": bool(safety_issues),
                "issues": safety_issues or [],
                "disclaimer": "This is an AI-assisted triage report. All information must be verified by qualified medical personnel."
            },
            
            # Summaries
            "summaries": {
                "clinician": self._generate_clinician_summary(
                    intent, symptom_data, triage_result, metadata
                ),
                "patient": self._generate_patient_summary(
                    intent, triage_result
                )
            }
        }
        
        logger.info(
            f"Generated report {report['report_id']} for patient {patient_id} | "
            f"Triage: {triage_result.get('triage_level')} | "
            f"Red flag: {triage_result.get('red_flag_detected', False)}"
        )
        
        return report
    
    def _generate_report_id(self, patient_id: str) -> str:
        """Generate unique report ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"RPT-{patient_id}-{timestamp}"
    
    def _get_intent_description(self, intent: IntentType) -> str:
        """Get human-readable intent description"""
        descriptions = {
            IntentType.APPOINTMENT_BOOKING: "Patient requesting appointment scheduling",
            IntentType.MEDICATION_REFILL: "Patient requesting prescription refill",
            IntentType.SYMPTOM_INQUIRY: "Patient reporting health concerns/symptoms",
            IntentType.FEEDBACK_COMPLAINT: "Patient providing feedback or complaint",
            IntentType.GENERAL_INQUIRY: "General question about services",
            IntentType.EMERGENCY: "Emergency medical situation"
        }
        return descriptions.get(intent, "Unknown intent")
    
    def _format_symptom_data(self, symptom_data: Dict) -> Dict:
        """Format symptom data for report"""
        if not symptom_data:
            return {}
        
        return {
            "primary_symptom": symptom_data.get("primary_symptom"),
            "onset": symptom_data.get("onset"),
            "duration": symptom_data.get("duration"),
            "severity": symptom_data.get("severity"),
            "location": symptom_data.get("location"),
            "character": symptom_data.get("character"),
            "aggravating_factors": symptom_data.get("aggravating_factors"),
            "relieving_factors": symptom_data.get("relieving_factors"),
            "associated_symptoms": symptom_data.get("associated_symptoms", []),
            "previous_episodes": symptom_data.get("previous_episodes"),
            "medications_tried": symptom_data.get("medications_tried", []),
            "vital_signs": symptom_data.get("vital_signs", {}),
            "is_complete": symptom_data.get("is_complete", False)
        }
    
    def _generate_clinician_summary(
        self,
        intent: IntentType,
        symptom_data: Dict,
        triage_result: Dict,
        metadata: Optional[Dict]
    ) -> str:
        """
        Generate professional summary for clinicians.
        
        Format: SOAP-like structure (Subjective, Objective, Assessment, Plan)
        """
        lines = []
        
        # Header
        lines.append("=== CLINICIAN SUMMARY ===\n")
        
        # Triage priority
        triage_level = triage_result.get("triage_level", "unknown").upper()
        red_flag = triage_result.get("red_flag_detected", False)
        
        if red_flag:
            lines.append(f"🚨 **PRIORITY: {triage_level} - RED FLAG DETECTED**")
            category = triage_result.get("red_flag_category", "unknown")
            lines.append(f"Red Flag Category: {category.upper()}\n")
        else:
            lines.append(f"Priority Level: {triage_level}\n")
        
        # Patient metadata
        if metadata:
            age = metadata.get("age")
            gender = metadata.get("gender")
            if age or gender:
                demo = []
                if age:
                    demo.append(f"{age}yo")
                if gender:
                    demo.append(gender)
                lines.append(f"Patient: {' '.join(demo)}")
            
            conditions = metadata.get("chronic_conditions", [])
            if conditions:
                lines.append(f"PMH: {', '.join(conditions)}")
            
            if metadata.get("pregnant"):
                lines.append("**PREGNANT**")
            
            lines.append("")
        
        # Subjective (Chief Complaint)
        lines.append("CHIEF COMPLAINT:")
        primary = symptom_data.get("primary_symptom", "Not specified")
        lines.append(f"  {primary}")
        
        # History of Present Illness
        if symptom_data:
            lines.append("\nHISTORY OF PRESENT ILLNESS:")
            
            onset = symptom_data.get("onset")
            duration = symptom_data.get("duration")
            if onset or duration:
                hpi_parts = []
                if onset:
                    hpi_parts.append(f"onset {onset}")
                if duration:
                    hpi_parts.append(f"duration {duration}")
                lines.append(f"  Timing: {', '.join(hpi_parts)}")
            
            severity = symptom_data.get("severity")
            if severity:
                lines.append(f"  Severity: {severity}/10")
            
            location = symptom_data.get("location")
            if location:
                lines.append(f"  Location: {location}")
            
            character = symptom_data.get("character")
            if character:
                lines.append(f"  Character: {character}")
            
            associated = symptom_data.get("associated_symptoms", [])
            if associated:
                lines.append(f"  Associated Sx: {', '.join(associated)}")
            
            agg = symptom_data.get("aggravating_factors")
            rel = symptom_data.get("relieving_factors")
            if agg or rel:
                factors = []
                if agg:
                    factors.append(f"worse with {agg}")
                if rel:
                    factors.append(f"better with {rel}")
                lines.append(f"  Modifying factors: {'; '.join(factors)}")
            
            meds = symptom_data.get("medications_tried", [])
            if meds:
                lines.append(f"  Medications tried: {', '.join(meds)}")
            
            prev = symptom_data.get("previous_episodes")
            if prev:
                lines.append(f"  Previous episodes: {prev}")
        
        # Objective (Vital Signs)
        vitals = symptom_data.get("vital_signs", {})
        if vitals:
            lines.append("\nVITAL SIGNS:")
            if vitals.get("temperature"):
                lines.append(f"  Temp: {vitals['temperature']}°C")
            if vitals.get("bp_systolic") and vitals.get("bp_diastolic"):
                lines.append(f"  BP: {vitals['bp_systolic']}/{vitals['bp_diastolic']} mmHg")
            if vitals.get("pulse"):
                lines.append(f"  Pulse: {vitals['pulse']} bpm")
            if vitals.get("spo2"):
                lines.append(f"  SpO2: {vitals['spo2']}%")
            if vitals.get("respiratory_rate"):
                lines.append(f"  RR: {vitals['respiratory_rate']} /min")
        
        # Assessment
        lines.append("\nASSESSMENT:")
        lines.append(f"  Triage Score: {triage_result.get('score', 'N/A')}/10")
        lines.append(f"  Classification: {triage_level}")
        
        # Plan
        lines.append("\nRECOMMENDED ACTIONS:")
        actions = triage_result.get("recommended_actions", [])
        for action in actions:
            lines.append(f"  • {action}")
        
        wait_time = triage_result.get("wait_time_recommendation", "")
        if wait_time:
            lines.append(f"\nTarget Wait Time: {wait_time}")
        
        return "\n".join(lines)
    
    def _generate_patient_summary(
        self,
        intent: IntentType,
        triage_result: Dict
    ) -> str:
        """
        Generate patient-friendly summary in plain language.
        Includes Nigerian Pidgin phrases for clarity.
        """
        lines = []
        
        triage_level = triage_result.get("triage_level", "medium")
        red_flag = triage_result.get("red_flag_detected", False)
        
        # Opening
        lines.append("Thank you for providing your information.")
        lines.append("(Tank you for di information wey you give us.)\n")
        
        # Urgency level
        if red_flag or triage_level == "critical":
            lines.append("⚠️ YOUR SITUATION REQUIRES IMMEDIATE ATTENTION")
            lines.append("(Your matter need urgent attention now now!)")
            lines.append("\nPlease go to the emergency room right away or call for emergency help.")
            lines.append("(Abeg go hospital emergency room sharp sharp or call ambulance.)")
        
        elif triage_level == "high":
            lines.append("Your situation needs prompt medical attention.")
            lines.append("(Your matter need doctor attention quick.)")
            lines.append("\nA healthcare worker will see you within 1 hour.")
            lines.append("(Doctor or nurse go see you for 1 hour time.)")
        
        elif triage_level == "medium":
            lines.append("A healthcare professional will see you soon.")
            lines.append("(Doctor or nurse go attend to you soon.)")
            lines.append("\nExpected wait time: up to 4 hours.")
            lines.append("(You fit wait small, maybe 4 hours.)")
        
        else:  # low
            lines.append("Your situation is not urgent.")
            lines.append("(Your matter no dey serious for now.)")
            lines.append("\nYou will be seen during regular clinic hours.")
            lines.append("(Dem go attend to you for normal clinic time.)")
        
        # What to expect
        lines.append("\n--- What Happens Next ---")
        lines.append("(Wetin go happen next)")
        lines.append("\n• A nurse will check your vital signs")
        lines.append("  (Nurse go check your body temperature, blood pressure)")
        lines.append("\n• A doctor will examine you")
        lines.append("  (Doctor go check you well well)")
        lines.append("\n• The medical team will determine the best treatment")
        lines.append("  (Di medical people go know which treatment dey best for you)")
        
        # Important reminders
        lines.append("\n--- Important Reminders ---")
        lines.append("• If your symptoms get worse, alert the staff immediately")
        lines.append("  (If your condition worse, tell staff sharp!)")
        lines.append("\n• Bring any medications you're currently taking")
        lines.append("  (Carry all di drugs wey you dey take)")
        lines.append("\n• Have your medical records if available")
        lines.append("  (If you get medical record, bring am)")
        
        # Disclaimer
        lines.append("\n--- Please Note ---")
        lines.append("This assessment was done by an AI assistant to help prepare for your visit.")
        lines.append("Only a qualified doctor or nurse can diagnose and treat medical conditions.")
        lines.append("(Na AI help collect this information. Only real doctor fit treat you.)")
        
        return "\n".join(lines)
    
    def generate_minimal_report(
        self,
        patient_id: str,
        intent: IntentType,
        message: str
    ) -> Dict:
        """
        Generate minimal report for non-symptom intents.
        
        Used for appointment booking, general inquiries, etc.
        """
        return {
            "report_id": self._generate_report_id(patient_id),
            "patient_id": patient_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_version": "1.0",
            "intent": {
                "type": intent.value,
                "description": self._get_intent_description(intent)
            },
            "message": message,
            "triage": None,
            "requires_medical_attention": False
        }
    
    def export_to_json(self, report: Dict) -> str:
        """Export report as JSON string"""
        import json
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def export_to_ehr_format(self, report: Dict) -> Dict:
        """
        Export in EHR-compatible format.
        
        Simplified structure for integration with
        electronic health record systems.
        """
        return {
            "patient_id": report["patient_id"],
            "encounter_date": report["generated_at"],
            "chief_complaint": report.get("symptoms", {}).get("primary_symptom"),
            "triage_level": report.get("triage", {}).get("level"),
            "triage_score": report.get("triage", {}).get("score"),
            "red_flag": report.get("triage", {}).get("red_flag_detected", False),
            "vital_signs": report.get("symptoms", {}).get("vital_signs", {}),
            "symptoms": report.get("symptoms", {}),
            "assessment": report.get("summaries", {}).get("clinician"),
            "urgent": report.get("triage", {}).get("requires_immediate_attention", False)
        }


# Singleton instance
_report_generator = None


def get_report_generator() -> ReportGenerator:
    """Get or create singleton ReportGenerator instance"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
