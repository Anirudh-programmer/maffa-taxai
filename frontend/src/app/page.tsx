'use client'
import { motion } from 'framer-motion'
import Link from 'next/link'
import {
  ArrowRight, Bot, Calculator, FileText, Shield, TrendingUp,
  Zap, ChevronRight, CheckCircle2, Star, BarChart3, Upload,
} from 'lucide-react'

const features = [
  { icon: Bot, title: 'Maffa AI Tax Assistant', desc: 'Chat with our intelligent assistant powered by the premium Maffa Core optimization engine adapted for Indian tax law.' },
  { icon: Calculator, title: 'Precise Tax Calculator', desc: 'Old vs new regime comparison with exact calculations. Never rely on estimates.' },
  { icon: FileText, title: 'Document Analysis', desc: 'Upload Form 16, salary slips, ITR PDFs. AI extracts and analyzes key tax data automatically.' },
  { icon: TrendingUp, title: 'Regime Optimizer', desc: 'Get personalized recommendation on old vs new tax regime with exact rupee savings.' },
  { icon: Shield, title: 'Maffa RAG Knowledge Base', desc: 'Answers grounded in latest Budget 2024 updates, tax sections, and Income Tax Act provisions, verified by Maffa Core.' },
  { icon: BarChart3, title: 'Analytics Dashboard', desc: 'Track your tax savings, documents, and consultations in a beautiful analytics dashboard.' },
]

const stats = [
  { value: '₹2.4L+', label: 'Avg. Tax Savings Identified' },
  { value: '15 secs', label: 'To Full Tax Analysis' },
  { value: '100%', label: 'Calculation Accuracy' },
  { value: 'FY 2024-25', label: 'Budget Updated' },
]

const testimonials = [
  { name: 'Priya Sharma', role: 'Software Engineer', company: 'Bangalore', quote: 'Saved ₹34,000 by switching to new regime. The AI explained exactly why in 2 minutes.', rating: 5 },
  { name: 'Rahul Mehta', role: 'Product Manager', company: 'Mumbai', quote: 'Finally understand what my Form 16 actually means. The document analysis is incredible.', rating: 5 },
  { name: 'Anjali Singh', role: 'Consultant', company: 'Delhi', quote: "The NPS suggestion alone saved me ₹15,600. I'd been missing this deduction for years.", rating: 5 },
]

