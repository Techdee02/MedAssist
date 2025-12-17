"use client"

import { useState } from "react"
import { Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface SendMessageFormProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function SendMessageForm({ onSend, disabled }: SendMessageFormProps) {
  const [message, setMessage] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim()) {
      onSend(message)
      setMessage("")
    }
  }

  return (
    <form onSubmit={handleSubmit} className="glass flex items-center gap-3 border-t border-gray-200 p-4">
      <Input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message..."
        disabled={disabled}
        className="flex-1 border-gray-300 bg-white text-gray-900 placeholder:text-gray-500 focus:border-blue-500"
      />
      <Button 
        type="submit" 
        size="icon" 
        disabled={disabled || !message.trim()}
        className="h-10 w-10 bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed border-0"
      >
        <Send className="h-5 w-5" />
      </Button>
    </form>
  )
}
