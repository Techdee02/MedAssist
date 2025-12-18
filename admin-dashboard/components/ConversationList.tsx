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
      <CardHeader className="border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50 p-3 md:p-6">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-gray-900 text-sm md:text-base">
            <MessageSquare className="h-4 w-4 md:h-5 md:w-5 text-blue-600" />
            {title}
          </CardTitle>
          <span className="rounded-full bg-blue-100 px-2 md:px-3 py-1 text-xs md:text-sm font-semibold text-blue-700">
            {conversations.length}
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
                className="group relative flex items-center justify-between gap-2 md:gap-4 p-3 md:p-4 transition-all duration-200 hover:bg-gray-50"
              >
                <div className="relative flex min-w-0 flex-1 flex-col gap-1.5 md:gap-2">
                  <div className="flex items-center gap-2 md:gap-3">
                    <div className="flex h-9 w-9 md:h-10 md:w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 text-xs md:text-sm font-bold text-white shadow-md flex-shrink-0">
                      {conv.patientName.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="font-semibold text-sm md:text-base text-gray-900 block truncate">{conv.patientName}</span>
                      <div className="mt-0.5">
                        <TriageBadge level={conv.triageLevel} />
                      </div>
                    </div>
                  </div>
                  {!compact && (
                    <>
                      <p className="line-clamp-2 text-xs md:text-sm text-gray-600">
                        {conv.preview || "No messages"}
                      </p>
                      <div className="flex items-center gap-2 md:gap-3 text-xs text-gray-500">
                        <Clock className="h-3 w-3" />
                        <span className="truncate">{formatDistanceToNow(new Date(conv.lastMessageAt), { addSuffix: true })}</span>
                        <span className="hidden sm:inline">•</span>
                        <span className="hidden sm:inline truncate">{conv.patientPhone}</span>
                      </div>
                    </>
                  )}
                </div>
                <div className="flex flex-col md:flex-row gap-1 md:gap-2 flex-shrink-0">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleCall(conv.patientPhone)}
                    className="gap-2 border-green-200 bg-green-50 text-green-700 hover:bg-green-100"
                  >
                    <Phone className="h-3.5 w-3.5 md:h-4 md:w-4" />
                    <span className="hidden sm:inline text-xs md:text-sm">Call</span>
                  </Button>
                  <Button 
                    asChild 
                    size="sm"
                    className="gap-1 md:gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md hover:shadow-lg px-2 md:px-3"
                  >
                    <Link href={`/dashboard/conversations/${conv.id}`}>
                      <MessageSquare className="h-3.5 w-3.5 md:h-4 md:w-4" />
                      <span className="hidden sm:inline text-xs md:text-sm">View</span>
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
