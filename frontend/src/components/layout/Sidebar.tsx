'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, MessageSquare, Calculator, Upload, BarChart3,
  Settings, Zap, ChevronLeft, ChevronRight, FileText, LogOut, User,
} from 'lucide-react'
import { useClerk, useUser } from '@clerk/nextjs'
import { useUIStore } from '@/store'
import { cn } from '@/lib/utils'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/chat', label: 'AI Chat', icon: MessageSquare },
  { href: '/calculator', label: 'Tax Calculator', icon: Calculator },
  { href: '/upload', label: 'Documents', icon: Upload },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, setSidebarOpen } = useUIStore()
  const { signOut } = useClerk()
  const { user } = useUser()

  return (
    <motion.aside
      animate={{ width: sidebarOpen ? 240 : 72 }}
      transition={{ duration: 0.25, ease: 'easeInOut' }}
      className="relative flex flex-col h-full z-20 flex-shrink-0"
    >
      {/* Sidebar background & scroll container with overflow-hidden to prevent text bleed during transitions */}
      <div className="flex flex-col h-full w-full border-r border-white/5 bg-background/80 backdrop-blur-xl overflow-hidden">
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-white/5">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center flex-shrink-0 glow-teal">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="font-display font-bold text-lg whitespace-nowrap"
              >
                Maffa TaxAI
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.href}
                href={item.href}
                prefetch={true}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all group relative',
                  isActive
                    ? 'bg-brand-500/15 text-brand-400'
                    : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute inset-0 bg-brand-500/10 rounded-xl border border-brand-500/20"
                    transition={{ duration: 0.2 }}
                  />
                )}
                <item.icon className={cn('w-5 h-5 flex-shrink-0 relative z-10', isActive ? 'text-brand-400' : '')} />
                <AnimatePresence>
                  {sidebarOpen && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="text-sm font-medium whitespace-nowrap relative z-10"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Link>
            )
          })}
        </nav>

        {/* User profile */}
        <div className="px-2 py-3 border-t border-white/5">
          <div className={cn(
            'flex items-center gap-3 px-3 py-2.5 rounded-xl',
            sidebarOpen ? '' : 'justify-center'
          )}>
            <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center flex-shrink-0">
              {user?.imageUrl ? (
                <img src={user.imageUrl} alt="" className="w-full h-full rounded-full object-cover" />
              ) : (
                <User className="w-4 h-4 text-brand-400" />
              )}
            </div>
            <AnimatePresence>
              {sidebarOpen && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex-1 min-w-0"
                >
                  <p className="text-sm font-medium truncate">
                    {user?.fullName || user?.emailAddresses[0]?.emailAddress?.split('@')[0] || 'User'}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">
                    {user?.emailAddresses[0]?.emailAddress}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <button
            onClick={() => signOut()}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-xl text-muted-foreground hover:text-red-400 hover:bg-red-400/10 transition-all text-sm mt-1',
              !sidebarOpen && 'justify-center'
            )}
          >
            <LogOut className="w-4 h-4 flex-shrink-0" />
            <AnimatePresence>
              {sidebarOpen && (
                <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  Sign out
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>
      </div>

      {/* Styled toggle button, positioned cleanly on the sidebar right border without clipping */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute -right-3.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-brand-500 hover:bg-brand-400 text-white border border-brand-400/20 flex items-center justify-center transition-all duration-200 ease-out hover:scale-110 active:scale-95 z-30 shadow-[0_4px_12px_rgba(20,184,166,0.3)] cursor-pointer"
        aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
      >
        {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
    </motion.aside>
  )
}

