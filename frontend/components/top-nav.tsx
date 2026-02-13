"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { getRouteLabel } from "@/components/navigation"
import { Bell, Menu, Search, UserCircle2 } from "lucide-react"

type TopNavProps = {
  onMenuToggle: () => void
}

export default function TopNav({ onMenuToggle }: TopNavProps) {
  const pathname = usePathname()
  const current = getRouteLabel(pathname)

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-background/95 backdrop-blur">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] text-soft lg:hidden"
            onClick={onMenuToggle}
            aria-label="Abrir menu"
          >
            <Menu className="h-4 w-4" />
          </button>
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-xs text-soft">
              <Link href="/" className="hover:text-high">Vixen Creator</Link>
              <span>/</span>
              <span className="truncate">{current}</span>
            </div>
            <h2 className="truncate text-sm font-semibold text-high">{current}</h2>
          </div>
        </div>

        <div className="hidden flex-1 items-center justify-center md:flex">
          <label className="flex w-full max-w-md items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2">
            <Search className="h-4 w-4 text-soft" />
            <input
              className="w-full bg-transparent text-sm text-high placeholder:text-soft focus:outline-none"
              placeholder="Buscar avatar, lote o accion..."
              aria-label="Buscar"
            />
          </label>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] text-soft hover:text-high"
            aria-label="Notificaciones"
          >
            <Bell className="h-4 w-4" />
          </button>
          <div className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1.5 text-xs text-soft">
            <UserCircle2 className="h-4 w-4 text-brand-100" />
            <span className="hidden sm:inline">Usuario</span>
          </div>
        </div>
      </div>
    </header>
  )
}
