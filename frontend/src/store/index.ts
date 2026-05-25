import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, ChatSession, ChatMessage, TaxCalculationResult, DashboardStats } from '@/types'

// ─── Auth Store ───────────────────────────────────────────────────────────

interface AuthStore {
  user: User | null
  token: string | null
  isLoading: boolean
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setLoading: (v: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      setLoading: (isLoading) => set({ isLoading }),
      logout: () => set({ user: null, token: null }),
    }),
    { name: 'taxai-auth', partialize: (s) => ({ token: s.token }) }
  )
)

// ─── Chat Store ───────────────────────────────────────────────────────────

interface ChatStore {
  sessions: ChatSession[]
  activeSessionId: string | null
  messages: ChatMessage[]
  isStreaming: boolean
  streamingContent: string
  setSessions: (sessions: ChatSession[]) => void
  addSession: (session: ChatSession) => void
  setActiveSession: (id: string | null) => void
  setMessages: (messages: ChatMessage[]) => void
  addMessage: (message: ChatMessage) => void
  appendStreamChunk: (chunk: string) => void
  setStreaming: (v: boolean) => void
  clearStreaming: () => void
  updateSessionTitle: (id: string, title: string) => void
  removeSession: (id: string) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  sessions: [],
  activeSessionId: null,
  messages: [],
  isStreaming: false,
  streamingContent: '',
  setSessions: (sessions) => set({ sessions }),
  addSession: (session) =>
    set((s) => ({ sessions: [session, ...s.sessions] })),
  setActiveSession: (activeSessionId) => set({ activeSessionId }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((s) => ({ messages: [...s.messages, message] })),
  appendStreamChunk: (chunk) =>
    set((s) => ({ streamingContent: s.streamingContent + chunk })),
  setStreaming: (isStreaming) => set({ isStreaming }),
  clearStreaming: () => set({ streamingContent: '', isStreaming: false }),
  updateSessionTitle: (id, title) =>
    set((s) => ({
      sessions: s.sessions.map((sess) =>
        sess.id === id ? { ...sess, title } : sess
      ),
    })),
  removeSession: (id) =>
    set((s) => ({
      sessions: s.sessions.filter((sess) => sess.id !== id),
      activeSessionId: s.activeSessionId === id ? null : s.activeSessionId,
    })),
}))

// ─── Tax Store ────────────────────────────────────────────────────────────

interface TaxStore {
  lastCalculation: TaxCalculationResult | null
  savedCalculations: Array<{ id: string; title: string; tax_saved: number; created_at: string }>
  setLastCalculation: (calc: TaxCalculationResult | null) => void
  setSavedCalculations: (calcs: TaxStore['savedCalculations']) => void
}

export const useTaxStore = create<TaxStore>((set) => ({
  lastCalculation: null,
  savedCalculations: [],
  setLastCalculation: (lastCalculation) => set({ lastCalculation }),
  setSavedCalculations: (savedCalculations) => set({ savedCalculations }),
}))

// ─── UI Store ─────────────────────────────────────────────────────────────

interface UIStore {
  sidebarOpen: boolean
  theme: 'dark' | 'light'
  dashboardStats: DashboardStats | null
  documents: UploadedDocument[]
  setSidebarOpen: (v: boolean) => void
  toggleSidebar: () => void
  setTheme: (theme: 'dark' | 'light') => void
  setDashboardStats: (stats: DashboardStats | null) => void
  setDocuments: (docs: UploadedDocument[]) => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'dark',
      dashboardStats: null,
      documents: [],
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
      setDashboardStats: (dashboardStats) => set({ dashboardStats }),
      setDocuments: (documents) => set({ documents }),
    }),
    { name: 'taxai-ui', partialize: (s) => ({ theme: s.theme, sidebarOpen: s.sidebarOpen }) }
  )
)
