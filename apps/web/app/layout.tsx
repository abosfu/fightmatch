import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'FightMatch',
  description: 'UFC matchmaking + rankings decision support tool',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

