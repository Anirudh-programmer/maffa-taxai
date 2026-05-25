'use client'
import { SignUp } from '@clerk/nextjs'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { Zap, CheckCircle2 } from 'lucide-react'

const benefits = [
  'Free AI tax consultations',
  'Old vs New regime comparison',
  'Form 16 & document analysis',
  'Personalized tax-saving tips',
  'FY 2024-25 Budget updated',
]

export default function SignUpPage() {
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
              Start saving on taxes<br />
              <span className="gradient-text">in minutes</span>
            </h2>
            <p className="text-muted-foreground mb-8">
              Join thousands of Indians who optimized their tax savings with Maffa TaxAI.
            </p>
          </motion.div>

          <div className="space-y-3">
            {benefits.map((b, i) => (
              <motion.div
                key={b}
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.08 }}
                className="flex items-center gap-3"
              >
                <CheckCircle2 className="w-4 h-4 text-brand-400 flex-shrink-0" />
                <span className="text-sm text-muted-foreground">{b}</span>
              </motion.div>
            ))}
          </div>
        </div>

        <p className="text-xs text-muted-foreground">© 2026 Maffa TaxAI. Free to start. No credit card required.</p>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          <div className="lg:hidden flex items-center gap-2 mb-8 justify-center">
            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-display font-bold text-xl">Maffa TaxAI</span>
          </div>

          <SignUp
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
              },
              layout: { socialButtonsPlacement: 'top' },
            }}
            fallbackRedirectUrl="/dashboard"
            signInUrl="/auth/sign-in"
          />

          <p className="text-center text-xs text-muted-foreground mt-6">
            Already have an account?{' '}
            <Link href="/auth/sign-in" className="text-brand-400 hover:text-brand-300 transition-colors">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}
