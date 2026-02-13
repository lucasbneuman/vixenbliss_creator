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

export default function TopNav() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background backdrop-blur">
      <div className="mx-auto flex max-w-[1320px] items-center gap-6 px-5 py-3.5">
        <Link href="/" className="flex items-center gap-3 group shrink-0">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] shadow-[0_8px_24px_rgba(107,33,168,0.25)]">
            <Sparkles className="h-5 w-5" />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-sm font-semibold text-high">Vixen Bliss Creator</h1>
            <p className="text-[11px] text-soft">Premium Control Center</p>
          </div>
        </Link>

        <nav className="flex flex-1 items-center justify-center gap-1.5 overflow-x-auto">
          {routes.map((route) => {
            const isActive = pathname === route.href
            return (
              <Link
                key={route.href}
                href={route.href}
                className={cn(
                  "flex items-center gap-2 rounded-full border px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "border-white/15 bg-white/10 text-white"
                    : "border-transparent text-slate-300 hover:text-white hover:bg-white/10 hover:border-white/15"
                )}
              >
                <route.icon className={cn(
                  "h-4 w-4 shrink-0",
                  isActive ? "text-[hsl(var(--primary))]" : "text-slate-300"
                )} />
                <span className="whitespace-nowrap">{route.label}</span>
              </Link>
            )
          })}
        </nav>

          <div className="hidden lg:flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200">
            <span className="h-2 w-2 rounded-full bg-[hsl(var(--primary))]"></span>
            <span className="font-semibold text-[hsl(var(--primary))]">Live</span>
          </div>
          <Link
            href="/settings"
            className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-200 hover:text-white hover:bg-white/10 transition-colors"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Link>
        </div>
      </div>
    </header>
  )
}
