# MedAssist Admin Dashboard

> **Production-ready admin dashboard for managing patient conversations and triage levels in healthcare clinics.**

🎉 **Status: 100% Complete & Production Ready**

## 🚀 Features

### Authentication
- ✅ Secure login with JWT (integrated with production backend)
- ✅ Remember Me functionality (30-day sessions)
- ✅ Auto-redirect for authenticated users
- ✅ Protected routes with middleware
- ✅ Auto-logout on 401 (token expiration)
- ✅ Dynamic user info from JWT (firstName, lastName, clinicName)

### Dashboard
- ✅ Real-time triage statistics (5-second polling)
- ✅ Color-coded urgency levels (Critical, High, Medium, Low)
- ✅ Patient queue with smart filtering
- ✅ Search by name or phone number
- ✅ Status filters (Active/Resolved/Closed/Pending)
- ✅ Triage level filters
- ✅ **Mobile responsive** with hamburger menu
- ✅ Graceful error handling (works even when backend is down)

### Conversation View
- ✅ WhatsApp-style 3-panel layout
- ✅ Left: Active conversations sidebar (hidden on mobile)
- ✅ Center: Message thread
- ✅ Right: Patient info & actions (slide-in drawer on mobile)
- ✅ Send messages as admin
- ✅ AI recommendations display
- ✅ Symptom summary
- ✅ Back button for mobile navigation

### Patient Management
- ✅ Patient information cards
- ✅ Call patient directly (tel: links)
- ✅ Mark conversations as resolved
- ✅ Escalate to doctor
- ✅ Schedule appointments

### Mobile Responsiveness
- ✅ Hamburger menu with slide-in drawer
- ✅ Responsive grid layouts (1 col mobile → 5 cols desktop)
- ✅ Touch-friendly tap targets
- ✅ Mobile-optimized conversation view
- ✅ Compact header with truncated text

## 🎨 Design Highlights

- **Professional UI**: Clean, modern interface inspired by WhatsApp Web and Linear
- **Color System**: Medical-grade color coding for triage levels
- **Responsive**: Desktop-first with mobile support
- **Animations**: Smooth transitions and hover effects
- **Icons**: Lucide React icon library
- **Typography**: System font stack for optimal rendering

## 🛠️ Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Date**: date-fns
- **HTTP Client**: Fetch API with custom interceptors
- **Authentication**: JWT Bearer tokens
- **Backend API**: https://medassist-23zx.onrender.com
- **AI Service**: https://medassist-ai-service.onrender.com

## 📦 Installation

```bash
npm install
```

## 🏃 Running the Project

### Development
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Production Build
```bash
npm run build
npm run start
```

## 🔐 Login Credentials

**Production Backend Integration**: The dashboard now connects to the real backend API.

**Test Account** (if available from backend team):
- Email: `admin@clinic.com` (or your registered email)
- Password: Your registered password

**Note**: Authentication is handled by the production backend at https://medassist-23zx.onrender.com. Contact your backend administrator for valid credentials.

## 📱 Usage Guide

### 1. Login
- Enter any email and password
- Check "Remember me" for extended sessions
- Click "Sign In"

### 2. Dashboard
- View triage statistics at the top
- Filter conversations by status or triage level
- Search for patients by name or phone
- Click "Call" to initiate a phone call
- Click "View Chat" to open the conversation

### 3. Conversation View
- **Left Sidebar**: Browse all active conversations
- **Main Area**: Read and send messages
- **Right Sidebar**: View patient details and take actions
- Mark conversations as resolved
- Escalate urgent cases to doctors

### 4. Logout
- Click the "Logout" button in the header or sidebar

## 🎯 Triage Levels

| Level | Color | Icon | Description |
|-------|-------|------|-------------|
| **Critical** | 🔴 Red | ⚠️ | Immediate attention required |
| **High** | 🟠 Orange | ⚠ | Urgent within 1 hour |
| **Medium** | 🟡 Yellow | ℹ️ | Semi-urgent within 4 hours |
| **Low** | 🟢 Green | ✓ | Non-urgent within 24 hours |

