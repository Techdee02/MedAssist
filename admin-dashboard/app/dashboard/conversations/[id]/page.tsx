"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { ChatThread } from "@/components/ChatThread"
import { SendMessageForm } from "@/components/SendMessageForm"
import { TriageBadge } from "@/components/TriageBadge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ConversationList } from "@/components/ConversationList"
import { Conversation, Message, MessageRole, TriageLevel } from "@/types"
import { Phone, Calendar, CheckCircle, AlertTriangle, Clock, UserCircle, Loader2, Activity } from "lucide-react"
import { api } from "@/lib/api"

export default function ConversationPage() {
  const params = useParams()
  const id = params.id as string
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [allConversations, setAllConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [convData, allConvs] = await Promise.all([
          api.getConversationById(id),
          api.getConversations()
        ])
        setConversation(convData)
        setAllConversations(allConvs)
      } catch (error) {
        console.error("Failed to fetch data", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id])

  const handleSendMessage = async (content: string) => {
    if (!conversation) return

    try {
      const newMessage = await api.sendMessage(conversation.id, content)
      setConversation({
        ...conversation,
        messages: [...conversation.messages, newMessage]
      })
    } catch (error) {
      console.error("Failed to send message", error)
    }
  }

  const handleResolve = async () => {
    if (!conversation) return
    try {
      await api.resolveConversation(conversation.id)
      setConversation({ ...conversation, status: 'resolved' })
    } catch (error) {
      console.error("Failed to resolve", error)
    }
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
          <p className="text-gray-600">Loading conversation...</p>
        </div>
      </div>
    )
  }

  if (!conversation) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-gray-600">Conversation not found</div>
      </div>
    )
  }

  const aiMessages = conversation.messages.filter(m => m.role === MessageRole.ASSISTANT)
  const lastAIMessage = aiMessages[aiMessages.length - 1]

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-0 animate-fade-in">
      {/* Left Sidebar - Conversations List */}
      <div className="w-80 border-r border-gray-200 bg-white">
        <div className="h-full overflow-y-auto p-4">
          <ConversationList 
            conversations={allConversations.filter(c => c.status === 'active')} 
            title="Active Conversations"
            compact
          />
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col bg-gray-50">
        <div className="glass sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-500 shadow-md">
              <UserCircle className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{conversation.patientName}</h2>
              <p className="text-sm text-gray-600">{conversation.patientPhone}</p>
            </div>
          </div>
          <TriageBadge level={conversation.triageLevel} />
        </div>
        
        <ChatThread messages={conversation.messages} />
        
        <SendMessageForm onSend={handleSendMessage} />
      </div>

      {/* Right Sidebar - Patient Info & Actions */}
      <div className="w-80 space-y-4 overflow-y-auto border-l border-gray-200 bg-white p-4">
        <div className="glass rounded-xl border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50 px-4 py-3">
            <div className="flex items-center gap-2">
              <UserCircle className="h-5 w-5 text-blue-600" />
              <h3 className="text-base font-semibold text-gray-900">Patient Information</h3>
            </div>
          </div>
          <div className="space-y-3 p-4">
            <div className="flex items-start gap-3 group">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 shadow-sm group-hover:shadow-md transition-shadow">
                <UserCircle className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-600">Full Name</p>
                <p className="text-sm text-gray-900">{conversation.patientName}</p>
              </div>
            </div>
            <div className="flex items-start gap-3 group">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-50 shadow-sm group-hover:shadow-md transition-shadow">
                <Phone className="h-5 w-5 text-green-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-600">Phone Number</p>
                <p className="text-sm text-gray-900">{conversation.patientPhone}</p>
              </div>
            </div>
            <div className="flex items-start gap-3 group">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50 shadow-sm group-hover:shadow-md transition-shadow">
                <Calendar className="h-5 w-5 text-purple-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-600">Registration Date</p>
                <p className="text-sm text-gray-900">{new Date(conversation.createdAt).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="glass rounded-xl border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200 bg-gradient-to-r from-orange-50 to-red-50 px-4 py-3">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-orange-600" />
              <h3 className="text-base font-semibold text-gray-900">Triage Summary</h3>
            </div>
          </div>
          <div className="space-y-3 p-4">
            <div>
              <p className="mb-2 text-xs font-medium text-gray-600">Urgency Level</p>
              <TriageBadge level={conversation.triageLevel} />
            </div>
            <div>
              <p className="mb-2 text-xs font-medium text-gray-600">Symptom Summary</p>
              <p className="text-sm text-gray-700 leading-relaxed">
                {conversation.messages.find(m => m.role === MessageRole.USER)?.content || "No symptoms reported"}
              </p>
            </div>
            {lastAIMessage && (
              <div>
                <p className="mb-2 text-xs font-medium text-gray-600">AI Recommendation</p>
                <div className="rounded-lg bg-gradient-to-br from-blue-50 to-purple-50 border border-blue-200 p-3 text-sm text-blue-900">
                  {lastAIMessage.content}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="glass rounded-xl border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200 bg-gradient-to-r from-purple-50 to-pink-50 px-4 py-3">
            <h3 className="text-base font-semibold text-gray-900">Actions</h3>
          </div>
          <div className="space-y-2 p-4">
            <Button 
              className="w-full justify-start gap-2 border-gray-300 bg-white text-gray-700 hover:bg-green-50 hover:text-green-600 hover:border-green-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed" 
              variant="outline"
              onClick={handleResolve}
              disabled={conversation.status === 'resolved'}
            >
              <CheckCircle className="h-4 w-4" />
              {conversation.status === 'resolved' ? 'Resolved' : 'Mark as Resolved'}
            </Button>
            <Button className="w-full justify-start gap-2 border-gray-300 bg-white text-gray-700 hover:bg-orange-50 hover:text-orange-600 hover:border-orange-300 transition-all" variant="outline">
              <AlertTriangle className="h-4 w-4" />
              Escalate to Doctor
            </Button>
            <Button className="w-full justify-start gap-2 border-gray-300 bg-white text-gray-700 hover:bg-purple-50 hover:text-purple-600 hover:border-purple-300 transition-all" variant="outline">
              <Clock className="h-4 w-4" />
              Schedule Appointment
            </Button>
            <Button 
              className="w-full justify-start gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-md hover:shadow-lg transition-all border-0" 
              onClick={() => window.location.href = `tel:${conversation.patientPhone}`}
            >
              <Phone className="h-4 w-4" />
              Call Patient
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

