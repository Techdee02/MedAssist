"use client"

import { useEffect, useState } from "react"
import { Bell, Menu } from "lucide-react"

interface HeaderProps {
  onMenuClick: () => void
}

interface User {
  id: string
  email: string
  firstName?: string
  lastName?: string
  clinicName?: string
  role: string
}

export function Header({ onMenuClick }: HeaderProps) {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    // Load user data from localStorage
    if (typeof window !== 'undefined') {
      const userData = localStorage.getItem('user')
      if (userData) {
        try {
          setUser(JSON.parse(userData))
        } catch (error) {
          console.error('Failed to parse user data:', error)
        }
      }
    }
  }, [])

  const displayName = user?.firstName && user?.lastName 
    ? `${user.firstName} ${user.lastName}`
    : user?.email?.split('@')[0] || 'Admin User'
  
  const displayClinic = user?.clinicName || 'Healthcare Provider'
  const initials = user?.firstName && user?.lastName
    ? `${user.firstName[0]}${user.lastName[0]}`.toUpperCase()
    : displayName[0]?.toUpperCase() || 'A'

  return (
    <header className="glass sticky top-0 z-10 border-b border-gray-200 px-4 md:px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button 
            onClick={onMenuClick}
            className="lg:hidden rounded-lg p-2 hover:bg-gray-100 transition-colors"
          >
            <Menu className="h-6 w-6 text-gray-700" />
          </button>
          <div>
            <h2 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Dashboard
            </h2>
            <p className="text-xs md:text-sm text-gray-600 hidden sm:block">Welcome back, {user?.firstName || 'Admin'}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 md:gap-4">
          <button className="relative rounded-full p-2 hover:bg-gray-100 transition-colors">
            <Bell className="h-5 w-5 text-gray-700" />
            <span className="absolute right-1 top-1 flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500"></span>
            </span>
          </button>
          <div className="flex items-center gap-2 md:gap-3">
            <div className="text-right hidden md:block">
              <p className="text-sm font-medium text-gray-900">{displayName}</p>
              <p className="text-xs text-gray-500">{displayClinic}</p>
            </div>
            <div className="flex h-9 w-9 md:h-10 md:w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600 text-white font-semibold shadow-md">
              {initials}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
