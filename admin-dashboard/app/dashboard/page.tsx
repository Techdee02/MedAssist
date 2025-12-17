"use client"

import { useState, useEffect } from "react"
import { TileCard } from "@/components/TileCard"
import { ConversationList } from "@/components/ConversationList"
import { Conversation, TriageLevel } from "@/types"
import { api } from "@/lib/api"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Filter, Loader2 } from "lucide-react"

type StatusFilter = 'all' | 'active' | 'resolved'
type TriageFilter = 'all' | TriageLevel

export default function DashboardPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('active')
  const [triageFilter, setTriageFilter] = useState<TriageFilter>('all')

  const fetchConversations = async () => {
    try {
      const data = await api.getConversations()
      setConversations(data)
    } catch (error) {
      console.error("Failed to fetch conversations", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Initial fetch
    fetchConversations()

    // Poll every 5 seconds for new messages
    const interval = setInterval(() => {
      fetchConversations()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const filteredConversations = conversations.filter(conv => {
    const matchesSearch = searchQuery === "" || 
      conv.patientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.patientPhone.includes(searchQuery)
    
    const matchesStatus = statusFilter === 'all' || conv.status === statusFilter
    const matchesTriage = triageFilter === 'all' || conv.triageLevel === triageFilter
    
    return matchesSearch && matchesStatus && matchesTriage
  })

  const stats = {
    [TriageLevel.CRITICAL]: conversations.filter(c => c.triageLevel === TriageLevel.CRITICAL && c.status === 'active').length,
    [TriageLevel.HIGH]: conversations.filter(c => c.triageLevel === TriageLevel.HIGH && c.status === 'active').length,
    [TriageLevel.MEDIUM]: conversations.filter(c => c.triageLevel === TriageLevel.MEDIUM && c.status === 'active').length,
    [TriageLevel.LOW]: conversations.filter(c => c.triageLevel === TriageLevel.LOW && c.status === 'active').length,
    TOTAL: conversations.filter(c => c.status === 'active').length
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <TileCard level={TriageLevel.CRITICAL} count={stats[TriageLevel.CRITICAL]} />
        <TileCard level={TriageLevel.HIGH} count={stats[TriageLevel.HIGH]} />
        <TileCard level={TriageLevel.MEDIUM} count={stats[TriageLevel.MEDIUM]} />
        <TileCard level={TriageLevel.LOW} count={stats[TriageLevel.LOW]} />
        <TileCard level="TOTAL" count={stats.TOTAL} />
      </div>

      {/* Filters Section */}
      <div className="glass rounded-xl border border-gray-200 p-4">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="h-5 w-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">Filters</h3>
        </div>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-2">
            <div className="flex gap-2">
              {(['all', 'active', 'resolved'] as StatusFilter[]).map((status) => (
                <Button
                  key={status}
                  variant={statusFilter === status ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatusFilter(status)}
                  className={statusFilter === status 
                    ? "bg-gradient-to-r from-blue-600 to-purple-600 border-0 text-white shadow-md" 
                    : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50 hover:text-blue-600"
                  }
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </Button>
              ))}
            </div>
            <div className="h-8 w-px bg-gray-300" />
            <div className="flex flex-wrap gap-2">
              {(['all', TriageLevel.CRITICAL, TriageLevel.HIGH, TriageLevel.MEDIUM, TriageLevel.LOW] as TriageFilter[]).map((level) => (
                <Button
                  key={level}
                  variant={triageFilter === level ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setTriageFilter(level)}
                  className={triageFilter === level 
                    ? "bg-gradient-to-r from-blue-600 to-purple-600 border-0 text-white shadow-md" 
                    : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50 hover:text-blue-600"
                  }
                >
                  {level === 'all' ? 'All Levels' : level}
                </Button>
              ))}
            </div>
          </div>
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search by name or phone..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 border-gray-300 bg-white pl-10 text-gray-900 placeholder:text-gray-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Patient Queue */}
      <ConversationList conversations={filteredConversations} />
    </div>
  )
}
