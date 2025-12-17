import { Card } from "@/components/ui/card"
import { TriageLevel } from "@/types"
import { AlertCircle, Clock, TrendingUp, CheckCircle2, Users } from "lucide-react"

interface TileCardProps {
  level: TriageLevel | "TOTAL"
  count: number
}

const config = {
  [TriageLevel.CRITICAL]: {
    label: "Critical",
    icon: AlertCircle,
    gradient: "from-red-500 to-pink-600",
    bg: "bg-red-50",
    iconBg: "bg-red-100",
    iconColor: "text-red-600",
    text: "text-red-700"
  },
  [TriageLevel.HIGH]: {
    label: "High Priority",
    icon: TrendingUp,
    gradient: "from-orange-500 to-red-500",
    bg: "bg-orange-50",
    iconBg: "bg-orange-100",
    iconColor: "text-orange-600",
    text: "text-orange-700"
  },
  [TriageLevel.MEDIUM]: {
    label: "Medium",
    icon: Clock,
    gradient: "from-yellow-500 to-orange-500",
    bg: "bg-yellow-50",
    iconBg: "bg-yellow-100",
    iconColor: "text-yellow-600",
    text: "text-yellow-700"
  },
  [TriageLevel.LOW]: {
    label: "Low Priority",
    icon: CheckCircle2,
    gradient: "from-green-500 to-emerald-600",
    bg: "bg-green-50",
    iconBg: "bg-green-100",
    iconColor: "text-green-600",
    text: "text-green-700"
  },
  TOTAL: {
    label: "Total Active",
    icon: Users,
    gradient: "from-blue-600 to-purple-600",
    bg: "bg-blue-50",
    iconBg: "bg-blue-100",
    iconColor: "text-blue-600",
    text: "text-blue-700"
  }
}

export function TileCard({ level, count }: TileCardProps) {
  const cfg = config[level]
  const Icon = cfg.icon

  return (
    <Card className={`relative overflow-hidden group hover:shadow-lg transition-all duration-300 border border-gray-200 ${cfg.bg}`}>
      <div className="p-6">
        <div className="flex items-center justify-between">
          <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${cfg.iconBg} group-hover:scale-110 transition-transform duration-300`}>
            <Icon className={`h-6 w-6 ${cfg.iconColor}`} />
          </div>
          <div className="text-right">
            <p className={`text-3xl font-bold ${cfg.text}`}>{count}</p>
            <p className="text-sm font-medium text-gray-600">{cfg.label}</p>
          </div>
        </div>
      </div>
      <div className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r ${cfg.gradient}`}></div>
    </Card>
  )
}
