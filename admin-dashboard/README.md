# MedAssist Admin Dashboard

A professional, feature-rich admin dashboard for managing patient conversations and triage levels in healthcare clinics.

## 🚀 Features

### Authentication
- ✅ Secure login with JWT
- ✅ Remember Me functionality (30-day sessions)
- ✅ Auto-redirect for authenticated users
- ✅ Protected routes with middleware

### Dashboard
- ✅ Real-time triage statistics
- ✅ Color-coded urgency levels (Critical, High, Medium, Low)
- ✅ Patient queue with smart filtering
- ✅ Search by name or phone number
- ✅ Status filters (Active/Resolved)
- ✅ Triage level filters

### Conversation View
- ✅ WhatsApp-style 3-panel layout
- ✅ Left: Active conversations sidebar
- ✅ Center: Message thread
- ✅ Right: Patient info & actions
- ✅ Send messages as admin
- ✅ AI recommendations display
- ✅ Symptom summary

### Patient Management
- ✅ Patient information cards
- ✅ Call patient directly (tel: links)
- ✅ Mark conversations as resolved
- ✅ Escalate to doctor
- ✅ Schedule appointments

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

## 🔐 Demo Credentials

For demonstration purposes, the app accepts **any email and password**.

Example:
- Email: `admin@clinic.com`
- Password: `anything`

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
```bash
# .env.local
NEXT_PUBLIC_API_URL=https://your-api-url.com
```

## 📊 Mock Data

The app includes a mock API (`lib/api.ts`) with:
- 3 sample conversations
- Different triage levels
- Simulated network delays
- In-memory state management

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

## 🎯 Next Steps (Post-MVP)

- [ ] Connect to real backend API
- [ ] Implement WebSocket for real-time updates
- [ ] Add analytics dashboard
- [ ] Patient management module
- [ ] Appointment scheduling
- [ ] Dark mode support
- [ ] Export reports
- [ ] Multi-clinic support

## 📄 License

MIT

## 👥 Support

For issues or questions, please contact the development team.

---

**Built with ❤️ for better healthcare communication**
