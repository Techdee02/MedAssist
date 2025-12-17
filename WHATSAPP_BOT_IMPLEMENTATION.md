# WhatsApp Bot Implementation Guide

**For:** Backend Java Developer  
**Service:** Twilio WhatsApp Business API  
**Tech Stack:** Spring Boot, Twilio SDK, PostgreSQL, MongoDB  
**AI Service:** https://medassist-ai-service.onrender.com

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Twilio Setup](#twilio-setup)
3. [Webhook Implementation](#webhook-implementation)
4. [Patient Registration Flow](#patient-registration-flow)
5. [AI Service Integration](#ai-service-integration)
6. [Conversation Storage](#conversation-storage)
7. [Admin Dashboard Integration](#admin-dashboard-integration)
8. [Complete Flow Examples](#complete-flow-examples)
9. [Testing Guide](#testing-guide)

---

## 1. System Overview

### Architecture

```
┌─────────────┐          ┌──────────────┐          ┌─────────────┐
│   Patient   │          │    Twilio    │          │   Backend   │
│  WhatsApp   │◄────────►│   WhatsApp   │◄────────►│  (Spring)   │
└─────────────┘          │   Gateway    │          └──────┬──────┘
                         └──────────────┘                 │
                                                          │
                                    ┌─────────────────────┼─────────────┐
                                    ▼                     ▼             ▼
                            ┌────────────┐      ┌──────────────┐  ┌──────────┐
                            │ AI Service │      │  PostgreSQL  │  │  Admin   │
                            │  (FastAPI) │      │  (Patients,  │  │Dashboard │
                            └────────────┘      │   Clinics)   │  │ (Next.js)│
                                                └──────────────┘  └──────────┘
```

### Message Flow

```
1. Patient sends WhatsApp message → Twilio receives
2. Twilio sends webhook POST request → Your backend
3. Backend checks if patient exists
   ├─ YES → Process message with AI
   └─ NO  → Start registration flow
4. Backend calls AI Service API
5. AI analyzes message, returns response + triage level
6. Backend saves conversation to database
7. Backend sends response via Twilio API
8. If CRITICAL/HIGH triage → Notify admin dashboard (WebSocket/SSE)
```

---

## 2. Twilio Setup

### Step 1: Create Twilio Account

1. Go to https://www.twilio.com/
2. Sign up for account
3. Get **FREE** sandbox WhatsApp number for testing

### Step 2: Get Credentials

From Twilio Console (https://console.twilio.com/):

```
Account SID:     ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Auth Token:      xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WhatsApp From:   whatsapp:+14155238886 (sandbox)
```

### Step 3: Configure Webhook

In Twilio Console → WhatsApp Sandbox Settings:

```
WHEN A MESSAGE COMES IN:
https://medassist-23zx.onrender.com/webhook/whatsapp
HTTP POST
```

### Step 4: Add Dependencies to `pom.xml`

```xml
<dependency>
    <groupId>com.twilio.sdk</groupId>
    <artifactId>twilio</artifactId>
    <version>9.14.1</version>
</dependency>
```

### Step 5: Configure `application.properties`

```properties
# Twilio Configuration
twilio.account.sid=${TWILIO_ACCOUNT_SID}
twilio.auth.token=${TWILIO_AUTH_TOKEN}
twilio.whatsapp.from=${TWILIO_WHATSAPP_FROM:whatsapp:+14155238886}

# AI Service
ai.service.url=https://medassist-ai-service.onrender.com
```

---

## 3. Webhook Implementation

### 3.1 Create Webhook Controller

```java
package com.medassist.controller;

import com.medassist.service.WhatsAppBotService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/webhook")
@RequiredArgsConstructor
@Slf4j
public class WebhookController {
    
    private final WhatsAppBotService whatsAppBotService;
    
    /**
     * Twilio WhatsApp webhook verification (GET)
     * Twilio sends this to verify your endpoint
     */
    @GetMapping("/whatsapp")
    public ResponseEntity<String> verifyWebhook() {
        log.info("Webhook verification request received");
        return ResponseEntity.ok("Webhook verified");
    }
    
    /**
     * Handle incoming WhatsApp messages (POST)
     * Twilio sends messages here
     */
    @PostMapping("/whatsapp")
    public ResponseEntity<String> handleWhatsAppMessage(
        @RequestParam String From,          // Patient phone: whatsapp:+234XXXXXXXXX
        @RequestParam String Body,          // Message text
        @RequestParam(required = false) String MediaUrl0  // Optional image/document
    ) {
        log.info("Received WhatsApp message from: {}", From);
        log.info("Message body: {}", Body);
        
        try {
            // Remove "whatsapp:" prefix from phone
            String patientPhone = From.replace("whatsapp:", "");
            
            // Process message asynchronously to respond quickly to Twilio
            whatsAppBotService.processIncomingMessage(patientPhone, Body, MediaUrl0);
            
            // Respond to Twilio (must be quick, < 15 seconds)
            return ResponseEntity.ok("<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>");
            
        } catch (Exception e) {
            log.error("Error processing WhatsApp message", e);
            return ResponseEntity.ok("<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>");
        }
    }
}
```

**Important Notes:**
- Response must be **< 15 seconds** or Twilio will timeout
- Use `@Async` for AI processing
- Always return TwiML XML response (even empty)

---

## 4. Patient Registration Flow

### 4.1 Predefined Messages

```java
package com.medassist.constant;

public class BotMessages {
    
    // Welcome message for new patients
    public static final String WELCOME_MESSAGE = 
        "👋 Welcome to MedAssist!\n\n" +
        "Which clinic are you registering with?\n\n" +
        "1️⃣ City Health Clinic\n" +
        "2️⃣ Green Cross Pharmacy\n" +
        "3️⃣ Life Care Hospital\n\n" +
        "Reply with the number (1, 2, or 3)";
    
    // Registration confirmation
    public static final String REGISTRATION_COMPLETE = 
        "✅ Registration complete!\n\n" +
        "You're now connected to %s.\n\n" +
        "How can we help you today?";
    
    // Invalid clinic selection
    public static final String INVALID_CLINIC = 
        "❌ Invalid selection.\n\n" +
        "Please reply with 1, 2, or 3 to select your clinic.";
    
    // Emergency detected
    public static final String EMERGENCY_ALERT = 
        "🚨 EMERGENCY DETECTED\n\n" +
        "Please call 911 immediately or go to the nearest hospital.\n\n" +
        "Your clinic has been notified.";
    
    // Generic error
    public static final String ERROR_MESSAGE = 
        "❌ Sorry, something went wrong.\n\n" +
        "Please try again or contact your clinic directly.";
}
```

### 4.2 Registration Service

```java
package com.medassist.service;

import com.medassist.entity.Patient;
import com.medassist.entity.Clinic;
import com.medassist.repository.PatientRepository;
import com.medassist.repository.ClinicRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import java.time.Duration;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class PatientRegistrationService {
    
    private final PatientRepository patientRepository;
    private final ClinicRepository clinicRepository;
    private final RedisTemplate<String, String> redisTemplate;
    
    private static final String PENDING_REG_KEY = "pending_registration:";
    
    // Clinic mapping (hardcoded for demo, should be from database)
    private static final Map<String, String> CLINIC_OPTIONS = Map.of(
        "1", "clinic_001",  // City Health Clinic
        "2", "clinic_002",  // Green Cross Pharmacy
        "3", "clinic_003"   // Life Care Hospital
    );
    
    /**
     * Check if patient exists in database
     */
    public Patient findByPhone(String phone) {
        return patientRepository.findByPhone(phone).orElse(null);
    }
    
    /**
     * Check if patient is in registration process
     */
    public boolean isPendingRegistration(String phone) {
        return redisTemplate.hasKey(PENDING_REG_KEY + phone);
    }
    
    /**
     * Mark patient as awaiting clinic selection
     */
    public void startRegistration(String phone) {
        // Store in Redis with 5-minute expiry
        redisTemplate.opsForValue().set(
            PENDING_REG_KEY + phone, 
            "awaiting_clinic", 
            Duration.ofMinutes(5)
        );
    }
    
    /**
     * Complete registration with clinic selection
     */
    public Patient completeRegistration(String phone, String clinicSelection) {
        String clinicId = CLINIC_OPTIONS.get(clinicSelection);
        
        if (clinicId == null) {
            return null;  // Invalid selection
        }
        
        Clinic clinic = clinicRepository.findById(clinicId)
            .orElseThrow(() -> new RuntimeException("Clinic not found: " + clinicId));
        
        // Create new patient
        Patient patient = new Patient();
        patient.setPhone(phone);
        patient.setClinic(clinic);
        patient.setFirstName("Patient");  // Will be updated later
        patient.setLastName(phone.substring(phone.length() - 4));  // Last 4 digits
        
        patient = patientRepository.save(patient);
        
        // Remove from pending registration
        redisTemplate.delete(PENDING_REG_KEY + phone);
        
        return patient;
    }
}
```

---

## 5. AI Service Integration

### 5.1 AI Service Client

```java
package com.medassist.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class AIServiceClient {
    
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    
    @Value("${ai.service.url}")
    private String aiServiceUrl;
    
    /**
     * Process patient message with AI
     */
    public AIResponse processMessage(
        String messageId,
        String patientId,
        String message,
        List<ConversationMessage> history
    ) {
        try {
            String url = aiServiceUrl + "/api/v1/message/process";
            
            // Build request
            Map<String, Object> request = Map.of(
                "message_id", messageId,
                "patient_id", patientId,
                "message", message,
                "conversation_history", history != null ? history : List.of()
            );
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);
            
            log.info("Calling AI service: {}", url);
            
            ResponseEntity<AIResponse> response = restTemplate.exchange(
                url,
                HttpMethod.POST,
                entity,
                AIResponse.class
            );
            
            return response.getBody();
            
        } catch (Exception e) {
            log.error("AI service call failed", e);
            
            // Fallback response
            return AIResponse.builder()
                .messageId(messageId)
                .intent("general_inquiry")
                .response("Thank you for your message. A healthcare professional will respond shortly.")
                .triageLevel("low")
                .requiresHumanReview(true)
                .timestamp(LocalDateTime.now())
                .build();
        }
    }
}

// DTOs
@Data
@Builder
class AIResponse {
    private String messageId;
    private String intent;
    private Double confidence;
    private String response;
    private Map<String, Object> extractedData;
    private String nextAction;
    private String triageLevel;
    private Boolean requiresHumanReview;
    private LocalDateTime timestamp;
}

@Data
@AllArgsConstructor
class ConversationMessage {
    private String role;  // "user" or "assistant"
    private String content;
}
```

### 5.2 Triage Level Mapping

```java
package com.medassist.enums;

public enum TriageLevel {
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL;
    
    public static TriageLevel fromString(String level) {
        if (level == null) return LOW;
        return switch (level.toLowerCase()) {
            case "critical" -> CRITICAL;
            case "high" -> HIGH;
            case "medium" -> MEDIUM;
            default -> LOW;
        };
    }
}
```

---

## 6. Conversation Storage

### 6.1 Database Entities

```java
package com.medassist.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "conversations")
@Data
public class Conversation {
    
    @Id
    private String id;  // UUID
    
    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "patient_id", nullable = false)
    private Patient patient;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private TriageLevel triageLevel = TriageLevel.LOW;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ConversationStatus status = ConversationStatus.ACTIVE;
    
    @OneToMany(mappedBy = "conversation", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Message> messages = new ArrayList<>();
    
    @Column(nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
    
    @Column(nullable = false)
    private LocalDateTime lastMessageAt = LocalDateTime.now();
    
    private LocalDateTime resolvedAt;
    private String resolvedBy;
}

@Entity
@Table(name = "messages")
@Data
public class Message {
    
    @Id
    private String id;  // UUID
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "conversation_id", nullable = false)
    private Conversation conversation;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private MessageRole role;  // USER, ASSISTANT, ADMIN, SYSTEM
    
    @Column(nullable = false, length = 5000)
    private String content;
    
    @Enumerated(EnumType.STRING)
    private TriageLevel triageLevel;
    
    @Column(nullable = false)
    private LocalDateTime timestamp = LocalDateTime.now();
}

public enum ConversationStatus {
    ACTIVE, RESOLVED, CLOSED, PENDING
}

public enum MessageRole {
    USER, ASSISTANT, ADMIN, SYSTEM
}
```

---

## 7. Admin Dashboard Integration

### 7.1 Notify Admins of Critical Cases

```java
package com.medassist.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class AdminNotificationService {
    
    private final SimpMessagingTemplate messagingTemplate;
    
    /**
     * Send real-time notification to admin dashboard
     */
    public void notifyAdmins(String clinicId, Conversation conversation) {
        try {
            // Send WebSocket notification to clinic's admins
            String destination = "/topic/clinic/" + clinicId + "/notifications";
            
            NotificationDTO notification = NotificationDTO.builder()
                .type("new_critical_case")
                .conversationId(conversation.getId())
                .patientName(conversation.getPatient().getFirstName() + " " + 
                           conversation.getPatient().getLastName())
                .patientPhone(conversation.getPatient().getPhone())
                .triageLevel(conversation.getTriageLevel().toString())
                .message("New " + conversation.getTriageLevel() + " priority patient")
                .timestamp(LocalDateTime.now())
                .build();
            
            messagingTemplate.convertAndSend(destination, notification);
            
            log.info("Sent notification to clinic {} admins", clinicId);
            
        } catch (Exception e) {
            log.error("Failed to send admin notification", e);
        }
    }
}

@Data
@Builder
class NotificationDTO {
    private String type;
    private String conversationId;
    private String patientName;
    private String patientPhone;
    private String triageLevel;
    private String message;
    private LocalDateTime timestamp;
}
```

---

## 8. Complete Flow Examples

### 8.1 Main WhatsApp Bot Service

```java
package com.medassist.service;

import com.medassist.constant.BotMessages;
import com.medassist.entity.*;
import com.medassist.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class WhatsAppBotService {
    
    private final PatientRegistrationService registrationService;
    private final AIServiceClient aiServiceClient;
    private final TwilioMessageService twilioService;
    private final ConversationRepository conversationRepository;
    private final MessageRepository messageRepository;
    private final AdminNotificationService adminNotificationService;
    
    /**
     * Process incoming WhatsApp message
     */
    @Async
    @Transactional
    public void processIncomingMessage(String phone, String messageText, String mediaUrl) {
        log.info("Processing message from: {}", phone);
        
        try {
            // 1. Check if patient exists
            Patient patient = registrationService.findByPhone(phone);
            
            if (patient == null) {
                // New patient - start registration
                handleNewPatient(phone, messageText);
                return;
            }
            
            // 2. Check if pending registration (awaiting clinic selection)
            if (registrationService.isPendingRegistration(phone)) {
                handleClinicSelection(phone, messageText);
                return;
            }
            
            // 3. Process message with AI
            handleExistingPatient(patient, messageText);
            
        } catch (Exception e) {
            log.error("Error processing message", e);
            twilioService.sendMessage(phone, BotMessages.ERROR_MESSAGE);
        }
    }
    
    /**
     * Handle message from new patient (not registered)
     */
    private void handleNewPatient(String phone, String message) {
        log.info("New patient detected: {}", phone);
        
        // Start registration process
        registrationService.startRegistration(phone);
        
        // Send welcome message with clinic options
        twilioService.sendMessage(phone, BotMessages.WELCOME_MESSAGE);
    }
    
    /**
     * Handle clinic selection during registration
     */
    private void handleClinicSelection(String phone, String selection) {
        log.info("Processing clinic selection: {}", selection);
        
        // Validate selection (1, 2, or 3)
        if (!selection.matches("[123]")) {
            twilioService.sendMessage(phone, BotMessages.INVALID_CLINIC);
            return;
        }
        
        // Complete registration
        Patient patient = registrationService.completeRegistration(phone, selection);
        
        if (patient == null) {
            twilioService.sendMessage(phone, BotMessages.INVALID_CLINIC);
            return;
        }
        
        // Send confirmation
        String confirmationMessage = String.format(
            BotMessages.REGISTRATION_COMPLETE,
            patient.getClinic().getName()
        );
        twilioService.sendMessage(phone, confirmationMessage);
    }
    
    /**
     * Handle message from existing patient
     */
    private void handleExistingPatient(Patient patient, String messageText) {
        log.info("Processing message from patient: {}", patient.getId());
        
        // 1. Get or create active conversation
        Conversation conversation = getOrCreateConversation(patient);
        
        // 2. Save patient message
        Message userMessage = saveMessage(
            conversation, 
            MessageRole.USER, 
            messageText, 
            null
        );
        
        // 3. Get conversation history
        List<ConversationMessage> history = conversation.getMessages().stream()
            .map(m -> new ConversationMessage(
                m.getRole().toString().toLowerCase(),
                m.getContent()
            ))
            .collect(Collectors.toList());
        
        // 4. Call AI service
        AIResponse aiResponse = aiServiceClient.processMessage(
            userMessage.getId(),
            patient.getId(),
            messageText,
            history
        );
        
        // 5. Update triage level if higher
        TriageLevel newTriageLevel = TriageLevel.fromString(aiResponse.getTriageLevel());
        if (newTriageLevel.ordinal() > conversation.getTriageLevel().ordinal()) {
            conversation.setTriageLevel(newTriageLevel);
            conversationRepository.save(conversation);
        }
        
        // 6. Save AI response
        saveMessage(
            conversation,
            MessageRole.ASSISTANT,
            aiResponse.getResponse(),
            newTriageLevel
        );
        
        // 7. Send response to patient
        String responseMessage = aiResponse.getResponse();
        
        // Add emergency alert if critical
        if (aiResponse.getIntent() != null && 
            aiResponse.getIntent().equalsIgnoreCase("emergency")) {
            responseMessage = BotMessages.EMERGENCY_ALERT + "\n\n" + responseMessage;
        }
        
        twilioService.sendMessage(patient.getPhone(), responseMessage);
        
        // 8. Notify admins if CRITICAL or HIGH
        if (newTriageLevel == TriageLevel.CRITICAL || newTriageLevel == TriageLevel.HIGH) {
            adminNotificationService.notifyAdmins(
                patient.getClinic().getId(),
                conversation
            );
        }
    }
    
    /**
     * Get active conversation or create new one
     */
    private Conversation getOrCreateConversation(Patient patient) {
        return conversationRepository
            .findByPatientIdAndStatus(patient.getId(), ConversationStatus.ACTIVE)
            .orElseGet(() -> {
                Conversation newConv = new Conversation();
                newConv.setId(UUID.randomUUID().toString());
                newConv.setPatient(patient);
                newConv.setTriageLevel(TriageLevel.LOW);
                newConv.setStatus(ConversationStatus.ACTIVE);
                return conversationRepository.save(newConv);
            });
    }
    
    /**
     * Save message to database
     */
    private Message saveMessage(
        Conversation conversation,
        MessageRole role,
        String content,
        TriageLevel triageLevel
    ) {
        Message message = new Message();
        message.setId(UUID.randomUUID().toString());
        message.setConversation(conversation);
        message.setRole(role);
        message.setContent(content);
        message.setTriageLevel(triageLevel);
        message.setTimestamp(LocalDateTime.now());
        
        message = messageRepository.save(message);
        
        // Update conversation last message time
        conversation.setLastMessageAt(LocalDateTime.now());
        conversationRepository.save(conversation);
        
        return message;
    }
}
```

### 8.2 Twilio Message Service

```java
package com.medassist.service;

import com.twilio.Twilio;
import com.twilio.rest.api.v2010.account.Message;
import com.twilio.type.PhoneNumber;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;

@Service
@Slf4j
public class TwilioMessageService {
    
    @Value("${twilio.account.sid}")
    private String accountSid;
    
    @Value("${twilio.auth.token}")
    private String authToken;
    
    @Value("${twilio.whatsapp.from}")
    private String fromNumber;
    
    @PostConstruct
    public void init() {
        Twilio.init(accountSid, authToken);
        log.info("Twilio initialized with account: {}", accountSid);
    }
    
    /**
     * Send WhatsApp message to patient
     */
    public void sendMessage(String toPhone, String messageBody) {
        try {
            // Ensure phone has whatsapp: prefix
            String to = toPhone.startsWith("whatsapp:") ? toPhone : "whatsapp:" + toPhone;
            
            Message message = Message.creator(
                new PhoneNumber(to),
                new PhoneNumber(fromNumber),
                messageBody
            ).create();
            
            log.info("Sent WhatsApp message: SID={}, To={}", message.getSid(), to);
            
        } catch (Exception e) {
            log.error("Failed to send WhatsApp message to: {}", toPhone, e);
            throw new RuntimeException("Failed to send WhatsApp message", e);
        }
    }
}
```

---

## 9. Testing Guide

### 9.1 Test with Twilio Sandbox

**Step 1:** Join Sandbox

Send this message from your personal WhatsApp to Twilio sandbox number:

```
join <your-sandbox-code>
```

Example: `join happy-donkey-1234`

**Step 2:** Test Registration Flow

```
Patient: Hello
Bot: 👋 Welcome to MedAssist!
     Which clinic are you registering with?
     1️⃣ City Health Clinic
     2️⃣ Green Cross Pharmacy
     3️⃣ Life Care Hospital
     Reply with the number (1, 2, or 3)

Patient: 1
Bot: ✅ Registration complete!
     You're now connected to City Health Clinic.
     How can we help you today?
```

**Step 3:** Test Symptom Flow

```
Patient: I have severe chest pain radiating to my left arm
Bot: 🚨 EMERGENCY DETECTED
     Please call 911 immediately or go to the nearest hospital.
     Your clinic has been notified.
     
     🚨 This appears to be a medical emergency...
```

**Step 4:** Test Normal Symptom

```
Patient: I have a mild headache for 2 days
Bot: Thank you for the information. Your symptoms appear manageable.
     We'll have a nurse review your case and provide guidance.
```

### 9.2 Test AI Service Directly

```bash
curl -X POST https://medassist-ai-service.onrender.com/api/v1/message/process \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "test_001",
    "patient_id": "patient_123",
    "message": "I have fever and cough for 3 days",
    "conversation_history": []
  }'
```

### 9.3 Monitor Logs

```bash
# Watch backend logs
tail -f logs/application.log | grep -i "whatsapp\|twilio\|ai"
```

---

## 10. Production Checklist

- [ ] Twilio account verified and upgraded from sandbox
- [ ] Production WhatsApp number configured
- [ ] Webhook URL set to HTTPS production URL
- [ ] Environment variables configured in Render/Railway
- [ ] Database migrations applied
- [ ] Test all triage levels (LOW, MEDIUM, HIGH, CRITICAL)
- [ ] Test registration flow with all clinics
- [ ] Verify admin notifications work
- [ ] Load test with multiple concurrent users
- [ ] Error handling and fallback responses tested

---

## 11. Common Issues & Solutions

### Issue: Webhook timeout (15 seconds)

**Solution:** Use `@Async` for AI processing:

```java
@Async
@Transactional
public void processIncomingMessage(String phone, String message, String media) {
    // Long-running AI processing here
}
```

### Issue: Duplicate messages

**Solution:** Use Redis to track processed message IDs:

```java
String messageKey = "processed:" + twilioMessageSid;
if (redisTemplate.hasKey(messageKey)) {
    return; // Already processed
}
redisTemplate.opsForValue().set(messageKey, "1", Duration.ofMinutes(10));
```

### Issue: Patient gets stuck in registration

**Solution:** Redis keys auto-expire after 5 minutes. Add manual reset:

```java
@DeleteMapping("/admin/reset-registration/{phone}")
public void resetRegistration(@PathVariable String phone) {
    redisTemplate.delete("pending_registration:" + phone);
}
```

---

## 12. Next Steps

1. **Implement webhook controller** (Section 3)
2. **Add Twilio SDK** and test sending messages
3. **Integrate AI service** (Section 5)
4. **Add database entities** (Section 6)
5. **Test end-to-end flow** with Twilio sandbox
6. **Deploy to production** and configure real WhatsApp number

---

## Support Resources

- **Twilio Docs:** https://www.twilio.com/docs/whatsapp
- **AI Service:** https://medassist-ai-service.onrender.com/docs
- **Frontend API:** https://medassist-23zx.onrender.com/swagger-ui/index.html

---

**Happy Coding! 🚀**