const faqs = [
  { q: 'Is Maffa TaxAI free to use?', a: 'The basic calculator and limited AI chat are free. Premium gives unlimited AI conversations, document analysis, and PDF reports.' },
  { q: 'How accurate are the tax calculations?', a: 'Calculations use exact FY 2024-25 tax rules. We never use the AI for math — all numbers come from our Python tax engine.' },
  { q: 'Is my financial data secure?', a: 'Yes. Bank-grade encryption, no data sold, and you can delete your data anytime. Hosted on SOC 2 compliant infrastructure.' },
  { q: 'Does it support both old and new tax regime?', a: 'Yes! Maffa TaxAI calculates both regimes and tells you exactly which one saves you more money, with a detailed breakdown.' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Background effects */}
      <div className="fixed inset-0 bg-mesh-gradient opacity-60 pointer-events-none" />
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-brand-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Navbar */}
      <nav className="relative z-10 flex items-center justify-between px-6 md:px-12 py-5 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-xl">Maffa TaxAI</span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
          <a href="#features" className="hover:text-foreground transition-colors">Features</a>
          <a href="#how-it-works" className="hover:text-foreground transition-colors">How it works</a>
          <a href="#faq" className="hover:text-foreground transition-colors">FAQ</a>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/auth/sign-in" className="text-sm text-muted-foreground hover:text-foreground transition-colors px-4 py-2">
            Sign in
          </Link>
          <Link href="/auth/sign-up" className="text-sm bg-brand-500 hover:bg-brand-400 text-white px-4 py-2 rounded-lg transition-colors font-medium">
            Get Started Free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 pt-24 pb-20 px-6 text-center">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <div className="inline-flex items-center gap-2 bg-brand-500/10 border border-brand-500/20 rounded-full px-4 py-1.5 text-sm text-brand-400 mb-6">
            <Star className="w-3.5 h-3.5" />
            Updated for Budget 2024 · FY 2024-25
          </div>
          <h1 className="font-display font-bold text-5xl md:text-7xl leading-none mb-6">
            Maffa AI Tax Assistant
            <br />
            <span className="gradient-text">Built for India</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
            Calculate taxes, compare old vs new regime, analyze Form 16, and get personalized
            recommendations — powered by the Maffa Core optimization engine and precise Indian tax logic.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/auth/sign-up"
              className="group flex items-center gap-2 bg-brand-500 hover:bg-brand-400 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-200 glow-teal hover:glow-teal-strong">
              Start Free Analysis
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link href="/calculator"
              className="flex items-center gap-2 glass hover:bg-white/[0.06] border border-white/10 px-8 py-4 rounded-xl font-medium text-lg transition-all">
              <Calculator className="w-5 h-5 text-brand-400" />
              Quick Calculator
            </Link>
          </div>
        </motion.div>

        {/* Hero mockup */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mt-16 max-w-4xl mx-auto"
        >
          <div className="glass-strong rounded-2xl p-1 glow-teal">
            <div className="bg-background/80 rounded-xl overflow-hidden">
              {/* Fake browser bar */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500/50" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                  <div className="w-3 h-3 rounded-full bg-green-500/50" />
                </div>
                <div className="flex-1 bg-white/5 rounded-md text-xs text-muted-foreground text-center py-1">
                  app.taxai.in/chat
                </div>
              </div>
              {/* Fake chat UI */}
              <div className="p-6 space-y-4 min-h-[300px]">
                <div className="flex justify-end">
                  <div className="chat-message-user rounded-2xl rounded-tr-sm px-4 py-3 max-w-sm text-sm">
                    Which tax regime is better for me? I earn ₹12L/year with ₹1.5L in 80C investments.
                  </div>
                </div>
                <div className="flex gap-3 items-start">
                  <div className="w-8 h-8 rounded-lg bg-brand-500/20 border border-brand-500/30 flex items-center justify-center flex-shrink-0">
                    <Zap className="w-4 h-4 text-brand-400" />
                  </div>
                  <div className="chat-message-ai rounded-2xl rounded-tl-sm px-4 py-3 max-w-xl text-sm leading-relaxed">
                    Based on your income of <strong className="text-brand-400">₹12,00,000</strong> with ₹1.5L in 80C deductions:
                    <br /><br />
                    <strong className="text-green-400">✓ Old Regime saves you ₹18,200 more</strong>
                    <br />• Old Regime tax: <strong>₹1,56,000</strong> (effective rate: 13%)
                    <br />• New Regime tax: <strong>₹1,74,200</strong> (effective rate: 14.5%)
                    <br /><br />
                    You should also consider adding NPS contributions for an extra <strong className="text-brand-400">₹50,000 deduction</strong> under 80CCD(1B)...
                  </div>
                </div>
                <div className="flex justify-center">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-brand-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 rounded-full bg-brand-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 rounded-full bg-brand-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Stats */}
      <section className="relative z-10 py-16 px-6 border-y border-white/5">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="font-display font-bold text-3xl md:text-4xl gradient-text mb-1">{stat.value}</div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-16">
            <h2 className="font-display font-bold text-4xl md:text-5xl mb-4">Everything you need to<br /><span className="gradient-text">optimize your taxes</span></h2>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              One platform to understand, calculate, and minimize your Indian income tax.
            </p>
          </motion.div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((feat, i) => (
              <motion.div
                key={feat.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                viewport={{ once: true }}
                className="glass rounded-2xl p-6 hover:bg-white/[0.06] transition-all group"
              >
                <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mb-4 group-hover:bg-brand-500/20 transition-colors">
                  <feat.icon className="w-5 h-5 text-brand-400" />
                </div>
                <h3 className="font-semibold text-lg mb-2">{feat.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{feat.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="relative z-10 py-24 px-6 bg-white/[0.02]">
        <div className="max-w-4xl mx-auto">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-16">
            <h2 className="font-display font-bold text-4xl mb-4">Get answers in <span className="gradient-text">3 steps</span></h2>
          </motion.div>
          <div className="space-y-8">
            {[
              { step: '01', title: 'Create your account', desc: 'Sign up in seconds with Google or email. Your data is encrypted and private.', icon: Shield },
              { step: '02', title: 'Enter your income details or upload documents', desc: 'Use the tax calculator or upload your Form 16/salary slip for instant AI analysis.', icon: Upload },
              { step: '03', title: 'Get AI-powered recommendations', desc: 'Chat with our tax advisor, get regime comparison, and download your tax report.', icon: Bot },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.15 }}
                viewport={{ once: true }}
                className="flex gap-6 items-start"
              >
                <div className="flex-shrink-0 w-12 h-12 rounded-xl glass border border-white/10 flex items-center justify-center">
                  <span className="font-display font-bold text-brand-400 text-sm">{item.step}</span>
                </div>
                <div className="flex-1 pt-1">
                  <h3 className="font-semibold text-lg mb-1">{item.title}</h3>
                  <p className="text-muted-foreground">{item.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="relative z-10 py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.h2 initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
            className="font-display font-bold text-4xl text-center mb-12">
            Loved by taxpayers <span className="gradient-text">across India</span>
          </motion.h2>
          <div className="grid md:grid-cols-3 gap-5">
            {testimonials.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="glass rounded-2xl p-6"
              >
                <div className="flex gap-0.5 mb-4">
                  {Array.from({ length: t.rating }).map((_, j) => (
                    <Star key={j} className="w-4 h-4 fill-gold-400 text-gold-400" />
                  ))}
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed mb-4">"{t.quote}"</p>
                <div>
                  <div className="font-medium text-sm">{t.name}</div>
                  <div className="text-xs text-muted-foreground">{t.role} · {t.company}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="relative z-10 py-24 px-6 bg-white/[0.02]">
        <div className="max-w-2xl mx-auto">
          <h2 className="font-display font-bold text-4xl text-center mb-12">Questions? <span className="gradient-text">Answered.</span></h2>
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <motion.div
                key={faq.q}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                viewport={{ once: true }}
                className="glass rounded-xl p-6"
              >
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-brand-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold mb-2">{faq.q}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">{faq.a}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 py-24 px-6 text-center">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}>
          <div className="max-w-2xl mx-auto glass-strong rounded-3xl p-12 glow-teal">
            <h2 className="font-display font-bold text-4xl mb-4">
              Start saving on taxes<br /><span className="gradient-text">today for free</span>
            </h2>
            <p className="text-muted-foreground mb-8">Join thousands of Indians who optimized their taxes with Maffa TaxAI</p>
            <Link href="/auth/sign-up"
              className="group inline-flex items-center gap-2 bg-brand-500 hover:bg-brand-400 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all">
              Get Started — It's Free
              <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 px-6 py-8">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-brand-500 flex items-center justify-center">
              <Zap className="w-3 h-3 text-white" />
            </div>
            <span className="font-display font-bold">Maffa TaxAI</span>
          </div>
          <p className="text-sm text-muted-foreground">© 2026 Maffa TaxAI. For educational purposes. Consult a CA for complex tax matters.</p>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
            <a href="#" className="hover:text-foreground transition-colors">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
