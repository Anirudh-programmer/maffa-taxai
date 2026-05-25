'use client'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Settings, User, Bell, Shield, Palette, Save, Loader2, Moon, Sun } from 'lucide-react'
import toast from 'react-hot-toast'
import { AppShell } from '@/components/layout/AppShell'
import { usersApi } from '@/lib/api'
import { useAuthStore, useUIStore } from '@/store'
import { cn } from '@/lib/utils'
import type { UserPreferences } from '@/types'

const FINANCIAL_YEARS = ['2026-27', '2025-26', '2024-25']
const TAX_REGIMES = [
  { value: 'new', label: 'New Regime (Default)' },
  { value: 'old', label: 'Old Regime' },
]

function Section({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <div className="glass rounded-2xl p-6">
      <h2 className="font-semibold flex items-center gap-2 mb-5">
        <Icon className="w-4 h-4 text-brand-400" />
        {title}
      </h2>
      {children}
    </div>
  )
}

function Toggle({ label, desc, value, onChange }: {
  label: string; desc?: string; value: boolean; onChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
      <div>
        <p className="text-sm font-medium">{label}</p>
        {desc && <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>}
      </div>
      <button
        onClick={() => onChange(!value)}
        className={cn(
          'relative w-11 h-6 rounded-full transition-all',
          value ? 'bg-brand-500' : 'bg-white/10'
        )}
      >
        <div className={cn(
          'absolute top-1 w-4 h-4 rounded-full bg-white transition-all',
          value ? 'left-6' : 'left-1'
        )} />
      </button>
    </div>
  )
}

