# MedAssist Admin Dashboard - Product Requirements Document

**Project:** Admin Dashboard for Clinic Staff  
**Stack:** Next.js 14, TypeScript, Tailwind CSS, PostgreSQL API  
**Developer:** Frontend Team  
**Timeline:** 1 day (MVP)

---

## 1. Project Overview

Build a web dashboard for clinic/pharmacy staff to:
- View WhatsApp patient conversations in real-time
- Monitor triage levels (CRITICAL, HIGH, MEDIUM, LOW)
- Send replies to patients via WhatsApp
- Manage patient queue
- View basic analytics

---

## 2. System Architecture

```
Admin User → [Next.js Dashboard] → Backend API → PostgreSQL
                                         ↓
                                   WhatsApp Bot
```

**Backend API:** To be built by Java team (see BACKEND_PRD.md)  
**Your Frontend:** Next.js web application

---

## 3. Tech Stack

### Required
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components (optional)
- React Query / SWR (data fetching)
- JWT authentication
- Axios/Fetch API

### Optional (Nice to have)
- Zustand/Redux (state management)
- Socket.io (real-time updates)
- Chart.js (analytics)

---

## 4. Core Features

### A. Login Page
```
/login

- Email input
- Password input
- "Remember me" checkbox
- Submit button
- Error handling (invalid credentials)

API: POST /api/auth/login
Response: { token, user: { id, email, clinicId, role } }

Store JWT in localStorage/cookies
Redirect to dashboard on success
```

### B. Dashboard Home
```
/dashboard

Top Stats:
┌─────────────────────────────────────────────┐
│ 🔴 CRITICAL: 2   🟠 HIGH: 5                │
│ 🟡 MEDIUM: 12    🟢 LOW: 8                 │
│ Total Patients Today: 27                    │
└─────────────────────────────────────────────┘

Patient Queue (Sorted by triage priority):
┌──────────────────────────────────────────────┐
│ 🔴 John Doe                                  │
│    +234-XXX-1111                             │
│    "I have severe chest pain..."            │
│    5 mins ago                                │
│    [View Chat] [Call Patient]               │
├──────────────────────────────────────────────┤
│ 🔴 Jane Smith                                │
│    +234-XXX-2222                             │
│    "Difficulty breathing..."                 │
│    12 mins ago                               │
│    [View Chat] [Call Patient]               │
└──────────────────────────────────────────────┘

Filters:
- All / Critical / High / Medium / Low
- Active / Resolved
- Search by name/phone
```

### C. Conversation View
```
/dashboard/conversations/:id

Left Panel: Conversation List (like WhatsApp)
Right Panel: Chat Thread

┌────────────────┬─────────────────────────────┐
│ Conversations  │  John Doe (+234-XXX-1111)  │
│                │  🔴 CRITICAL                │
│ 🔴 John Doe    │                             │
│    5m ago      │ ┌─────────────────────────┐ │
│                │ │ Patient (10:30 AM):     │ │
│ 🟠 Jane Smith  │ │ I have severe chest     │ │
│    12m ago     │ │ pain radiating to arm   │ │
│                │ └─────────────────────────┘ │
│ 🟡 Mike Johnson│                             │
│    1h ago      │ ┌─────────────────────────┐ │
│                │ │ AI (10:30 AM):          │ │
│                │ │ 🚨 EMERGENCY detected   │ │
│                │ │ Seek immediate care     │ │
│                │ └─────────────────────────┘ │
│                │                             │
│                │ [Type message...]  [Send]  │
└────────────────┴─────────────────────────────┘

Sidebar: Patient Info & Triage Report
- Name, Phone, Age
- Triage Level with color badge
- Symptom Summary
- AI Recommendations
- Action Buttons:
  • Mark as Resolved
  • Escalate to Doctor
  • Schedule Appointment
```

