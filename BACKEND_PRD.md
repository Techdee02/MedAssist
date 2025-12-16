# MedAssist Backend - Product Requirements Document

**Project:** WhatsApp Gateway & Admin API  
**Stack:** Java 17, Spring Boot 3.2, PostgreSQL, Redis  
**Developer:** Backend Java Team  
**Timeline:** 1 day (MVP)

---

## 1. Project Overview

Build backend services to:
- Receive WhatsApp messages via Twilio webhooks
- Route messages to existing AI Service (Python/FastAPI)
- Store conversations in MongoDB with multi-tenant isolation
- Provide REST APIs for Admin Dashboard
- Implement authentication & authorization
- Send WhatsApp replies to patients

---

## 2. System Architecture

```
Twilio WhatsApp → [Spring Boot Gateway] → AI Service (existing)
                         ↓
                    PostgreSQL + Redis
                         ↓
                  Admin Dashboard APIs
```

**Existing AI Service:** https://medassist-ai-service.onrender.com  
**Your Backend:** New Spring Boot application

---

## 3. Technical Stack

### Required
- Java 17+
- Spring Boot 3.2.x
- Spring Security + JWT
- Spring Data JPA + Hibernate
- PostgreSQL Driver
- Spring Data Redis (session management)
- Twilio Java SDK 9.x
- RestTemplate/WebClient (AI Service calls)
- Maven/Gradle

### Database
- PostgreSQL 15+ (Render/Railway/Supabase free tier)
- Redis (optional) - session cache, rate limiting

---

## 4. Core Features

### A. WhatsApp Webhook Handler
**Endpoint:** `POST /webhook/whatsapp`

```java
@PostMapping("/webhook/whatsapp")
public ResponseEntity<String> handleWhatsAppMessage(
    @RequestParam String From,      // Patient phone: +234XXXXXXXXX
    @RequestParam String Body,      // Message text
    @RequestParam String MediaUrl0  // Optional: image/document
) {
    // 1. Extract patient phone & message
    // 2. Look up patient in DB (get clinic_id)
    // 3. If new patient → start registration flow
    // 4. Call AI Service: POST /api/v1/message/process
    // 5. Store conversation in MongoDB
    // 6. Send AI response back via Twilio
    // 7. If triage CRITICAL/HIGH → notify admin via WebSocket
    
    return ResponseEntity.ok("Message received");
}
```

### B. Patient Registration Flow
When new patient contacts bot:

```java
// Check if patient exists
Patient patient = patientRepo.findByPhone(phone);

if (patient == null) {
    // Send clinic selection message
    twilioService.sendMessage(phone, 
        "Welcome! Which clinic?\n1. City Health\n2. Green Cross\nReply with number");
    
    // Store pending registration in Redis (5 min TTL)
    redis.set("pending:" + phone, "awaiting_clinic_selection");
    return;
}

// Patient exists → continue to AI service
processMessage(patient, messageBody);
```

### C. AI Service Integration

```java
@Service
public class AIServiceClient {
    private final RestTemplate restTemplate;
    private final String AI_SERVICE_URL = "https://medassist-ai-service.onrender.com";
    
    public AIResponse processMessage(ProcessMessageRequest request) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<ProcessMessageRequest> entity = new HttpEntity<>(request, headers);
        
        ResponseEntity<AIResponse> response = restTemplate.postForEntity(
            AI_SERVICE_URL + "/api/v1/message/process",
            entity,
            AIResponse.class
        );
        
        return response.getBody();
    }
}
```

### D. Admin Authentication

```java
@PostMapping("/api/auth/login")
public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest request) {
    // 1. Validate email/password (BCrypt)
    // 2. Get user's clinic_id from DB
    // 3. Generate JWT with claims: user_id, clinic_id, role
    // 4. Return token + user info
    
    String token = jwtService.generateToken(user.getId(), user.getClinicId(), user.getRole());
    return ResponseEntity.ok(new LoginResponse(token, user));
}
```

**JWT Claims:**
```json
{
  "sub": "admin_001",
  "clinic_id": "clinic_001",
  "role": "admin",
  "exp": 1735689600
}
```

