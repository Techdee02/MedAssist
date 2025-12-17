# MedAssist — AI Agent for Local Clinics, Pharmacies, and Hospitals

> **An AI-powered healthcare assistant that automates patient communication, streamlines appointment management, and extracts actionable insights for local healthcare facilities in Nigeria.**

---

## 🚨 Problem

Local clinics, pharmacies, and labs in Nigeria often face:

- Disorganized patient communication (WhatsApp, calls, emails)
- Missed appointments and follow-ups
- Poor review/feedback management
- No insight into common complaints or patient trends
- Manual record-keeping in Excel or paper
- High administrative workload for staff

**Impact:**
- Loss of revenue
- Poor patient trust
- Lower quality healthcare outcomes

---

## 🎯 Solution

MedAssist is an **AI-powered healthcare assistant** that helps clinics, pharmacies, and hospitals automate patient communication, streamline appointment management, and extract actionable insights.

### Key Capabilities

#### 1. Patient Communication Automation
- Responds to patient WhatsApp/Facebook messages automatically
- Understands intent: appointment booking, medication refill, feedback, symptom intake
- Slot-filling & follow-up questions for incomplete requests

#### 2. Appointment Scheduling
- AI-assisted booking via WhatsApp, dashboard, or mobile app
- Checks doctor/clinic availability and prevents double-booking
- Supports cancellations, reschedules, recurring appointments
- Optional integration with **Google Calendar** for staff schedules
- Automated reminders via WhatsApp/SMS/email

#### 3. Medication Refill & Follow-Up Alerts
- Sends automated reminders for prescriptions or follow-up visits
- Tracks adherence and flags missed refills for clinic staff

#### 4. Symptom Intake & Structured Reports
- AI asks relevant questions about patient symptoms
- Generates structured JSON reports and human-readable summaries
- Triage-level scoring (low/medium/high urgency)
- Sends reports to clinician dashboards or WhatsApp/email notifications
- Human-in-the-loop for urgent or sensitive cases

#### 5. Medical Document Extraction
- Upload PDFs, images, or scanned documents (lab reports, prescriptions, discharge summaries)
- OCR + AI extracts structured patient info, test results, medications
- Generates summaries and integrates data into patient records

#### 6. Feedback & Complaint Management
- Collects patient reviews and ratings automatically
- AI clusters common complaints/trends
- Generates weekly insights for clinic management

#### 7. Analytics & Dashboards
- Clinic dashboard showing:
  - Upcoming appointments
  - Missed appointments
  - Patient satisfaction score
  - Common complaints
  - Weekly summary of AI interactions

#### 8. External System Integration (Optional)
- **Google Sheets / Excel:** auto-sync patient records, appointments, follow-ups
- **Google Calendar:** sync appointments for doctors/staff
- Can serve as **backup for low-tech clinics**

#### 9. Multi-Language & Accessibility
- AI can support English and local languages (Yoruba, Hausa, Igbo)
- Designed for accessibility in low-tech environments

---

## 🤖 Tech Stack

