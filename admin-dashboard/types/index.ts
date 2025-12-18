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
  preview?: string; // Last message preview for list view
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
