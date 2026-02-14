import type { Metadata } from 'next'
import { Sora, Source_Sans_3 } from 'next/font/google'
import './globals.css'
import { Toaster } from 'sonner'

const sora = Sora({ subsets: ['latin'], variable: '--font-display' })
const sourceSans = Source_Sans_3({ subsets: ['latin'], variable: '--font-body' })

export const metadata: Metadata = {
  title: 'Vixen Bliss Creator - Industrial Monetization Platform',
  description: 'AI-powered content generation and monetization system at scale',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${sourceSans.variable} ${sora.variable} font-body`}>
        <div className="app-shell">
          <main className="flex-1 overflow-y-auto">
            <div className="page-container">
              {children}
            </div>
          </main>
        </div>

        <Toaster
          theme="dark"
          position="bottom-right"
          toastOptions={{
            style: {
              background: 'hsl(var(--card))',
              border: '1px solid rgba(255,255,255,0.06)',
              color: 'hsl(var(--card-foreground))',
            },
          }}
        />
      </body>
    </html>
  )
}
