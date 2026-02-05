import { cn } from "@/lib/utils"
import { CheckCircle2, AlertCircle, XCircle, Clock } from "lucide-react"
import { Badge } from "@/components/ui/badge"

export type HealthStatus = "healthy" | "warning" | "critical" | "pending"

interface HealthIndicatorProps {
  status: HealthStatus
  label?: string
  showIcon?: boolean
  showBadge?: boolean
  size?: "sm" | "md" | "lg"
  className?: string
}

export function HealthIndicator({
  status,
  label,
  showIcon = true,
  showBadge = false,
  size = "md",
  className
}: HealthIndicatorProps) {
  const getStatusConfig = () => {
    switch (status) {
      case "healthy":
        return {
          icon: CheckCircle2,
          color: "text-green-500",
          bgColor: "bg-green-500",
          borderColor: "border-green-500",
          label: label || "Healthy"
        }
      case "warning":
        return {
          icon: AlertCircle,
          color: "text-yellow-500",
          bgColor: "bg-yellow-500",
          borderColor: "border-yellow-500",
          label: label || "Warning"
        }
      case "critical":
        return {
          icon: XCircle,
          color: "text-red-500",
          bgColor: "bg-red-500",
          borderColor: "border-red-500",
          label: label || "Critical"
        }
      case "pending":
        return {
          icon: Clock,
          color: "text-soft",
          bgColor: "bg-white/20",
          borderColor: "border-white/20",
          label: label || "Pending"
        }
    }
  }

  const config = getStatusConfig()
  const Icon = config.icon

  const sizeClasses = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5"
  }

  const dotSizeClasses = {
    sm: "h-2 w-2",
    md: "h-3 w-3",
    lg: "h-4 w-4"
  }

  if (showBadge) {
    return (
      <Badge
        variant="outline"
        className={cn(
          "gap-1.5",
          config.color,
          config.borderColor,
          className
        )}
      >
        {showIcon && <Icon className={sizeClasses[size]} />}
        <span>{config.label}</span>
      </Badge>
    )
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {showIcon ? (
        <Icon className={cn(sizeClasses[size], config.color)} />
      ) : (
        <div className={cn(
          "rounded-full",
          dotSizeClasses[size],
          config.bgColor
        )} />
      )}
      {label && (
        <span className="text-sm font-medium">{config.label}</span>
      )}
    </div>
  )
}

interface HealthStatsProps {
  healthy: number
  warning: number
  critical: number
  total: number
  className?: string
}

export function HealthStats({
  healthy,
  warning,
  critical,
  total,
  className
}: HealthStatsProps) {
  return (
    <div className={cn("flex items-center gap-4", className)}>
      <div className="flex items-center gap-1.5">
        <div className="h-3 w-3 rounded-full bg-green-500" />
        <span className="text-sm font-semibold text-green-500">{healthy}</span>
        <span className="text-xs text-soft">healthy</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="h-3 w-3 rounded-full bg-yellow-500" />
        <span className="text-sm font-semibold text-yellow-500">{warning}</span>
        <span className="text-xs text-soft">warning</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="h-3 w-3 rounded-full bg-red-500" />
        <span className="text-sm font-semibold text-red-500">{critical}</span>
        <span className="text-xs text-soft">critical</span>
      </div>
      <div className="flex items-center gap-1.5 ml-auto">
        <span className="text-sm font-semibold">{total}</span>
        <span className="text-xs text-soft">total</span>
      </div>
    </div>
  )
}