### E. Conversation APIs (Multi-Tenant Secured)

```java
@GetMapping("/api/conversations")
public ResponseEntity<List<Conversation>> getConversations(
    @RequestHeader("Authorization") String token,
    @RequestParam(required = false) String status,
    @RequestParam(required = false) String triageLevel
) {
    // Extract clinic_id from JWT
    String clinicId = jwtService.getClaimFromToken(token, "clinic_id");
    
    // Query PostgreSQL - FILTER BY CLINIC_ID (security)
    Specification<Conversation> spec = (root, query, cb) -> {
        Predicate clinicPredicate = cb.equal(root.get("clinicId"), clinicId);
        
        if (status != null) {
            clinicPredicate = cb.and(clinicPredicate, cb.equal(root.get("status"), status));
        }
        if (triageLevel != null) {
            clinicPredicate = cb.and(clinicPredicate, cb.equal(root.get("triageLevel"), triageLevel));
        }
        
        return clinicPredicate;
    };
    
    List<Conversation> conversations = conversationRepo.findAll(spec, 
        Sort.by(Sort.Direction.DESC, "lastMessageAt"));
    return ResponseEntity.ok(conversations);
}
```

### F. Send WhatsApp Message

```java
@PostMapping("/api/messages/send")
public ResponseEntity<SendMessageResponse> sendMessage(
    @RequestHeader("Authorization") String token,
    @RequestBody SendMessageRequest request
) {
    String clinicId = jwtService.getClaimFromToken(token, "clinic_id");
    
    // Security: Verify conversation belongs to this clinic
    Conversation conv = conversationRepo.findById(request.getConversationId());
    if (!conv.getClinicId().equals(clinicId)) {
        throw new ForbiddenException("Access denied");
    }
    
    // Send via Twilio
    twilioService.sendMessage(conv.getPatientPhone(), request.getMessage());
    
    // Save to DB
    Message msg = new Message(conv.getId(), "admin", request.getMessage());
    conversationRepo.addMessage(conv.getId(), msg);
    
    return ResponseEntity.ok(new SendMessageResponse(true, msg.getId()));
}
```

---

## 5. Database Schema

### PostgreSQL Tables

```java
// Table: clinics
@Entity
@Table(name = "clinics")
public class Clinic {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    
    @Column(nullable = false)
    private String name;            // "City Health Clinic"
    
    private String location;
    
    @Column(name = "whatsapp_enabled")
    private boolean whatsappEnabled = true;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @OneToMany(mappedBy = "clinic")
    private List<Patient> patients;
}

// Table: patients
@Entity
@Table(name = "patients", indexes = {
    @Index(name = "idx_phone", columnList = "phone"),
    @Index(name = "idx_clinic_id", columnList = "clinic_id")
})
public class Patient {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    
    @Column(nullable = false, unique = true)
    private String phone;           // "+234XXXXXXXXX"
    
    @ManyToOne
    @JoinColumn(name = "clinic_id", nullable = false)
    private Clinic clinic;
    
    @Column(name = "first_name")
    private String firstName;
    
    @Column(name = "last_name")
    private String lastName;
    
    @Column(name = "registered_at")
    private LocalDateTime registeredAt;
}

// Table: conversations
@Entity
@Table(name = "conversations", indexes = {
    @Index(name = "idx_clinic_id", columnList = "clinic_id"),
    @Index(name = "idx_patient_id", columnList = "patient_id"),
    @Index(name = "idx_triage_level", columnList = "triage_level")
})
public class Conversation {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    
    @ManyToOne
    @JoinColumn(name = "patient_id", nullable = false)
    private Patient patient;
    
    @ManyToOne
    @JoinColumn(name = "clinic_id", nullable = false)
    private Clinic clinic;
    
    @Column(name = "session_id")
    private String sessionId;
    
    @OneToMany(mappedBy = "conversation", cascade = CascadeType.ALL)
    private List<Message> messages;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "triage_level")
    private TriageLevel triageLevel;  // CRITICAL, HIGH, MEDIUM, LOW
    
    @Enumerated(EnumType.STRING)
    private ConversationStatus status = ConversationStatus.ACTIVE;
    
    @Column(name = "last_message_at")
    private LocalDateTime lastMessageAt;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
}

// Table: messages
@Entity
@Table(name = "messages")
public class Message {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    
    @ManyToOne
    @JoinColumn(name = "conversation_id", nullable = false)
    private Conversation conversation;
    
    @Enumerated(EnumType.STRING)
    private MessageRole role;       // USER, ASSISTANT, ADMIN
    
    @Column(columnDefinition = "TEXT")
    private String content;
    
    private LocalDateTime timestamp;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "triage_level")
    private TriageLevel triageLevel;
}

// Table: admin_users
@Entity
@Table(name = "admin_users")
public class AdminUser {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    
    @Column(nullable = false, unique = true)
    private String email;
    
    @Column(name = "password_hash", nullable = false)
    private String passwordHash;    // BCrypt
    
    @ManyToOne
    @JoinColumn(name = "clinic_id", nullable = false)
    private Clinic clinic;
    
    @Enumerated(EnumType.STRING)
    private UserRole role;          // ADMIN, NURSE, DOCTOR
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
}
```

