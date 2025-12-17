import Link from "next/link"
import { formatDistanceToNow } from "date-fns"
import { Conversation } from "@/types"
import { TriageBadge } from "@/components/TriageBadge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Phone, MessageSquare, Clock } from "lucide-react"

interface ConversationListProps {
  conversations: Conversation[]
  title?: string
  compact?: boolean
}

export function ConversationList({ conversations, title = "Patient Queue", compact = false }: ConversationListProps) {
  const handleCall = (phone: string) => {
    window.location.href = `tel:${phone}`
  }

  return (
    <Card className="glass border-gray-200 shadow-md">
      <CardHeader className="border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <MessageSquare className="h-5 w-5 text-blue-600" />
            {title}
          </CardTitle>
          <span className="rounded-full bg-blue-100 px-3 py-1 text-sm font-semibold text-blue-700">
            {conversations.length} patient{conversations.length !== 1 ? 's' : ''}
          </span>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-gray-100">
          {conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-16 text-center">
              <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gray-100">
                <MessageSquare className="h-10 w-10 text-gray-400" />
              </div>
              <p className="text-sm text-gray-500">No conversations found</p>
            </div>
          ) : (
            conversations.map((conv, index) => (
              <div 
                key={conv.id} 
                className="group relative flex items-center justify-between gap-4 p-4 transition-all duration-200 hover:bg-gray-50"
              >
                <div className="relative flex min-w-0 flex-1 flex-col gap-2">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 text-sm font-bold text-white shadow-md">
                      {conv.patientName.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="font-semibold text-gray-900">{conv.patientName}</span>
                      <div className="mt-0.5">
                        <TriageBadge level={conv.triageLevel} />
                      </div>
                    </div>
                  </div>
                  {!compact && (
                    <>
                      <p className="line-clamp-2 text-sm text-gray-600">
                        {conv.messages[conv.messages.length - 1]?.content || "No messages"}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <Clock className="h-3 w-3" />
                        <span>{formatDistanceToNow(new Date(conv.lastMessageAt), { addSuffix: true })}</span>
                        <span>•</span>
                        <span>{conv.patientPhone}</span>
                      </div>
                    </>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleCall(conv.patientPhone)}
                    className="gap-2 border-green-200 bg-green-50 text-green-700 hover:bg-green-100"
                  >
                    <Phone className="h-4 w-4" />
                  </Button>
                  <Button 
                    asChild 
                    size="sm"
                    className="gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md hover:shadow-lg"
                  >
                    <Link href={`/dashboard/conversations/${conv.id}`}>
                      <MessageSquare className="h-4 w-4" />
                      <span className="hidden sm:inline">View</span>
                    </Link>
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
