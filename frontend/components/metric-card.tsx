"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
import { cn } from "@/lib/utils"

interface MetricCardProps {
  title: string
  value: string | number
  delta?: number
  deltaLabel?: string
  icon?: React.ReactNode
  trend?: "up" | "down" | "neutral"
  format?: "currency" | "number" | "percentage"
  variant?: "default" | "success" | "danger" | "warning"
  sparkline?: number[]
}

export function MetricCard({
  title,
  value,
  delta,
  deltaLabel,
  icon,
  trend,
  format = "number",
  variant = "default",
  sparkline
}: MetricCardProps) {

  const getTrendIcon = () => {
    if (trend === "up") return <TrendingUp className="h-3 w-3" />
    if (trend === "down") return <TrendingDown className="h-3 w-3" />
    return <Minus className="h-3 w-3" />
  }

  const getTrendColor = () => {
    if (trend === "up") return "text-green-500 bg-green-500/10 border-green-500/20"
    if (trend === "down") return "text-red-500 bg-red-500/10 border-red-500/20"
    return "text-soft bg-white/10 border-white/10"
  }

  const getIconColor = () => {
    switch (variant) {
      case "success": return "text-green-500"
      case "danger": return "text-red-500"
      case "warning": return "text-yellow-500"
      default: return "text-blue-500"
    }
  }

  const formatValue = (val: string | number) => {
    if (typeof val === "string") return val

    switch (format) {
      case "currency":
        return new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: "USD",
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        }).format(val)
      case "percentage":
        return `${val.toFixed(1)}%`
      default:
        return new Intl.NumberFormat("en-US").format(val)
    }
  }

  return (
    <Card className="panel hover:translate-y-[-2px] transition-transform duration-200">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-[11px] font-semibold uppercase tracking-[0.2em] text-soft">
          {title}
        </CardTitle>
        {icon && (
          <div className={cn("h-4 w-4", getIconColor())}>
            {icon}
          </div>
        )}
      </CardHeader>

      <CardContent>
        <div className="space-y-1">
          <div className="flex items-baseline gap-2">
            <div className="text-3xl font-semibold tracking-tight text-high">
              {formatValue(value)}
            </div>

            {delta !== undefined && (
              <Badge
                variant="outline"
                className={cn(
                  "gap-1 px-2 py-0.5 border-white/10 bg-white/10 text-[11px]",
                  getTrendColor()
                )}
              >
                {getTrendIcon()}
                <span className="text-xs font-medium">
                  {delta > 0 ? "+" : ""}{delta.toFixed(1)}%
                </span>
              </Badge>
            )}
          </div>

          {deltaLabel && (
            <p className="text-xs text-slate-500">
              {deltaLabel}
            </p>
          )}

          {sparkline && sparkline.length > 0 && (
            <div className="h-12 flex items-end gap-0.5 mt-3">
              {sparkline.map((value, index) => {
                const max = Math.max(...sparkline)
                const height = (value / max) * 100
                return (
                  <div
                    key={index}
                    className={cn(
                      "flex-1 rounded-sm",
                      variant === "success" ? "bg-green-500/40" :
                      variant === "danger" ? "bg-red-500/40" :
                      variant === "warning" ? "bg-yellow-500/40" :
                      "bg-blue-500/35"
                    )}
                    style={{ height: `${height}%` }}
                  />
                )
              })}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