---

## 6. API Specifications

### Base URL: `https://api.medassist.com`

### Public Endpoints
```
POST   /webhook/whatsapp           # Twilio webhook (no auth)
POST   /api/auth/login             # Admin login
POST   /api/auth/refresh           # Refresh JWT token
```

### Protected Endpoints (Require JWT)
```
GET    /api/conversations          # List conversations (filtered by clinic)
GET    /api/conversations/:id      # Get conversation details
POST   /api/messages/send          # Send WhatsApp message
PATCH  /api/conversations/:id      # Update status/notes
GET    /api/patients               # List patients (filtered by clinic)
POST   /api/patients               # Register new patient
GET    /api/analytics              # Clinic analytics
```

### Request/Response Examples

**POST /api/auth/login**
```json
Request:
{
  "email": "admin@cityhealthclinic.com",
  "password": "SecurePass123!"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "admin_001",
    "email": "admin@cityhealthclinic.com",
    "clinicId": "clinic_001",
    "role": "admin"
  }
}
```

**GET /api/conversations?triageLevel=CRITICAL**
```json
Response:
[
  {
    "id": "conv_123",
    "patientId": "patient_456",
    "patientName": "John Doe",
    "patientPhone": "+234-XXX-1111",
    "triageLevel": "CRITICAL",
    "status": "active",
    "lastMessageAt": "2025-12-16T17:30:00Z",
    "messageCount": 5,
    "preview": "I have severe chest pain..."
  }
]
```

---

## 7. Security Requirements

### Must Implement

1. **JWT Authentication**
   - Sign tokens with HS256 + secret key
   - Include: user_id, clinic_id, role
   - Expiry: 24 hours
   - Refresh token support

2. **Multi-Tenant Isolation**
   - ALL queries MUST filter by clinic_id from JWT
   - Verify clinic_id before any update/delete operation
   - Never trust clinic_id from request body

3. **Input Validation**
   - Validate phone numbers (E.164 format)
   - Sanitize message content
   - Rate limiting (10 req/sec per clinic)

4. **Audit Logging**
   - Log all admin actions (who, what, when)
   - Log all patient data access
   - Store in MongoDB audit_logs collection

5. **CORS Configuration**
   - Allow admin dashboard domain only
   - Whitelist Twilio webhook IPs

---

## 8. Integration Points

### A. Twilio WhatsApp
```java
// application.properties
twilio.account.sid=AC...
twilio.auth.token=...
twilio.whatsapp.number=whatsapp:+14155238886

// Send message
Message message = Message.creator(
    new PhoneNumber("whatsapp:+234XXXXXXXXX"),
    new PhoneNumber("whatsapp:+14155238886"),
    "Your message here"
).create();
```

