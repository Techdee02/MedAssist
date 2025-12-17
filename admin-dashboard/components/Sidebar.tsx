"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { 
  LayoutDashboard, 
  LogOut,
  Activity,
  TrendingUp,
  FileText,
  Sparkles
} from "lucide-react"

const sidebarItems = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "Patient queue & triage"
  },
  {
    title: "Analytics",
    href: "#",
    icon: TrendingUp,
    description: "Coming soon",
    disabled: true
  },
  {
    title: "Reports",
    href: "#",
    icon: FileText,
    description: "Coming soon",
    disabled: true
  }
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = () => {
    document.cookie = "auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT"
    localStorage.removeItem("user")
    router.push("/login")
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={cn(
        "fixed lg:static inset-y-0 left-0 z-50 flex h-full w-72 flex-col border-r border-gray-200 bg-white/95 backdrop-blur-xl transition-transform duration-300 lg:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
      {/* Header with gradient */}
      <div className="relative overflow-hidden border-b border-gray-200 bg-gradient-to-r from-blue-50 via-purple-50 to-blue-50 px-6 py-4">
        <Link href="/dashboard" className="relative z-10 flex items-center gap-3" onClick={onClose}>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 shadow-md">
            <Activity className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">MedAssist</h1>
            <p className="text-xs text-gray-600">Healthcare Dashboard</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-auto py-6">
        <nav className="space-y-1 px-3">
          {sidebarItems.map((item, index) => {
            const Icon = item.icon
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`)
            
            return (
              <Link
                key={`${item.title}-${index}`}
                href={item.disabled ? "#" : item.href}
                onClick={(e) => {
                  if (item.disabled) {
                    e.preventDefault()
                  } else {
                    onClose()
                  }
                }}
                className={cn(
                  "group relative flex flex-col gap-1.5 rounded-xl px-4 py-3.5 transition-all duration-300",
                  isActive 
                    ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/25" 
                    : "text-gray-700 hover:bg-gray-100 hover:text-gray-900",
                  item.disabled && "cursor-not-allowed opacity-50"
                )}
                aria-disabled={item.disabled}
              >
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-lg transition-all duration-300",
                    isActive 
                      ? "bg-white/20" 
                      : "bg-gray-100 text-gray-600 group-hover:bg-white group-hover:shadow-sm"
                  )}>
                    <Icon className={cn(
                      "h-5 w-5 transition-transform duration-300",
                      isActive ? "scale-110 text-white" : "group-hover:scale-110"
                    )} />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{item.title}</div>
                    <div className={cn(
                      "text-xs transition-colors",
                      isActive ? "text-blue-100" : "text-gray-500 group-hover:text-gray-600"
                    )}>
                      {item.description}
                    </div>
                  </div>
                  {isActive && <Sparkles className="h-4 w-4 animate-pulse text-white" />}
                </div>
                {isActive && (
                  <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-600/20 via-purple-600/20 to-blue-600/20 blur-lg -z-10 animate-pulse" />
                )}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Logout Button */}
      <div className="border-t border-gray-200 p-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-gray-700 transition-all duration-300 hover:bg-red-50 hover:text-red-600 hover:shadow-md"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 transition-colors group-hover:bg-red-100">
            <LogOut className="h-5 w-5" />
          </div>
          <div>
            <div className="font-medium">Logout</div>
            <div className="text-xs text-gray-500 group-hover:text-red-500">Sign out of account</div>
          </div>
        </button>
      </div>
    </div>
    </>
  )
}
