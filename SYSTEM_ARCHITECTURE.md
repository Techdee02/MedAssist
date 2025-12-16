# MedAssist System Architecture

## Overview

MedAssist is a multi-tenant healthcare platform connecting patients with clinics/pharmacies via WhatsApp AI chatbot.

**Components:**
1. **AI Service** (existing) - Symptom analysis, triage, translation
2. **WhatsApp Gateway** (to build) - Message routing, patient-clinic linking
3. **Admin Dashboard** (to build) - Clinic staff interface
4. **MongoDB** - Conversations, patients, clinic data

---

## System Flow

```
Patient → WhatsApp → Gateway → AI Service → Response → Patient
                         ↓
                    MongoDB
                         ↓
                  Admin Dashboard
```

---

## Patient WhatsApp Flow

### First Contact
```
Patient: "Hello"
Bot: "Welcome! Which clinic are you with?
     1. City Health Clinic
     2. Green Cross Pharmacy
     Reply with number or clinic code."

Patient: "1"
Bot: "✅ Linked to City Health Clinic"
```

### Symptom Conversation
```
Patient: "I have severe chest pain"
Bot: "🚨 EMERGENCY detected. Call 911 immediately!"
     [Notifies clinic admin instantly]

Patient: "I have a headache for 2 days"
Bot: "When did it start?"
Patient: "Sunday morning"
Bot: "How severe (1-10)?"
Patient: "7"
Bot: "📋 Triage: MEDIUM
     We recommend seeing a doctor within 24 hours.
     City Health Clinic has been notified."
```

### Language Support
```
Patient: "Mo ni ibà" (Yoruba)
Bot: "Bawo ni ibà náà ti lágbara?" 
     (How severe is the fever?)
```

---

## Admin Dashboard Flow

### Login
```
https://admin.medassist.com
Email: admin@cityhealthclinic.com
Password: ***

→ Dashboard shows only City Health Clinic patients
```

### Dashboard View
```
┌─────────────────────────────────────┐
│ City Health Clinic Dashboard        │
├─────────────────────────────────────┤
│ 🔴 CRITICAL (2)                     │
│ 🟠 HIGH (5)                         │
│ 🟡 MEDIUM (12)                      │
│ 🟢 LOW (8)                          │
└─────────────────────────────────────┘

Patient Queue:
┌────────────────────────────────────────┐
│ 🔴 John Doe (+234-XXX-1111)           │
│    Chest pain, radiating to left arm   │
│    5 mins ago                          │
│    [View Chat] [Call] [Assign Doctor] │
└────────────────────────────────────────┘
```

### Admin Actions
- View full conversation history
- See AI triage report
- Send WhatsApp reply to patient
- Escalate to phone call
- Schedule appointment
- Mark as resolved

---

## Data Security

### Patient-Clinic Isolation

**Database:**
```json
{
  "conversation_id": "conv_123",
  "patient_phone": "+234-XXX-1111",
  "clinic_id": "clinic_001",
  "messages": [...],
  "triage_level": "MEDIUM"
}
```

**Admin Access:**
```javascript
// Admin from Clinic A logs in
// JWT token contains: { clinic_id: "clinic_001" }

// All database queries filtered:
db.conversations.find({ 
  clinic_id: "clinic_001"  // Auto-filtered
})

// Result: Only Clinic A's patients visible
```

---

## Technical Stack

### WhatsApp Gateway (Python/FastAPI)
```
- Twilio webhooks
- MongoDB integration
- AI Service API calls
- JWT authentication
- WebSocket notifications
```

### Admin Dashboard (Next.js/React)
```
- Next.js 14 + TypeScript
- Tailwind CSS
- MongoDB connection
- Real-time updates
- Charts/analytics
```

### Database (MongoDB)
```
Collections:
- clinics
- patients
- conversations
- admin_users
- audit_logs
```

---

## Deployment

**AI Service:** https://medassist-ai-service.onrender.com ✅ (live)

**WhatsApp Gateway:** Render (to deploy)
**Admin Dashboard:** Vercel (to deploy)
**MongoDB:** MongoDB Atlas (free tier)

---

## Patient Registration

### Option 1: WhatsApp Self-Registration
```
Bot: "New patient? Enter clinic code."
Patient: "CH2025"
Bot: "✅ Registered with City Health Clinic"
```

### Option 2: Admin Pre-Registration
```
Admin Dashboard → Add Patient
Enter: +234-XXX-XXXX
→ Patient receives: "Welcome to City Health Clinic! 
                     Chat with us anytime."
```

---

## API Endpoints

### WhatsApp Gateway
```
POST /webhook/whatsapp          # Receive messages
POST /api/send-message          # Send WhatsApp reply
GET  /api/conversations         # Get clinic conversations
GET  /api/conversations/:id     # Get conversation details
POST /api/auth/login            # Admin login
```

### Existing AI Service
```
POST /api/v1/message/process    # Process symptom message
POST /api/v1/translate          # Translate text
GET  /api/v1/health             # Health check
```

---

## Next Steps

1. **Build WhatsApp Gateway** (1 week)
2. **Build Admin Dashboard** (2 weeks)
3. **Setup Twilio WhatsApp** (1 day)
4. **Deploy & Test** (3 days)
5. **Onboard First Clinic** (1 week)
