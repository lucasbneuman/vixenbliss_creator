"use client"

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar
} from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface RevenueData {
  date: string
  layer1: number
  layer2: number
  layer3: number
  total: number
}

interface RevenueChartProps {
  data: RevenueData[]
  chartType?: "area" | "bar"
  title?: string
  description?: string
}

export function RevenueChart({
  data,
  chartType = "area",
  title = "Revenue Breakdown",
  description = "Daily revenue by subscription tier"
}: RevenueChartProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-950/90 border border-white/10 p-4 rounded-xl shadow-lg">
          <p className="text-sm font-medium text-high mb-2">{label}</p>
          {payload.reverse().map((entry: any) => (
            <div key={entry.dataKey} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-xs text-soft">{entry.name}</span>
              </div>
              <span className="text-sm font-semibold" style={{ color: entry.color }}>
                {formatCurrency(entry.value)}
              </span>
            </div>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <Card className="panel-glow">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          {chartType === "area" ? (
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorLayer1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorLayer2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorLayer3" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#243447" />
              <XAxis
                dataKey="date"
                stroke="#93a4ba"
                style={{ fontSize: "12px" }}
              />
              <YAxis
                stroke="#93a4ba"
                style={{ fontSize: "12px" }}
                tickFormatter={formatCurrency}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: "12px", paddingTop: "20px" }}
                iconType="circle"
              />
              <Area
                type="monotone"
                dataKey="layer1"
                stackId="1"
                stroke="#22c55e"
                fill="url(#colorLayer1)"
                name="Layer 1 ($9-19)"
              />
              <Area
                type="monotone"
                dataKey="layer2"
                stackId="1"
                stroke="#38bdf8"
                fill="url(#colorLayer2)"
                name="Layer 2 ($29-99)"
              />
              <Area
                type="monotone"
                dataKey="layer3"
                stackId="1"
                stroke="#f59e0b"
                fill="url(#colorLayer3)"
                name="Layer 3 (VIP)"
              />
            </AreaChart>
          ) : (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#243447" />
              <XAxis
                dataKey="date"
                stroke="#93a4ba"
                style={{ fontSize: "12px" }}
              />
              <YAxis
                stroke="#93a4ba"
                style={{ fontSize: "12px" }}
                tickFormatter={formatCurrency}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: "12px", paddingTop: "20px" }}
                iconType="circle"
              />
              <Bar dataKey="layer1" stackId="a" fill="#22c55e" name="Layer 1 ($9-19)" />
              <Bar dataKey="layer2" stackId="a" fill="#38bdf8" name="Layer 2 ($29-99)" />
              <Bar dataKey="layer3" stackId="a" fill="#f59e0b" name="Layer 3 (VIP)" />
            </BarChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

interface ConversionFunnelProps {
  data: {
    stage: string
    count: number
    conversionRate?: number
  }[]
}

export function ConversionFunnel({ data }: ConversionFunnelProps) {
  return (
    <Card className="panel">
      <CardHeader>
        <CardTitle>Conversion Funnel</CardTitle>
        <CardDescription>Free to VIP conversion flow</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {data.map((stage, index) => {
            const maxCount = data[0].count
            const widthPercent = (stage.count / maxCount) * 100

            return (
              <div key={stage.stage} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{stage.stage}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-soft">
                      {stage.count.toLocaleString()} users
                    </span>
                    {stage.conversionRate !== undefined && (
                      <span className="text-emerald-300 font-semibold">
                        {stage.conversionRate.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
                <div className="h-10 bg-white/10 rounded-lg overflow-hidden">
                  <div
                    className={`h-full rounded-lg transition-all ${
                      index === 0 ? "bg-slate-600" :
                      index === 1 ? "bg-emerald-500" :
                      index === 2 ? "bg-sky-500" :
                      "bg-amber-500"
                    }`}
                    style={{ width: `${widthPercent}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
