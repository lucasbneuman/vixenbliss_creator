"use client"

import { useState } from "react"
import type { ReactNode } from "react"
import Sidebar from "@/components/sidebar"
import TopNav from "@/components/top-nav"

type AppShellProps = {
  children: ReactNode
}

export default function AppShell({ children }: AppShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  const closeMobile = () => setMobileOpen(false)

  return (
    <div className="app-shell">
      <aside className="hidden lg:block shell-sidebar">
        <Sidebar />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/60"
            aria-label="Cerrar menu"
            onClick={closeMobile}
          />
          <aside className="relative h-full w-[300px] border-r border-white/10 bg-background">
            <Sidebar onNavigate={closeMobile} />
          </aside>
        </div>
      )}

      <div className="shell-main">
        <TopNav onMenuToggle={() => setMobileOpen((prev) => !prev)} />
        <main className="shell-content">
          <div className="page-container">{children}</div>
        </main>
      </div>
    </div>
  )
}