### D. Send Message Feature
```
Admin types message in chat input
Click "Send"

API: POST /api/messages/send
{
  "conversationId": "conv_123",
  "message": "A doctor will call you shortly"
}

Message appears in chat thread
Patient receives WhatsApp message instantly
```

---

## 5. UI/UX Requirements

### Design System
```
Colors:
- Critical: Red (#EF4444)
- High: Orange (#F59E0B)
- Medium: Yellow (#EAB308)
- Low: Green (#10B981)
- Primary: Blue (#3B82F6)
- Background: Gray (#F9FAFB)

Typography:
- Headings: Inter/SF Pro
- Body: System font stack

Responsive:
- Desktop first (clinic staff use computers)
- Mobile responsive (tablet support)
```

### Key Components
```tsx
// TileCard.tsx - Triage level cards
<TileCard 
  level="CRITICAL" 
  count={2} 
  color="red" 
/>

// ConversationList.tsx - Patient queue
<ConversationList 
  conversations={conversations}
  onSelect={handleSelect}
/>

// ChatThread.tsx - Message display
<ChatThread 
  messages={messages}
  onSend={handleSend}
/>

// TriageBadge.tsx - Color-coded badge
<TriageBadge level="CRITICAL" />
```

---

## 6. API Integration

### Base URL
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
// e.g., https://api.medassist.com
```

### Authentication
```typescript
// Store JWT after login
localStorage.setItem('auth_token', response.token);

// Include in all requests
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

### API Endpoints
```typescript
// Auth
POST   /api/auth/login
POST   /api/auth/refresh

// Conversations
GET    /api/conversations
GET    /api/conversations/:id
PATCH  /api/conversations/:id

// Messages
POST   /api/messages/send

// Patients
GET    /api/patients
```

### Example API Call
```typescript
// lib/api.ts
export async function getConversations(
  triageLevel?: string,
  status?: string
) {
  const token = localStorage.getItem('auth_token');
  
  const params = new URLSearchParams();
  if (triageLevel) params.append('triageLevel', triageLevel);
  if (status) params.append('status', status);
  
  const response = await fetch(
    `${API_BASE_URL}/api/conversations?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) throw new Error('Failed to fetch');
  return response.json();
}
```

---

## 7. Data Types

```typescript
// types/index.ts

export enum TriageLevel {
  CRITICAL = 'CRITICAL',
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW'
}

export enum MessageRole {
  USER = 'USER',
  ASSISTANT = 'ASSISTANT',
  ADMIN = 'ADMIN'
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  triageLevel?: TriageLevel;
}

export interface Conversation {
  id: string;
  patientId: string;
  patientName: string;
  patientPhone: string;
  clinicId: string;
  messages: Message[];
  triageLevel: TriageLevel;
  status: 'active' | 'resolved';
  lastMessageAt: string;
  createdAt: string;
}

export interface User {
  id: string;
  email: string;
  clinicId: string;
  role: string;
}
```

---

## 8. Project Structure

```
admin-dashboard/
├── app/
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx
│   ├── dashboard/
│   │   ├── page.tsx                 # Home/queue
│   │   └── conversations/
│   │       └── [id]/
│   │           └── page.tsx         # Chat view
│   └── layout.tsx
├── components/
│   ├── ui/                          # Base components
│   ├── TileCard.tsx
│   ├── ConversationList.tsx
│   ├── ChatThread.tsx
│   ├── TriageBadge.tsx
│   └── SendMessageForm.tsx
├── lib/
│   ├── api.ts                       # API calls
│   └── auth.ts                      # Auth helpers
├── types/
│   └── index.ts
└── middleware.ts                    # Auth protection
```

---

## 9. Authentication Flow

```typescript
// middleware.ts - Protect dashboard routes
export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token');
  
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
}

