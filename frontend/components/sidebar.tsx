"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Target,
  Factory,
  Antenna,
  DollarSign,
  Settings,
  TrendingUp,
  Sparkles
} from "lucide-react"

const routes = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    href: "/",
  },
  {
    label: "Models",
    icon: Target,
    href: "/models",
  },
  {
    label: "Content Factory",
    icon: Factory,
    href: "/factory",
  },
  {
    label: "Distribution",
    icon: Antenna,
    href: "/distribution",
  },
  {
    label: "Revenue",
    icon: DollarSign,
    href: "/revenue",
  },
  {
    label: "Analytics",
    icon: TrendingUp,
    href: "/analytics",
  },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col h-full text-slate-100 bg-slate-950/90">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-slate-100 shadow-[0_10px_30px_rgba(16,185,129,0.35)]">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-high">Vixen Bliss Creator</h1>
            <p className="text-xs text-soft">Premium Control Center</p>
          </div>
        </Link>
      </div>

      {/* Key Metrics Summary */}
      <div className="px-5 py-5 border-b border-white/10">
        <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-soft uppercase tracking-[0.2em]">MRR</span>
            <span className="text-sm font-semibold text-emerald-300">$156.8K</span>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-xs text-soft">Models</div>
              <div className="font-semibold text-high">48</div>
            </div>
            <div>
              <div className="text-xs text-soft">Subscribers</div>
              <div className="font-semibold text-high">3,742</div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-5 space-y-1.5">
        <div className="px-2 pb-2 text-[11px] uppercase tracking-[0.25em] text-soft">
          Core
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-2 space-y-1.5">
          {routes.map((route) => {
            const isActive = pathname === route.href
            return (
              <Link
                key={route.href}
                href={route.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-colors border border-transparent",
                  isActive
                    ? "bg-white/15 text-high border-white/10 shadow-[0_10px_30px_rgba(0,0,0,0.35)]"
                    : "text-soft hover:text-high hover:bg-white/5 hover:border-white/10"
                )}
              >
                <div className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-lg",
                  isActive ? "bg-emerald-400/20 text-emerald-300" : "bg-white/5 text-soft"
                )}>
                  <route.icon className="h-5 w-5 shrink-0" />
                </div>
                <span className="text-[15px]">{route.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Bottom Section */}
      <div className="p-4 border-t border-white/10">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-soft hover:text-high hover:bg-white/5 transition-colors border border-transparent hover:border-white/10"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-soft">
            <Settings className="h-5 w-5 shrink-0" />
          </div>
          <span className="text-[15px]">Settings</span>
        </Link>

        {/* System Status */}
        <div className="mt-3 px-3 py-3 rounded-xl border border-white/10 bg-white/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] text-soft uppercase tracking-[0.2em]">Status</span>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-emerald-400"></div>
              <span className="text-xs font-semibold text-emerald-300">Live</span>
            </div>
          </div>
          <div className="h-1 bg-white/10 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-400 rounded-full" style={{ width: '99.9%' }}></div>
          </div>
          <p className="text-xs text-soft mt-1">99.9% uptime</p>
        </div>
      </div>
    </div>
  )
}
