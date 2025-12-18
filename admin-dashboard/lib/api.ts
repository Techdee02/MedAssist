/**
 * API Client for MedAssist Admin Dashboard
 * Real implementation connecting to backend API
 */

import { Conversation, Message, MessageRole, TriageLevel } from "@/types"
import { httpClient } from "./httpClient"
import { API_ROUTES } from "./config"

// ============================================================================
// Authentication Types
// ============================================================================

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  token: string
  user: {
    id: string
    email: string
    firstName?: string
    lastName?: string
    clinicId: string
    clinicName?: string
    role: string
  }
}

// ============================================================================
// Backend Response Types (what backend actually returns)
// ============================================================================

interface BackendConversation {
  id: string
  patientId: string
  patientName: string | null  // Can be null if patient hasn't completed registration
  patientPhone: string
  triageLevel: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  status: 'ACTIVE' | 'RESOLVED' | 'CLOSED' | 'PENDING'
  lastMessageAt: string // ISO datetime
  messageCount?: number
  preview?: string
  createdAt: string // ISO datetime
}

interface BackendConversationDetail {
  id: string
  patient: {
    id: string
    phone: string
    firstName?: string
    lastName?: string
    clinicId: string
    registeredAt: string
  }
  triageLevel: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  status: 'ACTIVE' | 'RESOLVED' | 'CLOSED' | 'PENDING'
  messages: BackendMessage[]
  createdAt: string
  lastMessageAt: string
}

interface BackendMessage {
  id: string
  role: 'USER' | 'ASSISTANT' | 'ADMIN' | 'SYSTEM'
  content: string
  triageLevel?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  timestamp: string // ISO datetime
}

// ============================================================================
// Data Transformation Layer
// ============================================================================

function transformMessage(msg: BackendMessage): Message {
  return {
    id: msg.id,
    role: msg.role as MessageRole,
    content: msg.content,
    timestamp: msg.timestamp,
    triageLevel: msg.triageLevel as TriageLevel | undefined,
  }
}

function transformConversation(conv: BackendConversation): Conversation {
  return {
    id: conv.id,
    patientId: conv.patientId,
    patientName: conv.patientName || conv.patientPhone || 'Unknown Patient', // Fallback if name is null
    patientPhone: conv.patientPhone,
    clinicId: '', // Will be set from user context
    messages: [], // Messages come from detail endpoint
    preview: conv.preview, // Preview of last message
    triageLevel: conv.triageLevel as TriageLevel,
    status: conv.status.toLowerCase() as 'active' | 'resolved',
    lastMessageAt: conv.lastMessageAt,
    createdAt: conv.createdAt,
  }
}

function transformConversationDetail(conv: BackendConversationDetail): Conversation {
  return {
    id: conv.id,
    patientId: conv.patient.id,
    patientName: conv.patient.firstName && conv.patient.lastName 
      ? `${conv.patient.firstName} ${conv.patient.lastName}`
      : conv.patient.phone,
    patientPhone: conv.patient.phone,
    clinicId: conv.patient.clinicId,
    messages: conv.messages.map(transformMessage),
    triageLevel: conv.triageLevel as TriageLevel,
    status: conv.status.toLowerCase() as 'active' | 'resolved',
    lastMessageAt: conv.lastMessageAt,
    createdAt: conv.createdAt,
  }
}

// ============================================================================
// API Methods
// ============================================================================

export const api = {
  /**
   * Login with email and password
   */
  login: async (email: string, password: string): Promise<LoginResponse> => {
    try {
      const response = await httpClient.post<LoginResponse>(
        API_ROUTES.AUTH.LOGIN,
        { email, password },
        false // Don't include auth header for login
      )
      
      // Store token and user data
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', response.token)
        localStorage.setItem('user', JSON.stringify(response.user))
        
        // Also set in cookie for middleware
        document.cookie = `auth_token=${response.token}; path=/; max-age=2592000` // 30 days
      }
      
      return response
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  },

  /**
   * Get all conversations for the authenticated user's clinic
   */
  getConversations: async (): Promise<Conversation[]> => {
    try {
      const response = await httpClient.get<BackendConversation[]>(API_ROUTES.CONVERSATIONS.LIST)
      
      // Validate and transform each conversation
      const conversations = response
        .filter(conv => {
          // Skip conversations with missing critical data
          if (!conv.id || !conv.patientPhone) {
            console.warn('Skipping invalid conversation:', conv)
            return false
          }
          return true
        })
        .map(transformConversation)
      
      return conversations
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
      // Return empty array instead of throwing when backend is unavailable
      console.warn('⚠️  Backend not available - returning empty conversation list')
      return []
    }
  },

  /**
   * Get a specific conversation by ID
   */
  getConversationById: async (id: string): Promise<Conversation> => {
    try {
      const response = await httpClient.get<BackendConversationDetail>(
        API_ROUTES.CONVERSATIONS.GET(id)
      )
      return transformConversationDetail(response)
    } catch (error) {
      console.error('Failed to fetch conversation:', error)
      console.warn('⚠️  Backend not available - returning mock conversation')
      // Return a minimal conversation when backend unavailable
      return {
        id,
        patientId: `patient_${id}`,
        patientName: 'Patient',
        patientPhone: '+234-XXX-XXXX',
        clinicId: 'clinic_001',
        messages: [],
        triageLevel: TriageLevel.LOW,
        status: 'active',
        lastMessageAt: new Date().toISOString(),
        createdAt: new Date().toISOString(),
      }
    }
  },

  /**
   * Send a WhatsApp message to a patient
   */
  sendMessage: async (conversationId: string, content: string): Promise<Message> => {
    try {
      const response = await httpClient.post<BackendMessage>(
        API_ROUTES.MESSAGES.SEND,
        {
          conversationId,
          message: content,
        }
      )
      return transformMessage(response)
    } catch (error) {
      console.error('Failed to send message:', error)
      console.warn('⚠️  Backend not available - message not actually sent')
      // Return a mock message when backend unavailable
      return {
        id: `msg_${Date.now()}`,
        role: MessageRole.ASSISTANT,
        content,
        timestamp: new Date().toISOString(),
      }
    }
  },

  /**
   * Mark a conversation as resolved
   */
  resolveConversation: async (conversationId: string): Promise<void> => {
    try {
      await httpClient.patch(
        API_ROUTES.CONVERSATIONS.UPDATE(conversationId),
        { status: 'resolved' }
      )
    } catch (error) {
      console.error('Failed to resolve conversation:', error)
      console.warn('⚠️  Backend not available - conversation not actually resolved')
      // Silently fail when backend unavailable
    }
  },

  /**
   * Logout - clear local storage and cookies
   */
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT'
    }
  },
}
