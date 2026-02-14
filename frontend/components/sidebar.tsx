"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { navRoutes } from "@/components/navigation"
import {
  LayoutDashboard,
  UserRound,
  Factory,
  Antenna,
  DollarSign,
  Settings,
  Sparkles,
  CircleDot,
} from "lucide-react"

type SidebarProps = {
  onNavigate?: () => void
}

const iconByPath = {
  "/": LayoutDashboard,
  "/avatars": UserRound,
  "/factory": Factory,
  "/distribution": Antenna,
  "/revenue": DollarSign,
} as const

export default function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname()

  return (
    <div className="flex h-full flex-col bg-background text-foreground">
      <div className="border-b border-white/10 px-5 py-5">
        <Link href="/" className="flex items-center gap-3" onClick={onNavigate}>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-[0_10px_30px_rgba(107,33,168,0.35)]">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-high">Vixen Creator</h1>
            <p className="text-xs text-soft">S1 + S2 Control</p>
          </div>
        </Link>
      </div>

      <div className="border-b border-white/10 px-5 py-4">
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
          <div className="flex items-center justify-between text-xs">
            <span className="uppercase tracking-[0.2em] text-soft">Estado</span>
            <span className="inline-flex items-center gap-1 text-brand-100">
              <CircleDot className="h-3 w-3" />
              Activo
            </span>
          </div>
          <p className="mt-2 text-xs text-soft">Base visual dark para Sistemas 1 y 2.</p>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4">
        <div className="mb-2 px-2 text-[11px] uppercase tracking-[0.24em] text-soft">Navegacion</div>
        <div className="space-y-1">
          {navRoutes.map((route) => {
            const Icon = iconByPath[route.href as keyof typeof iconByPath]
            const isActive = pathname === route.href
            return (
              <Link
                key={route.href}
                href={route.href}
                onClick={onNavigate}
                className={cn(
                  "flex items-center gap-3 rounded-xl border px-3 py-2.5 text-sm transition-colors",
                  isActive
                    ? "border-white/15 bg-white/10 text-high"
                    : "border-transparent text-soft hover:border-white/10 hover:bg-white/[0.04] hover:text-high"
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-lg",
                    isActive ? "bg-brand-gradient text-white" : "bg-white/[0.06] text-soft"
                  )}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <span>{route.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>

      <div className="border-t border-white/10 p-3">
        <Link
          href="/settings"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-xl border border-transparent px-3 py-2.5 text-sm text-soft transition-colors hover:border-white/10 hover:bg-white/[0.04] hover:text-high"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/[0.06]">
            <Settings className="h-4 w-4" />
          </span>
          Configuracion
        </Link>
      </div>
    </div>
  )
}
