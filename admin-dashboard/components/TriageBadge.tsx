import { TriageLevel } from "@/types"
import { AlertCircle, TrendingUp, Clock, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface TriageBadgeProps {
  level: TriageLevel
}

const config = {
  [TriageLevel.CRITICAL]: {
    label: "Critical",
    icon: AlertCircle,
    className: "bg-red-100 text-red-700 border-red-200",
  },
  [TriageLevel.HIGH]: {
    label: "High",
    icon: TrendingUp,
    className: "bg-orange-100 text-orange-700 border-orange-200",
  },
  [TriageLevel.MEDIUM]: {
    label: "Medium",
    icon: Clock,
    className: "bg-yellow-100 text-yellow-700 border-yellow-200",
  },
  [TriageLevel.LOW]: {
    label: "Low",
    icon: CheckCircle2,
    className: "bg-green-100 text-green-700 border-green-200",
  },
}

export function TriageBadge({ level }: TriageBadgeProps) {
  const cfg = config[level]
  const Icon = cfg.icon

  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold",
      cfg.className
    )}>
      <Icon className="h-3.5 w-3.5" />
      {cfg.label}
    </span>
  )
}
