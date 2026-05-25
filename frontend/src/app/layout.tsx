import type { Metadata } from 'next'
import { ClerkProvider } from '@clerk/nextjs'
import { Toaster } from 'react-hot-toast'
import { ThemeProvider } from '@/components/ThemeProvider'
import '../styles/globals.css'

export const metadata: Metadata = {
  title: 'Maffa TaxAI – AI-Powered Indian Tax Advisor',
  description: 'Smart AI tax advisor for Indian taxpayers. Calculate taxes, compare regimes, get personalized recommendations and optimize your tax savings.',
  keywords: 'tax calculator, income tax India, old vs new regime, tax saving, Form 16, ITR filing',
  openGraph: {
    title: 'Maffa TaxAI – AI-Powered Indian Tax Advisor',
    description: 'Calculate, compare and optimize your Indian income tax with AI',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <head>
          <link rel="preconnect" href="https://fonts.googleapis.com" />
          <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
          <link
            href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Mono:wght@400;500&family=Syne:wght@600;700;800&display=swap"
            rel="stylesheet"
          />
        </head>
        <body className="font-sans antialiased bg-background text-foreground">
          <ThemeProvider>
            {children}
          </ThemeProvider>
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: 'hsl(222 47% 9%)',
                color: 'hsl(210 40% 96%)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '12px',
                fontSize: '14px',
              },
              success: { iconTheme: { primary: '#14b8a6', secondary: '#042f2e' } },
              error: { iconTheme: { primary: '#ef4444', secondary: '#1a0000' } },
            }}
          />
        </body>
      </html>
    </ClerkProvider>
  )
}