export const config = {
  matcher: '/dashboard/:path*'
};
```

---

## 10. Real-time Updates (Optional)

```typescript
// Use polling for MVP (simpler)
useEffect(() => {
  const interval = setInterval(() => {
    refetchConversations();
  }, 5000); // Poll every 5 seconds
  
  return () => clearInterval(interval);
}, []);

// Later: Upgrade to WebSocket
// const socket = io(API_BASE_URL);
// socket.on('new_message', (data) => { ... });
```

---

## 11. Deliverables

### Day 1 - MVP
- [ ] Next.js project setup
- [ ] Login page with JWT authentication
- [ ] Dashboard home with triage stats
- [ ] Conversation list (patient queue)
- [ ] Chat view (conversation thread)
- [ ] Send WhatsApp message feature
- [ ] Basic responsive design
- [ ] API integration with backend
- [ ] Deploy to Vercel

**MVP Scope:**
- Basic UI (no fancy animations)
- Manual polling (no WebSockets)
- Essential features only
- Desktop-first (mobile can improve later)

**Post-MVP:**
- Real-time WebSocket updates
- Advanced filtering/search
- Analytics dashboard
- Patient management
- Appointment scheduling
- Dark mode

---

## 12. Testing Requirements

### Manual Testing
```
✓ Login with valid credentials
✓ Login with invalid credentials (show error)
✓ View conversation list
✓ Filter by triage level
✓ Click conversation → open chat
✓ Send message → appears in chat
✓ Logout → redirect to login
✓ Protected route without token → redirect to login
```

---

## 13. Deployment

**Platform:** Vercel (recommended for Next.js)

**Environment Variables:**
```bash
# .env.local
NEXT_PUBLIC_API_URL=https://api.medassist.com
```

**Build Commands:**
```bash
npm run build
npm run start
```

**Vercel Deployment:**
```bash
npx vercel --prod
```

---

## 14. Design Reference

**Inspiration:**
- WhatsApp Web (conversation layout)
- Slack (sidebar navigation)
- Linear (clean minimal UI)
- Tailwind UI components

**Must Haves:**
- Clean, professional look
- Clear triage color coding
- Easy to scan patient queue
- Mobile responsive
- Fast load times

---

## 15. Success Criteria

- [ ] Admin can login successfully
- [ ] Dashboard shows all conversations filtered by clinic
- [ ] Triage levels clearly visible with colors
- [ ] Admin can click conversation to view full chat
- [ ] Admin can send WhatsApp message to patient
- [ ] Messages appear in real-time (or within 5 sec refresh)
- [ ] No cross-clinic data leaks (security)
- [ ] Page loads under 2 seconds
- [ ] Works on Chrome, Safari, Firefox
- [ ] Deployed to production URL

---

## Sample Screens

### Login
```
┌─────────────────────────────────┐
│                                 │
│       🏥 MedAssist Admin       │
│                                 │
│  Email: [____________]          │
│                                 │
│  Password: [____________]       │
│                                 │
│  ☐ Remember me                  │
│                                 │
│  [    Login    ]                │
│                                 │
└─────────────────────────────────┘
```

### Dashboard
```
┌──────────────────────────────────────────────┐
│  MedAssist - City Health Clinic              │
│  👤 admin@cityhealthclinic.com    [Logout]  │
├──────────────────────────────────────────────┤
│                                              │
│  🔴 CRITICAL (2)  🟠 HIGH (5)               │
│  🟡 MEDIUM (12)   🟢 LOW (8)                │
│                                              │
│  Filters: [All] [Active] [Resolved]         │
│  Search: [_____________] 🔍                  │
│                                              │
│  Patient Queue:                              │
│  ┌──────────────────────────────────────┐   │
│  │ 🔴 John Doe                          │   │
│  │    I have severe chest pain...       │   │
│  │    5 mins ago         [View Chat]    │   │
│  └──────────────────────────────────────┘   │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Questions?

Backend API Docs: See BACKEND_PRD.md  
AI Service: https://medassist-ai-service.onrender.com/docs