### B. Existing AI Service
```java
// Call AI Service
POST https://medassist-ai-service.onrender.com/api/v1/message/process
Content-Type: application/json

{
  "message_id": "msg_001",
  "patient_id": "patient_123",
  "session_id": "session_abc",
  "message": "I have a headache"
}

// Response
{
  "intent": "symptom_inquiry",
  "response": "Thank you for sharing...",
  "triage_level": "MEDIUM",
  "confidence": 0.95
}
```

---

## 9. Configuration

### application.yml
```yaml
server:
  port: 8080

spring:
  datasource:
    url: ${DATABASE_URL}
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
    driver-class-name: org.postgresql.Driver
  
  jpa:
    hibernate:
      ddl-auto: validate  # Use Flyway for migrations
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true
    show-sql: false
  
  redis:
    host: ${REDIS_HOST:localhost}
    port: 6379

twilio:
  account-sid: ${TWILIO_ACCOUNT_SID}
  auth-token: ${TWILIO_AUTH_TOKEN}
  whatsapp-number: ${TWILIO_WHATSAPP_NUMBER}

ai-service:
  base-url: https://medassist-ai-service.onrender.com

jwt:
  secret: ${JWT_SECRET}
  expiration: 86400000  # 24 hours
```

---

## 10. Deliverables

### Day 1 - MVP (Core Features Only)
- [ ] Project setup (Spring Boot, PostgreSQL, Twilio SDK)
- [ ] Database schema + migrations (Flyway)
- [ ] Twilio webhook endpoint (basic message receive/send)
- [ ] AI Service client integration
- [ ] Basic patient registration (auto-assign to default clinic)
- [ ] Admin login API (JWT)
- [ ] GET conversations API (filtered by clinic)
- [ ] POST send message API
- [ ] Deploy to Render/Railway

**MVP Scope:**
- Single clinic support initially (multi-tenant can be added later)
- Basic security (JWT, no advanced rate limiting)
- Manual testing (skip unit tests for now)
- Minimal error handling

**Post-MVP (Later):**
- Advanced multi-tenant features
- Comprehensive testing
- Analytics endpoints
- Audit logging
- Rate limiting

---

## 11. Testing Requirements

### Unit Tests
```java
@SpringBootTest
class ConversationServiceTest {
    
    @Test
    void shouldFilterConversationsByClinic() {
        // Admin from clinic_001 should only see their conversations
        List<Conversation> convs = service.getConversations("clinic_001");
        assertTrue(convs.stream().allMatch(c -> c.getClinicId().equals("clinic_001")));
    }
    
    @Test
    void shouldDenyAccessToOtherClinicConversation() {
        // Admin from clinic_001 tries to access clinic_002 conversation
        assertThrows(ForbiddenException.class, () -> {
            service.getConversation("clinic_001", "conv_from_clinic_002");
        });
    }
}
```

### Integration Tests
- Test Twilio webhook with mock data
- Test AI Service integration with WireMock
- Test JWT authentication flow

---

## 12. Deployment

**Platform:** Render / Railway / Heroku  
**Environment Variables:**
```bash
DATABASE_URL=postgresql://user:pass@host:5432/medassist
DB_USERNAME=postgres
DB_PASSWORD=...
REDIS_HOST=redis-xxx.render.com
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
JWT_SECRET=...
AI_SERVICE_URL=https://medassist-ai-service.onrender.com
```

**Health Check Endpoint:**
```java
@GetMapping("/health")
public ResponseEntity<HealthResponse> health() {
    return ResponseEntity.ok(new HealthResponse("healthy", "1.0.0"));
}
```

---

## 13. Success Criteria

- [ ] WhatsApp messages successfully routed to AI Service
- [ ] Conversations stored in MongoDB with clinic isolation
- [ ] Admin can login and view only their clinic's patients
- [ ] Admin can send WhatsApp replies to patients
- [ ] Zero cross-tenant data leaks (security audit passing)
- [ ] API response time < 500ms (95th percentile)
- [ ] 99% uptime during business hours

---

## Questions?

Contact: Product Team  
Existing AI Service Docs: https://medassist-ai-service.onrender.com/docs
