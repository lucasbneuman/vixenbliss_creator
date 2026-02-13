"use client"

import { RevenueChart } from "@/components/revenue-chart"

export default function Home() {
  const revenueData = [
    { date: "Jan 1", layer1: 2400, layer2: 1800, layer3: 900, total: 5100 },
    { date: "Jan 2", layer1: 2600, layer2: 2100, layer3: 1200, total: 5900 },
    { date: "Jan 3", layer1: 2800, layer2: 2400, layer3: 1400, total: 6600 },
    { date: "Jan 4", layer1: 3200, layer2: 2700, layer3: 1600, total: 7500 },
    { date: "Jan 5", layer1: 3600, layer2: 3100, layer3: 1900, total: 8600 },
    { date: "Jan 6", layer1: 4100, layer2: 3600, layer3: 2300, total: 10000 },
    { date: "Jan 7", layer1: 4500, layer2: 4200, layer3: 2800, total: 11500 },
  ]

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold text-high">Panel Principal</h1>
        <p className="text-soft">
          Accesos rápidos para operar el sistema.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <a
          href="/avatars"
          className="inline-flex items-center justify-center rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-sm font-semibold text-high hover:bg-white/10"
        >
          Crear avatar
        </a>
        <a
          href="/factory"
          className="inline-flex items-center justify-center rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-sm font-semibold text-high hover:bg-white/10"
        >
          Crear contenido
        </a>
      </div>

      <h2 className="text-2xl font-semibold text-high">Revenue Breakdown</h2>
      <RevenueChart
        data={revenueData}
        title="Revenue Breakdown"
        description="Daily revenue by subscription tier"
      />
    </div>
  )
}
