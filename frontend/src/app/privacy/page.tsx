'use client'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { ArrowLeft, Shield } from 'lucide-react'

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-background overflow-hidden relative">
      <div className="fixed inset-0 bg-mesh-gradient opacity-60 pointer-events-none" />
      
      <div className="max-w-3xl mx-auto px-6 py-16 relative z-10">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>
        
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-12">
          <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mb-6">
            <Shield className="w-6 h-6 text-brand-400" />
          </div>
          <h1 className="font-display font-bold text-4xl mb-3">Privacy Policy</h1>
          <p className="text-muted-foreground">Last updated: June 8, 2026</p>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ delay: 0.1 }}
          className="glass rounded-2xl p-8 space-y-6 text-sm text-muted-foreground leading-relaxed"
        >
          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">1. Data We Collect</h2>
            <p>
              We collect information to provide you with precise tax planning and AI assistance. This includes:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1">
              <li><strong>Account Information:</strong> Sign-up details provided via Clerk authentication (e.g. name, verified email).</li>
              <li><strong>Financial Input:</strong> Self-declared salary components, investment records, rent paid, and details entered into the calculator.</li>
              <li><strong>Documents:</strong> Uploaded Form 16s, salary slips, and receipts. We parse the text solely to perform tax calculations.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">2. How We Use Your Data</h2>
            <p>
              Your personal and financial data is only used to compute your tax liability, evaluate regimes (Old vs. New), and generate optimizations. We do not sell, rent, or monetize your data. All data resides securely in our database and is analyzed using sandboxed AI APIs.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">3. Security Measures</h2>
            <p>
              We prioritize the protection of your personal information. All connections are secured via HTTPS. Document analysis uses SOC 2 compliant processing engines. Your sensitive data is encrypted using AES-256 at rest.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">4. Data Deletion and Control</h2>
            <p>
              You maintain complete ownership of your data. You can delete your uploaded documents, calculations, or close your account entirely via the Settings panel at any time. Once deleted, your records are purged permanently from our database.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground mb-3">5. Disclaimer & Professional Advice</h2>
            <p>
              Maffa TaxAI is an educational and optimization assistant. It does not constitute official tax filing or professional financial audit advice. For complex scenarios, please consult a qualified Chartered Accountant.
            </p>
          </section>
        </motion.div>
      </div>
    </div>
  )
}
