import { useEffect, useRef } from "react"
import { format } from "date-fns"
import { Message, MessageRole } from "@/types"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Bot, User } from "lucide-react"

interface ChatThreadProps {
  messages: Message[]
}

export function ChatThread({ messages }: ChatThreadProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
      {messages.map((msg, index) => {
        const isUser = msg.role === MessageRole.USER
        const isAdmin = msg.role === MessageRole.ADMIN
        const isAssistant = msg.role === MessageRole.ASSISTANT

        return (
          <div
            key={msg.id}
            className={cn(
              "flex w-full gap-3",
              isUser ? "justify-start" : "justify-end"
            )}
          >
            {isUser && (
              <Avatar className="h-9 w-9 border-2 border-gray-200 shadow-sm">
                <AvatarFallback className="bg-gradient-to-br from-green-500 to-emerald-600 text-white">
                  <User className="h-5 w-5" />
                </AvatarFallback>
              </Avatar>
            )}
            
            <div
              className={cn(
                "group max-w-[70%] rounded-2xl p-3 text-sm shadow-sm transition-all hover:shadow-md",
                isUser 
                  ? "bg-white border border-gray-200 text-gray-900" 
                  : isAdmin 
                    ? "bg-gradient-to-br from-blue-600 to-purple-600 text-white" 
                    : "bg-blue-50 border border-blue-200 text-gray-900"
              )}
            >
              {isAssistant && (
                <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-blue-600">
                  <Bot className="h-3 w-3" />
                  AI Assistant
                </div>
              )}
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              <div
                className={cn(
                  "mt-1.5 text-xs",
                  isUser ? "text-gray-500" : isAdmin ? "text-blue-100" : "text-blue-600"
                )}
              >
                {format(new Date(msg.timestamp), "h:mm a")}
              </div>
            </div>

            {!isUser && (
              <Avatar className="h-9 w-9 border-2 border-gray-200 shadow-sm">
                <AvatarFallback className={isAdmin 
                  ? "bg-gradient-to-br from-blue-600 to-purple-600 text-white" 
                  : "bg-gradient-to-br from-purple-500 to-pink-500 text-white"
                }>
                  {isAdmin ? "A" : <Bot className="h-5 w-5" />}
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        )
      })}
    </div>
  )
}