export default function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const { theme, setTheme } = useUIStore()
  const [prefs, setPrefs] = useState<UserPreferences | null>(null)
  const [profileForm, setProfileForm] = useState({ full_name: '', pan_number: '', financial_year: '2026-27', preferred_regime: 'new' })
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPrefs, setSavingPrefs] = useState(false)

  useEffect(() => {
    if (!user) return
    setProfileForm({
      full_name: user.full_name || '',
      pan_number: user.pan_number || '',
      financial_year: user.financial_year || '2026-27',
      preferred_regime: user.preferred_regime || 'new',
    })
    usersApi.getPreferences().then(setPrefs).catch(console.error)
  }, [user])

  const saveProfile = async () => {
    setSavingProfile(true)
    try {
      const updated = await usersApi.updateProfile(profileForm)
      setUser(updated)
      toast.success('Profile updated!')
    } catch {
      toast.error('Failed to update profile')
    } finally {
      setSavingProfile(false)
    }
  }

  const updatePref = async (key: keyof UserPreferences, value: boolean | string) => {
    if (!prefs) return
    const updated = { ...prefs, [key]: value }
    setPrefs(updated)
    setSavingPrefs(true)
    try {
      await usersApi.updatePreferences({ [key]: value })
    } catch {
      toast.error('Failed to save preference')
      setPrefs(prefs)
    } finally {
      setSavingPrefs(false)
    }
  }

  const handleThemeChange = (t: 'dark' | 'light') => {
    setTheme(t)
    // Apply to DOM immediately
    document.documentElement.classList.toggle('light', t === 'light')
    document.documentElement.classList.toggle('dark', t === 'dark')
    if (prefs) updatePref('theme', t)
    toast.success(`Switched to ${t} mode`)
  }

  return (
    <AppShell>
      <div className="p-6 md:p-8 max-w-3xl mx-auto">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="font-display font-bold text-3xl mb-1 flex items-center gap-3">
            <Settings className="w-7 h-7 text-brand-400" />
            Settings
          </h1>
          <p className="text-muted-foreground">Manage your account and preferences</p>
        </motion.div>

        <div className="space-y-5">
          {/* Profile */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
            <Section title="Profile" icon={User}>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">Full Name</label>
                  <input
                    value={profileForm.full_name}
                    onChange={(e) => setProfileForm(p => ({ ...p, full_name: e.target.value }))}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-brand-500/50 transition-colors"
                    placeholder="Your full name"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">Email</label>
                  <input
                    value={user?.email || ''}
                    disabled
                    className="w-full bg-white/3 border border-white/5 rounded-lg px-3 py-2.5 text-sm text-muted-foreground cursor-not-allowed"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">PAN Number</label>
                  <input
                    value={profileForm.pan_number}
                    onChange={(e) => setProfileForm(p => ({ ...p, pan_number: e.target.value.toUpperCase() }))}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-brand-500/50 transition-colors font-mono"
                    placeholder="ABCDE1234F"
                    maxLength={10}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Financial Year</label>
                    <select
                      value={profileForm.financial_year}
                      onChange={(e) => setProfileForm(p => ({ ...p, financial_year: e.target.value }))}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-brand-500/50 text-foreground"
                    >
                      {FINANCIAL_YEARS.map((fy) => (
                        <option key={fy} value={fy}>{fy}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-muted-foreground mb-1.5">Preferred Regime</label>
                    <select
                      value={profileForm.preferred_regime}
                      onChange={(e) => setProfileForm(p => ({ ...p, preferred_regime: e.target.value }))}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-brand-500/50 text-foreground"
                    >
                      {TAX_REGIMES.map((r) => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <button
                  onClick={saveProfile}
                  disabled={savingProfile}
                  className="flex items-center gap-2 bg-brand-500/20 hover:bg-brand-500/30 text-brand-400 px-4 py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-50"
                >
                  {savingProfile ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Save Profile
                </button>
              </div>
            </Section>
          </motion.div>

          {/* Appearance */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
            <Section title="Appearance" icon={Palette}>
              <div>
                <p className="text-sm text-muted-foreground mb-3">Theme</p>
                <div className="flex gap-3">
                  {([
                    { t: 'dark', icon: Moon, label: 'Dark' },
                    { t: 'light', icon: Sun, label: 'Light' },
                  ] as const).map(({ t, icon: Icon, label }) => (
                    <button
                      key={t}
                      onClick={() => handleThemeChange(t)}
                      className={cn(
                        'flex-1 py-3 rounded-xl text-sm font-medium border transition-all flex items-center justify-center gap-2',
                        theme === t
                          ? 'bg-brand-500/15 border-brand-500/30 text-brand-400'
                          : 'bg-white/5 border-white/10 text-muted-foreground hover:text-foreground hover:bg-white/8'
                      )}
                    >
                      <Icon className="w-4 h-4" />
                      {label}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  {theme === 'light' ? '☀️ Light mode active — optimized for bright environments' : '🌙 Dark mode active — easy on the eyes'}
                </p>
              </div>
            </Section>
          </motion.div>

          {/* Notifications */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Section title="Notifications" icon={Bell}>
              {prefs ? (
                <div>
                  <Toggle
                    label="Notifications"
                    desc="Receive in-app notifications"
                    value={prefs.notifications_enabled}
                    onChange={(v) => updatePref('notifications_enabled', v)}
                  />
                  <Toggle
                    label="Email Reports"
                    desc="Receive weekly tax summary emails"
                    value={prefs.email_reports}
                    onChange={(v) => updatePref('email_reports', v)}
                  />
                  <Toggle
                    label="AI Suggestions"
                    desc="Get proactive tax-saving suggestions from Maffa Core"
                    value={prefs.ai_suggestions}
                    onChange={(v) => updatePref('ai_suggestions', v)}
                  />
                </div>
              ) : (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => <div key={i} className="skeleton h-12 rounded-xl" />)}
                </div>
              )}
            </Section>
          </motion.div>

          {/* Security */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
            <Section title="Security & Privacy" icon={Shield}>
              <div className="space-y-3 text-sm text-muted-foreground">
                <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02]">
                  <span>Authentication</span>
                  <span className="text-brand-400 text-xs">Clerk · Secured</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02]">
                  <span>Data encryption</span>
                  <span className="text-brand-400 text-xs">AES-256 · Active</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02]">
                  <span>Data retention</span>
                  <span className="text-xs">Stored until you delete</span>
                </div>
                <p className="text-xs pt-2">
                  Maffa TaxAI is for personal tax guidance. For complex tax situations, consult a Chartered Accountant.
                  Your data is never shared with third parties.
                </p>
              </div>
            </Section>
          </motion.div>
        </div>
      </div>
    </AppShell>
  )
}
