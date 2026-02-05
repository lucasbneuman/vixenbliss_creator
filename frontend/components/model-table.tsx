"use client"

import { useState } from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { HealthIndicator } from "@/components/health-indicator"
import { QuickActionButton } from "@/components/action-button"
import { MoreHorizontal, ArrowUpDown, TrendingUp, TrendingDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { Model } from "@/types/avatar"

interface ModelTableProps {
  models: Model[]
  onClone?: (model: Model) => void
  onKill?: (model: Model) => void
  onPause?: (model: Model) => void
  onActivate?: (model: Model) => void
  onView?: (model: Model) => void
}

type SortField = "name" | "mrr" | "arpu" | "engagement_rate" | "subscribers"
type SortDirection = "asc" | "desc"

export function ModelTable({
  models,
  onClone,
  onKill,
  onPause,
  onActivate,
  onView
}: ModelTableProps) {
  const [sortField, setSortField] = useState<SortField>("mrr")
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc")

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("desc")
    }
  }

  const sortedModels = [...models].sort((a, b) => {
    const aValue = a[sortField]
    const bValue = b[sortField]

    if (typeof aValue === "string" && typeof bValue === "string") {
      return sortDirection === "asc"
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue)
    }

    return sortDirection === "asc"
      ? (aValue as number) - (bValue as number)
      : (bValue as number) - (aValue as number)
  })

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const SortButton = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-3 h-8 data-[state=open]:bg-accent"
      onClick={() => handleSort(field)}
    >
      {children}
      <ArrowUpDown className="ml-2 h-4 w-4" />
    </Button>
  )

  return (
    <div className="panel">
      <Table>
        <TableHeader>
          <TableRow className="border-white/10 hover:bg-white/5 transition-colors">
            <TableHead>
              <SortButton field="name">Model</SortButton>
            </TableHead>
            <TableHead>Niche</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Health</TableHead>
            <TableHead className="text-right">
              <SortButton field="mrr">MRR</SortButton>
            </TableHead>
            <TableHead className="text-right">
              <SortButton field="arpu">ARPU</SortButton>
            </TableHead>
            <TableHead className="text-right">
              <SortButton field="subscribers">Subscribers</SortButton>
            </TableHead>
            <TableHead className="text-right">
              <SortButton field="engagement_rate">Engagement</SortButton>
            </TableHead>
            <TableHead className="text-right">Content</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedModels.length === 0 ? (
            <TableRow>
              <TableCell colSpan={10} className="h-24 text-center text-soft">
                No models found
              </TableCell>
            </TableRow>
          ) : (
            sortedModels.map((model, index) => (
              <TableRow
                key={model.id}
                className="border-white/10 hover:bg-white/10 cursor-pointer transition-all duration-200 group"
                onClick={() => onView?.(model)}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <TableCell className="font-medium">
                  <div className="flex flex-col">
                    <span>{model.name}</span>
                    <span className="text-xs text-soft">ID: {model.id.slice(0, 8)}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-xs border-white/10 bg-white/10">
                    {model.niche}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={
                      model.status === "active" ? "default" :
                      model.status === "paused" ? "secondary" :
                      "outline"
                    }
                    className={cn(
                      model.status === "active" && "bg-emerald-500/70 hover:bg-emerald-500",
                      model.status === "paused" && "bg-yellow-600 hover:bg-yellow-700",
                      model.status === "archived" && "bg-slate-600 hover:bg-slate-700"
                    )}
                  >
                    {model.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <HealthIndicator status={model.health} showBadge />
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex flex-col items-end">
                    <span className="font-semibold text-emerald-300">
                      {formatCurrency(model.mrr)}
                    </span>
                    {model.performance_delta !== undefined && (
                      <div className="flex items-center gap-1 text-xs">
                        {model.performance_delta > 0 ? (
                          <>
                            <TrendingUp className="h-3 w-3 text-emerald-400" />
                            <span className="text-emerald-300">+{model.performance_delta}%</span>
                          </>
                        ) : (
                          <>
                            <TrendingDown className="h-3 w-3 text-red-500" />
                            <span className="text-red-500">{model.performance_delta}%</span>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right font-medium">
                  {formatCurrency(model.arpu)}
                </TableCell>
                <TableCell className="text-right">
                  {model.subscribers.toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  <span className={cn(
                    "font-semibold",
                    model.engagement_rate >= 5 ? "text-emerald-400" :
                    model.engagement_rate >= 3 ? "text-yellow-500" :
                    "text-red-500"
                  )}>
                    {model.engagement_rate.toFixed(1)}%
                  </span>
                </TableCell>
                <TableCell className="text-right text-soft">
                  {model.content_generated}
                </TableCell>
                <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-slate-950 border-white/10">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuItem onClick={() => onView?.(model)}>
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuSeparator className="bg-slate-700" />
                      <DropdownMenuItem
                        onClick={() => onClone?.(model)}
                        className="text-blue-500"
                      >
                        Clone Model
                      </DropdownMenuItem>
                      {model.status === "active" ? (
                        <DropdownMenuItem
                          onClick={() => onPause?.(model)}
                          className="text-yellow-500"
                        >
                          Pause Model
                        </DropdownMenuItem>
                        ) : (
                          <DropdownMenuItem
                            onClick={() => onActivate?.(model)}
                            className="text-emerald-400"
                          >
                            Activate Model
                          </DropdownMenuItem>
                        )}
                      <DropdownMenuSeparator className="bg-slate-700" />
                      <DropdownMenuItem
                        onClick={() => onKill?.(model)}
                        className="text-red-500"
                      >
                        Kill Model
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}
