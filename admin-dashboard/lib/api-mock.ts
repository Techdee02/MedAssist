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
    clinicId: string
    role: string
  }
}

// ============================================================================
// Backend Response Types (what backend actually returns)
// ============================================================================

interface BackendConversation {
  conversation_id?: string
  id?: string
  patient_phone: string
  patient_name?: string
  patient_id?: string
  clinic_id: string
  messages: BackendMessage[]
  triage_level: string
  status?: string
  last_message_at?: string
  created_at?: string
}

interface BackendMessage {
  id?: string
  role: string
  content: string
  timestamp: string
  triage_level?: string
}

// ============================================================================
// Data Transformation Layer
// ============================================================================

function transformMessage(msg: BackendMessage): Message {
  return {
    id: msg.id || `msg_${Date.now()}_${Math.random()}`,
    role: msg.role.toUpperCase() as MessageRole,
    content: msg.content,
    timestamp: msg.timestamp,
    triageLevel: msg.triage_level?.toUpperCase() as TriageLevel | undefined,
  }
}

function transformConversation(conv: BackendConversation): Conversation {
  const id = conv.conversation_id || conv.id || `conv_${Date.now()}`
  
  return {
    id,
    patientId: conv.patient_id || `patient_${id}`,
    patientName: conv.patient_name || conv.patient_phone || 'Unknown Patient',
    patientPhone: conv.patient_phone,
    clinicId: conv.clinic_id,
    messages: conv.messages?.map(transformMessage) || [],
    triageLevel: conv.triage_level?.toUpperCase() as TriageLevel || TriageLevel.LOW,
    status: (conv.status as 'active' | 'resolved') || 'active',
    lastMessageAt: conv.last_message_at || conv.messages?.[conv.messages.length - 1]?.timestamp || new Date().toISOString(),
    createdAt: conv.created_at || conv.messages?.[0]?.timestamp || new Date().toISOString(),
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
      return response.map(transformConversation)
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
      throw error
    }
  },

  /**
   * Get a specific conversation by ID
   */
  getConversationById: async (id: string): Promise<Conversation> => {
    try {
      const response = await httpClient.get<BackendConversation>(
        API_ROUTES.CONVERSATIONS.GET(id)
      )
      return transformConversation(response)
    } catch (error) {
      console.error('Failed to fetch conversation:', error)
      throw error
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
      throw error
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
      throw error
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

// ============================================================================
// Development Mode - Fallback to Mock Data
// ============================================================================

const USE_MOCK_DATA = process.env.NEXT_PUBLIC_USE_MOCK === 'true'

if (USE_MOCK_DATA && typeof window !== 'undefined') {
  console.warn('⚠️  Using MOCK data - set NEXT_PUBLIC_USE_MOCK=false for real API')
}

// Export mock API for development/testing (optional)
export { api as default }
