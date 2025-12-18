# Patient Registration Flow (Two-Step)

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: New Patient Sends First Message                            │
├─────────────────────────────────────────────────────────────────────┤
│ Patient: "Hello"                                                    │
│ Phone: whatsapp:+2348012345678                                     │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Backend Creates Patient Record (Status: PENDING_CLINIC)    │
├─────────────────────────────────────────────────────────────────────┤
│ Patient patient = registrationService.startRegistration(phone);    │
│                                                                     │
│ Patient Record Created:                                            │
│   - phone: "+2348012345678"                                        │
│   - clinic: City Health Clinic (temporary)                         │
│   - firstName: "Pending"                                           │
│   - lastName: "Registration"                                       │
│   - registrationStatus: "PENDING_CLINIC"  ← KEY                    │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Bot Sends Clinic Options                                   │
├─────────────────────────────────────────────────────────────────────┤
│ Bot: "👋 Welcome to MedAssist!                                     │
│                                                                     │
│       Which clinic are you registering with?                       │
│                                                                     │
│       1️⃣ City Health Clinic                                       │
│       2️⃣ Green Cross Pharmacy                                     │
│       3️⃣ Life Care Hospital                                       │
│                                                                     │
│       Reply with the number (1, 2, or 3)"                          │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Patient Selects Clinic                                     │
├─────────────────────────────────────────────────────────────────────┤
│ Patient: "2"                                                        │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Backend Updates Patient (Status: AWAITING_NAME)            │
├─────────────────────────────────────────────────────────────────────┤
│ // Check: registrationStatus == "PENDING_CLINIC" ✅                │
│                                                                     │
│ Patient updated = registrationService.setClinicSelection(          │
│     patient, "2");                                                 │
│                                                                     │
│ Patient Record Updated:                                            │
│   - clinic: Green Cross Pharmacy  ← UPDATED                        │
│   - registrationStatus: "AWAITING_NAME"  ← UPDATED                 │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: Bot Asks for Name                                          │
├─────────────────────────────────────────────────────────────────────┤
│ Bot: "Great! 👍                                                    │
│                                                                     │
│       What's your full name?                                       │
│                                                                     │
│       (Example: John Doe)"                                         │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: Patient Provides Name                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Patient: "Sarah Johnson"                                           │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 8: Backend Completes Registration (Status: COMPLETE)          │
├─────────────────────────────────────────────────────────────────────┤
│ // Check: registrationStatus == "AWAITING_NAME" ✅                 │
│                                                                     │
│ Patient completed = registrationService.completeRegistrationWithName(│
│     patient, "Sarah Johnson");                                     │
│                                                                     │
│ Name Parsing:                                                      │
│   - Split on whitespace: ["Sarah", "Johnson"]                     │
│   - firstName = "Sarah"                                            │
│   - lastName = "Johnson"                                           │
│                                                                     │
│ Patient Record Final:                                              │
│   - phone: "+2348012345678"                                        │
│   - clinic: Green Cross Pharmacy                                   │
│   - firstName: "Sarah"  ← UPDATED                                  │
│   - lastName: "Johnson"  ← UPDATED                                 │
│   - registrationStatus: "COMPLETE"  ← UPDATED                      │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 9: Bot Sends Confirmation                                     │
├─────────────────────────────────────────────────────────────────────┤
│ Bot: "✅ Registration complete!                                    │
│                                                                     │
│       You're now connected to Green Cross Pharmacy.                │
│                                                                     │
│       How can we help you today?"                                  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 10: Patient Sends Medical Query                               │
├─────────────────────────────────────────────────────────────────────┤
│ Patient: "I have severe headache and fever"                        │
│                                                                     │
│ Backend checks:                                                     │
│   - Patient exists? YES ✅                                         │
│   - registrationStatus == "COMPLETE"? YES ✅                       │
│                                                                     │
│ → Route to AI service for symptom analysis                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Registration States

| State | Description | Next State |
|-------|-------------|------------|
| `PENDING_CLINIC` | Patient created, awaiting clinic selection | `AWAITING_NAME` |
| `AWAITING_NAME` | Clinic selected, awaiting patient name | `COMPLETE` |
| `COMPLETE` | Registration complete, ready for medical queries | N/A |

## Code Decision Logic

```java
// In WhatsAppService.handleIncomingMessage()

Patient patient = registrationService.findByPhone(normalizedPhone);

if (patient == null) {
    // NEW PATIENT
    registrationService.startRegistration(phone);
    twilioService.sendMessage(phone, BotMessages.WELCOME_MESSAGE);
    return;
}

if ("PENDING_CLINIC".equals(patient.getRegistrationStatus())) {
    // STEP 1: CLINIC SELECTION
    registrationService.setClinicSelection(patient, messageBody);
    twilioService.sendMessage(phone, BotMessages.ASK_NAME);
    return;
}

if ("AWAITING_NAME".equals(patient.getRegistrationStatus())) {
    // STEP 2: NAME COLLECTION
    registrationService.completeRegistrationWithName(patient, messageBody);
    twilioService.sendMessage(phone, BotMessages.REGISTRATION_COMPLETE);
    return;
}

if ("COMPLETE".equals(patient.getRegistrationStatus())) {
    // FULLY REGISTERED - PROCESS WITH AI
    processMessageWithAI(patient, messageBody);
}
```

## Name Parsing Logic

```java
// Simple split on whitespace
String[] nameParts = fullName.trim().split("\\s+", 2);

// Examples:
"Sarah Johnson"        → firstName="Sarah",    lastName="Johnson"
"John"                 → firstName="John",     lastName=""
"Mary Jane Smith"     → firstName="Mary",     lastName="Jane Smith"
"José María García"   → firstName="José",     lastName="María García"
```

## Error Handling

**Invalid Clinic Selection:**
```
Patient: "5"  (not 1, 2, or 3)
Bot: "❌ Invalid selection. Please reply with 1, 2, or 3 to select your clinic."
```

**Empty Name:**
```
Patient: "  "  (whitespace only)
→ firstName="", lastName=""  (allowed, admin can update later)
```

## Database Schema

```sql
CREATE TABLE patients (
    id BINARY(16) PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    clinic_id BINARY(16) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    registration_status VARCHAR(20) DEFAULT 'COMPLETE',
    registered_at TIMESTAMP NOT NULL,
    INDEX idx_phone (phone),
    INDEX idx_clinic_id (clinic_id),
    INDEX idx_registration_status (registration_status)
);
```

## Benefits of This Approach

✅ **User-friendly:** Natural conversation flow  
✅ **Accurate data:** Real patient names instead of placeholders  
✅ **Simple:** Only 2 extra messages  
✅ **Database-only:** No Redis required  
✅ **Flexible:** Easy to add more steps (email, age, etc.) later  
✅ **Recoverable:** If patient abandons, record stays pending (can be cleaned up later)  

## Optional Enhancement: Timeout Cleanup

Add a scheduled job to clean up abandoned registrations:

```java
@Scheduled(cron = "0 0 2 * * ?")  // Daily at 2 AM
public void cleanupAbandonedRegistrations() {
    LocalDateTime oneDayAgo = LocalDateTime.now().minusDays(1);
    
    List<Patient> abandoned = patientRepository.findByRegistrationStatusIn(
        List.of("PENDING_CLINIC", "AWAITING_NAME")
    ).stream()
    .filter(p -> p.getRegisteredAt().isBefore(oneDayAgo))
    .collect(Collectors.toList());
    
    patientRepository.deleteAll(abandoned);
    log.info("Cleaned up {} abandoned registrations", abandoned.size());
}
```
