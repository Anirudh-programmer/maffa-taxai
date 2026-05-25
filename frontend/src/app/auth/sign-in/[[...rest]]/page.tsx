'use client'
import { SignIn, useClerk, useAuth } from '@clerk/nextjs'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'
import { useEffect, Suspense } from 'react'
import { Zap, Shield, Calculator, MessageSquare } from 'lucide-react'

export default function SignInPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="w-8 h-8 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
      </div>
    }>
      <SignInContent />
    </Suspense>
  )
}

function SignInContent() {
  const { signOut } = useClerk()
  const { isSignedIn } = useAuth()
  const searchParams = useSearchParams()
  const router = useRouter()

  useEffect(() => {
    // Always sign them out when landing on the sign-in page to clear active cookies
    // and force a clean, manual credentials login and Google account-selection prompt.
    if (isSignedIn) {
      signOut().then(() => {
        router.replace('/auth/sign-in')
      })
    }
  }, [isSignedIn, signOut, router])

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left panel */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 bg-gradient-to-br from-brand-950/80 to-background border-r border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-xl">Maffa TaxAI</span>
        </div>

        <div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <h2 className="font-display font-bold text-4xl mb-4 leading-tight">
              Your AI-powered<br />
              <span className="gradient-text">Indian Tax Advisor</span>
            </h2>
            <p className="text-muted-foreground text-lg mb-10">
              Calculate taxes, compare regimes, analyze documents — all in one place.
            </p>
          </motion.div>

          <div className="space-y-4">
            {[
              { icon: Calculator, title: 'Precise Tax Calculations', desc: 'Old vs New regime with exact FY 2024-25 figures' },
              { icon: MessageSquare, title: 'AI Tax Advisor', desc: 'Gemini-powered chat with deep tax knowledge' },
              { icon: Shield, title: 'Secure & Private', desc: 'Bank-grade encryption, your data stays yours' },
            ].map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="flex items-start gap-3"
              >
                <div className="w-8 h-8 rounded-lg bg-brand-500/15 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <feature.icon className="w-4 h-4 text-brand-400" />
                </div>
                <div>
                  <p className="font-medium text-sm">{feature.title}</p>
                  <p className="text-xs text-muted-foreground">{feature.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          © 2026 Maffa TaxAI. For educational purposes. Consult a CA for complex matters.
        </p>
      </div>

      {/* Right panel - Clerk SignIn */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 mb-8 justify-center">
            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-display font-bold text-xl">Maffa TaxAI</span>
          </div>

          <SignIn
            appearance={{
              elements: {
                rootBox: 'w-full',
                card: 'bg-transparent shadow-none border-0 p-0',
                headerTitle: 'text-foreground font-display font-bold text-2xl',
                headerSubtitle: 'text-muted-foreground',
                socialButtonsBlockButton: 'bg-white/5 border border-white/10 text-foreground hover:bg-white/10 transition-all rounded-xl',
                socialButtonsBlockButtonText: 'text-sm font-medium',
                dividerLine: 'bg-white/10',
                dividerText: 'text-muted-foreground text-xs',
                formFieldLabel: 'text-sm text-muted-foreground',
                formFieldInput: 'bg-white/5 border-white/10 text-foreground rounded-xl focus:border-brand-500/50 focus:ring-0',
                formButtonPrimary: 'bg-brand-500 hover:bg-brand-400 text-white rounded-xl font-semibold transition-all',
                footerActionLink: 'text-brand-400 hover:text-brand-300',
                identityPreviewText: 'text-foreground',
                identityPreviewEditButton: 'text-brand-400',
                alertText: 'text-sm',
                formResendCodeLink: 'text-brand-400',
              },
              layout: { socialButtonsPlacement: 'top', showOptionalFields: false },
            }}
            fallbackRedirectUrl="/dashboard"
            signUpUrl="/auth/sign-up"
          />

          <p className="text-center text-xs text-muted-foreground mt-6">
            Don&apos;t have an account?{' '}
            <Link href="/auth/sign-up" className="text-brand-400 hover:text-brand-300 transition-colors">
              Sign up free
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