| Component | Technology / Tool | Status |
|-----------|-------------------|--------|
| **AI Microservice** | FastAPI (Python), Groq LLM (Llama 3.3 70B) | ✅ **Live** - [https://medassist-ai-service.onrender.com](https://medassist-ai-service.onrender.com) |
| **Backend / Orchestration** | Java (Spring Boot), PostgreSQL | ✅ **Live** - [https://medassist-23zx.onrender.com](https://medassist-23zx.onrender.com) |
| **Database** | PostgreSQL (patient records, conversations, messages) | ✅ **Live** |
| **Messaging Gateway** | Twilio WhatsApp API (sandbox + production) | 📋 **Implementation Guide Ready** |
| **Admin Dashboard** | Next.js 14, TypeScript, Tailwind CSS | ✅ **Production Ready** - Mobile Responsive |
| **Translation** | Azure AI Translator API | 🚧 **Partial** (Credentials needed) |
| **OCR / Document AI** | Azure Form Recognizer | 🔄 **Planned** |

---

## 🏗 Architecture Overview

```
┌─────────────────┐
│ Patient Message │
│  (WhatsApp/FB)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Meta WhatsApp API   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐      ┌──────────────────┐
│  Java Backend       │◄────►│  FastAPI AI      │
│  (Spring Boot)      │      │  (Intent, NLP)   │
└────────┬────────────┘      └──────────────────┘
         │
         ├──────────────────┬──────────────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   MongoDB       │ │   Redis Cache   │ │ Clinician       │ │ Google Calendar │
│ (Patient Data)  │ │ (Session State) │ │ Dashboard       │ │ / Sheets        │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Workflow:**
1. **Inbound Patient Message** → Meta WhatsApp API → Java Backend → FastAPI AI (intent detection, symptom intake)
2. **AI Output** → structured report, summary, triage level → Java backend → clinician dashboard + WhatsApp/email notification
3. **Appointment Requests** → AI slot-filling → Backend checks availability → Confirm & store → Send confirmation + reminders
4. **Document Upload** → OCR + AI extraction → store structured data → link to patient record
5. **Analytics & Dashboard** → aggregate data, trends, common complaints, satisfaction scores

---

## 💡 Safety & Guardrails

- AI **does not diagnose or prescribe**; always refers critical cases to a clinician
- Red-flag detection for urgent symptoms
- Human-in-loop review for sensitive or emergency cases
- Encrypted storage for PII; audit logs for all AI interactions

---

## ✅ Benefits for Clinics

- Saves **administrative time** → staff can focus on patient care
- Improves **patient communication and satisfaction**
- Reduces **missed appointments and follow-ups**
- Provides **data-driven insights** on complaints, trends, and drop-offs
- Integrates smoothly with **existing systems** (Sheets, Calendar)

---

## 🚀 MVP Scope

### Phase 1 (MVP) - ✅ **COMPLETE**
1. ✅ Admin dashboard with real-time patient queue and triage levels
2. ✅ Conversation management with WhatsApp-style interface
3. ✅ AI-powered symptom intake and triage scoring
4. ✅ Emergency detection with high-confidence classification
5. ✅ Real-time polling (5-second intervals) for live updates
6. ✅ Mobile-responsive design with hamburger menu
7. ✅ JWT authentication with auto-logout on 401
8. ✅ Backend API with PostgreSQL (deployed on Render)
9. ✅ AI Service with Groq LLM (deployed on Render)
10. 📋 WhatsApp bot implementation guide (ready for backend integration)

### Phase 2 (In Progress / Planned)
- 🚧 WhatsApp Twilio integration (guide complete, awaiting implementation)
- 🚧 Multi-language support - Yoruba, Hausa, Igbo (Azure Translator setup needed)
- 🔄 Medical document extraction (PDFs, lab reports, prescriptions)
- 🔄 Automated appointment reminders via WhatsApp/SMS
- 🔄 Complaint clustering & trend analytics
- 🔄 Google Sheets / Excel integration

---

## 👥 Team & Roles

### AI/ML Engineer
**Focus:** AI microservice, NLP, and intelligent features

- Build and deploy FastAPI AI service with Llama-based LLM
- Implement intent detection and slot-filling conversational flows
- Develop symptom intake AI with follow-up question generation
- Create triage scoring system (low/medium/high urgency)
- Implement medical document extraction (OCR + AI parsing)
- Develop complaint clustering and trend analysis algorithms
- Design and maintain AI safety guardrails
- Implement multi-language support
- Fine-tune models and optimize AI performance

### Software Engineer
**Focus:** Backend orchestration, integrations, and frontend

- Build Java/Spring Boot backend for core business logic
- Implement appointment scheduling system with availability checking
- Integrate Meta WhatsApp Cloud API for messaging gateway
- Set up MongoDB and Redis infrastructure
- Build RESTful APIs connecting AI service to backend
- Develop React dashboard and/or Flutter mobile app
- Implement automated reminders (WhatsApp/SMS/email)
- Build Google Calendar/Sheets integration
- Set up authentication, authorization, and RBAC
- Implement encrypted document storage
- Create audit logging system for compliance
- Deploy and maintain production infrastructure

---

## 📈 Business Value

- Every local clinic and pharmacy in Nigeria struggles with workflow automation
- MedAssist positions itself as a **mini AI CRM** for healthcare
- Quick adoption potential with **3–5 pilot clinics** for testimonials
- Scales to larger hospitals or multi-branch networks

---

## 🛠 Getting Started

### Prerequisites
- Node.js 18+ (for admin dashboard)
- Python 3.11+ (for AI service - optional if using deployed version)
- Java 17+ (for backend - optional if using deployed version)

### Quick Start - Admin Dashboard

```bash
# Clone the repository
git clone <repository-url>
cd MedAssist/admin-dashboard

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local and set:
# NEXT_PUBLIC_API_URL=https://medassist-23zx.onrender.com

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and login with your credentials.

### Quick Start - AI Service (Local Development)

```bash
cd MedAssist/ai-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_groq_api_key

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### WhatsApp Bot Implementation

Backend developers should refer to [WHATSAPP_BOT_IMPLEMENTATION.md](WHATSAPP_BOT_IMPLEMENTATION.md) for complete integration guide including:
- Twilio setup and configuration
- Webhook implementation
- Patient registration flow
- AI service integration
- Full Java/Spring Boot code examples

### Production Deployments

| Service | URL | Documentation |
|---------|-----|---------------|
| **Backend API** | https://medassist-23zx.onrender.com | [Swagger UI](https://medassist-23zx.onrender.com/swagger-ui/index.html) |
| **AI Service** | https://medassist-ai-service.onrender.com | [API Docs](https://medassist-ai-service.onrender.com/docs) |
| **Admin Dashboard** | *Coming Soon* | See [admin-dashboard/README.md](admin-dashboard/README.md) |

---

## 📄 License

MIT License - See LICENSE file for details
