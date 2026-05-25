'use client'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import {
  MessageSquare, Calculator, FileText, TrendingUp,
  ArrowRight, Zap, IndianRupee, Clock, BarChart3,
} from 'lucide-react'
import Link from 'next/link'
import { AppShell } from '@/components/layout/AppShell'
import { usersApi } from '@/lib/api'
import { useAuthStore, useUIStore } from '@/store'
import { formatCurrency, formatDate, SUGGESTED_PROMPTS } from '@/lib/utils'
import type { DashboardStats } from '@/types'

function StatCard({ icon: Icon, label, value, sub, color }: {
  icon: React.ElementType; label: string; value: string; sub?: string; color: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-6 hover:bg-white/[0.06] transition-all"
    >
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${color}`}>
          <Icon className="w-5 h-5" />
      </div>
      <div className="text-2xl font-bold font-display mb-1">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
      {sub && <div className="text-xs text-brand-400 mt-1">{sub}</div>}
    </motion.div>
  )
}

export default function DashboardPage() {
  const { dashboardStats: stats, setDashboardStats } = useUIStore()
  const [loading, setLoading] = useState(!stats)
  const { user } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!user) return
    usersApi.getDashboardStats()
      .then((data) => {
        setDashboardStats(data)
        setLoading(false)
      })
      .catch(console.error)
  }, [user, setDashboardStats])

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <AppShell>
      <div className="p-6 md:p-8 max-w-6xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="font-display font-bold text-3xl mb-1">
            {greeting()}, {user?.full_name?.split(' ')[0] || 'there'} 👋
          </h1>
          <p className="text-muted-foreground">
            FY {stats?.current_financial_year || '2026-27'} · Here's your tax overview
          </p>
        </motion.div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="glass rounded-2xl p-6 h-36">
                <div className="skeleton h-10 w-10 rounded-xl mb-4" />
                <div className="skeleton h-6 w-20 mb-2" />
                <div className="skeleton h-4 w-28" />
              </div>
            ))
          ) : (
            <>
              <StatCard
                icon={MessageSquare} label="AI Consultations" color="bg-blue-500/10 text-blue-400"
                value={String(stats?.total_chats || 0)}
              />
              <StatCard
                icon={FileText} label="Documents" color="bg-purple-500/10 text-purple-400"
                value={String(stats?.total_documents || 0)}
              />
              <StatCard
                icon={Calculator} label="Calculations" color="bg-orange-500/10 text-orange-400"
                value={String(stats?.total_calculations || 0)}
              />
              <StatCard
                icon={IndianRupee} label="Tax Savings Found" color="bg-brand-500/10 text-brand-400"
                value={formatCurrency(stats?.estimated_tax_savings || 0)}
                sub={stats?.recommended_regime ? `${stats.recommended_regime} regime recommended` : undefined}
              />
            </>
          )}
        </div>

        {/* Quick actions + suggested prompts */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Quick actions */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass rounded-2xl p-6">
            <h2 className="font-semibold text-lg mb-4">Quick Actions</h2>
            <div className="space-y-2">
              {[
                { href: '/chat', icon: MessageSquare, label: 'Ask AI about my taxes', desc: 'Get instant personalized advice', color: 'text-blue-400' },
                { href: '/calculator', icon: Calculator, label: 'Calculate my tax', desc: 'Old vs New regime comparison', color: 'text-orange-400' },
                { href: '/upload', icon: FileText, label: 'Upload Form 16', desc: 'AI-powered document analysis', color: 'text-purple-400' },
                { href: '/analytics', icon: BarChart3, label: 'View analytics', desc: 'Charts and insights', color: 'text-green-400' },
              ].map((action) => (
                <Link key={action.href} href={action.href}
                  className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-all group">
                  <div className={`w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center ${action.color}`}>
                    <action.icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium">{action.label}</div>
                    <div className="text-xs text-muted-foreground">{action.desc}</div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-foreground group-hover:translate-x-1 transition-all" />
                </Link>
              ))}
            </div>
          </motion.div>

          {/* Suggested chat prompts */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass rounded-2xl p-6">
            <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4 text-brand-400" />
              Consult Maffa
            </h2>
            <div className="space-y-2">
              {SUGGESTED_PROMPTS.slice(0, 5).map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => router.push(`/chat?q=${encodeURIComponent(prompt)}`)}
                  className="w-full text-left p-3 rounded-xl hover:bg-white/5 transition-all group flex items-start gap-2"
                >
                  <div className="w-1 h-1 rounded-full bg-brand-400 mt-2 flex-shrink-0" />
                  <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors leading-relaxed">
                    {prompt}
                  </span>
                </button>
              ))}
            </div>
            <Link href="/chat" className="mt-4 flex items-center gap-1 text-sm text-brand-400 hover:text-brand-300 transition-colors">
              Open AI Chat <ArrowRight className="w-3 h-3" />
            </Link>
          </motion.div>
        </div>

        {/* Last calculation */}
        {stats?.last_calculation && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-lg">Last Calculation</h2>
              <Link href="/calculator" className="text-sm text-brand-400 hover:text-brand-300 transition-colors flex items-center gap-1">
                New calculation <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="glass rounded-2xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{stats.last_calculation.title}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      {formatDate(stats.last_calculation.created_at)}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-brand-400">
                    {formatCurrency(stats.last_calculation.tax_saved)}
                  </div>
                  <div className="text-xs text-muted-foreground">potential savings</div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Regime banner */}
        {stats?.recommended_regime && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="mt-6 rounded-2xl p-6 bg-gradient-to-r from-brand-500/10 to-brand-500/5 border border-brand-500/20"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-5 h-5 text-brand-400" />
                <div>
                  <div className="font-medium">
                    Recommended: <span className="text-brand-400 capitalize">{stats.recommended_regime} Tax Regime</span>
                  </div>
                  <div className="text-sm text-muted-foreground">Based on your latest tax calculation</div>
                </div>
              </div>
              <Link href="/calculator" className="text-sm bg-brand-500/20 hover:bg-brand-500/30 text-brand-400 px-4 py-2 rounded-lg transition-colors">
                Recalculate
              </Link>
            </div>
          </motion.div>
        )}
      </div>
    </AppShell>
  )
}