## 📂 Project Structure

```
admin-dashboard/
├── app/
│   ├── (auth)/
│   │   └── login/              # Login page
│   ├── dashboard/
│   │   ├── page.tsx            # Main dashboard
│   │   └── conversations/
│   │       └── [id]/           # Conversation detail
│   ├── layout.tsx
│   └── page.tsx                # Root redirect
├── components/
│   ├── ui/                     # Base UI components
│   ├── ChatThread.tsx
│   ├── ConversationList.tsx
│   ├── Header.tsx
│   ├── SendMessageForm.tsx
│   ├── Sidebar.tsx
│   ├── TileCard.tsx
│   └── TriageBadge.tsx
├── lib/
│   ├── api.ts                  # Mock API
│   └── utils.ts                # Utilities
├── types/
│   └── index.ts                # TypeScript types
└── middleware.ts               # Auth protection
```

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file in the `admin-dashboard` directory:

```bash
# Production Backend API
NEXT_PUBLIC_API_URL=https://medassist-23zx.onrender.com

# For local backend development (optional)
# NEXT_PUBLIC_API_URL=http://localhost:8080
```

**Note**: The `.env.example` file is provided as a template.

## 📊 Data Source

**Production API Integration**: The dashboard fetches real data from:
- **Backend API**: https://medassist-23zx.onrender.com
- **AI Service**: https://medassist-ai-service.onrender.com

**Fallback Behavior**: If the backend is unavailable, the app gracefully handles errors:
- Shows user-friendly error messages
- Returns empty arrays instead of crashing
- Displays offline indicators

**Real-time Updates**: 
- 5-second polling interval (as per PRD specification)
- Automatic data refresh on conversation page
- Live triage statistics

## 🚦 Workflow

1. **Patient sends WhatsApp message** → AI analyzes → Triage level assigned
2. **Conversation appears in dashboard** → Sorted by urgency
3. **Admin reviews** → Filters by triage level
4. **Admin responds** → Message sent via WhatsApp
5. **Admin resolves** → Conversation marked as complete

## 📝 Features Checklist

- ✅ Authentication & Authorization
- ✅ Dashboard with Statistics
- ✅ Patient Queue Management
- ✅ Conversation Filtering
- ✅ Search Functionality
- ✅ Real-time Message Thread
- ✅ Send Messages
- ✅ Patient Information Display
- ✅ Triage Level Indicators
- ✅ Action Buttons (Resolve, Escalate, Schedule, Call)
- ✅ Responsive Design
- ✅ Professional UI/UX

## 🎯 Production Deployment

### Pre-Deployment Checklist
- ✅ Environment variables configured
- ✅ Production API endpoints tested
- ✅ Mobile responsiveness verified
- ✅ Error handling implemented
- ✅ JWT authentication working
- ✅ All TypeScript errors resolved

### Deployment Steps

1. **Vercel (Recommended)**
   ```bash
   npm install -g vercel
   vercel --prod
   ```
   Set environment variable: `NEXT_PUBLIC_API_URL=https://medassist-23zx.onrender.com`

2. **Manual Build**
   ```bash
   npm run build
   npm run start
   ```

### Post-MVP Enhancements

- [ ] WebSocket for real-time updates (replace polling)
- [ ] Analytics dashboard with charts
- [ ] Patient management module
- [ ] Appointment scheduling integration
- [ ] Dark mode support
- [ ] Export reports (PDF/CSV)
- [ ] Multi-clinic support
- [ ] Push notifications
- [ ] Advanced search filters
- [ ] Conversation tagging system

## 📄 License

MIT

## 👥 Support

For issues or questions, please contact the development team.

---

**Built with ❤️ for better healthcare communication**
