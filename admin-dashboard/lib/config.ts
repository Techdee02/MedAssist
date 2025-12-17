/**
 * API Endpoint Configuration
 * Centralized location for all backend API endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

export const API_ROUTES = {
  // Authentication
  AUTH: {
    LOGIN: `${API_BASE_URL}/api/auth/login`,
    REFRESH: `${API_BASE_URL}/api/auth/refresh`,
    LOGOUT: `${API_BASE_URL}/api/auth/logout`,
  },
  
  // Conversations
  CONVERSATIONS: {
    LIST: `${API_BASE_URL}/api/conversations`,
    GET: (id: string) => `${API_BASE_URL}/api/conversations/${id}`,
    UPDATE: (id: string) => `${API_BASE_URL}/api/conversations/${id}`,
  },
  
  // Messages
  MESSAGES: {
    SEND: `${API_BASE_URL}/api/send-message`, // Backend uses /api/send-message
  },
  
  // Patients (future)
  PATIENTS: {
    LIST: `${API_BASE_URL}/api/patients`,
    GET: (id: string) => `${API_BASE_URL}/api/patients/${id}`,
  },
}

export { API_BASE_URL }
