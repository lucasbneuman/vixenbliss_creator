import type { Metadata } from "next"
import type { ReactNode } from "react"
import { Sora, Source_Sans_3 } from "next/font/google"
import "./globals.css"
import { Toaster } from "sonner"
import AppShell from "@/components/app-shell"

const sora = Sora({ subsets: ["latin"], variable: "--font-display" })
const sourceSans = Source_Sans_3({ subsets: ["latin"], variable: "--font-body" })

export const metadata: Metadata = {
  title: "Vixen Bliss Creator",
  description: "Sistema de creacion y produccion de avatares IA",
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="es" className="dark">
      <body className={`${sourceSans.variable} ${sora.variable} font-body`}>
        <AppShell>{children}</AppShell>

        <Toaster
          theme="dark"
          position="bottom-right"
          toastOptions={{
            style: {
              background: "hsl(var(--card))",
              border: "1px solid rgba(255,255,255,0.08)",
              color: "hsl(var(--card-foreground))",
            },
          }}
        />
      </body>
    </html>
  )
}
