/**
 * Loading State Components
 */

import { Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"

/**
 * Full page loading spinner
 */
export function LoadingSpinner({ size = 32 }: { size?: number }) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Loader2 className="animate-spin text-emerald-300" size={size} />
    </div>
  )
}

/**
 * Inline loading text
 */
export function LoadingText({ text = "Loading..." }: { text?: string }) {
  return (
    <div className="flex items-center gap-2 text-soft">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>{text}</span>
    </div>
  )
}

/**
 * Loading skeleton for cards
 */
export function LoadingCard() {
  return (
    <Card className="panel animate-pulse">
      <CardHeader>
        <div className="h-4 bg-white/10 rounded w-1/2 mb-2"></div>
        <div className="h-6 bg-white/10 rounded w-3/4"></div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="h-4 bg-white/10 rounded"></div>
          <div className="h-4 bg-white/10 rounded w-5/6"></div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Loading skeleton for table rows
 */
export function LoadingTableRow() {
  return (
    <tr className="animate-pulse">
      <td className="px-6 py-4">
        <div className="h-4 bg-white/10 rounded w-32"></div>
      </td>
      <td className="px-6 py-4">
        <div className="h-4 bg-white/10 rounded w-24"></div>
      </td>
      <td className="px-6 py-4">
        <div className="h-4 bg-white/10 rounded w-20"></div>
      </td>
      <td className="px-6 py-4">
        <div className="h-4 bg-white/10 rounded w-16"></div>
      </td>
    </tr>
  )
}
