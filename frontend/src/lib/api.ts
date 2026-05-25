import axios, { AxiosInstance, AxiosError } from 'axios'
import toast from 'react-hot-toast'
import type {
  AuthResponse, User, UserPreferences, ChatSession, ChatMessage,
  TaxInput, TaxCalculationResult, UploadedDocument, DashboardStats
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ─── Axios instance ───────────────────────────────────────────────────────

const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// Request interceptor - attach JWT
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('taxai_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor - handle auth errors
api.interceptors.response.use(
  (res) => res,
  (err: AxiosError<{ detail?: string; message?: string }>) => {
    if (err.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('taxai_token')
        window.location.href = '/auth/sign-in'
      }
    }
    return Promise.reject(err)
  }
)

export function setAuthToken(token: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('taxai_token', token)
  }
}

export function clearAuthToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('taxai_token')
  }
}

export function getAuthToken(): string | null {
  if (typeof window !== 'undefined') return localStorage.getItem('taxai_token')
  return null
}

// ─── Auth ─────────────────────────────────────────────────────────────────

export const authApi = {
  register: (data: { email: string; full_name?: string; password: string }) =>
    api.post<AuthResponse>('/auth/register', data).then(r => r.data),

  login: (email: string, password: string) =>
    api.post<AuthResponse>('/auth/login', { email, password }).then(r => r.data),

  syncClerk: (clerk_token: string, email?: string, full_name?: string) =>
    api.post<AuthResponse>('/auth/clerk/sync', { clerk_token, email, full_name }).then(r => r.data),

  me: () => api.get<User>('/auth/me').then(r => r.data),
}

// ─── Users ────────────────────────────────────────────────────────────────

export const usersApi = {
  getProfile: () => api.get<User>('/users/me').then(r => r.data),

  updateProfile: (data: Partial<User>) =>
    api.put<User>('/users/me', data).then(r => r.data),

  getPreferences: () => api.get<UserPreferences>('/users/me/preferences').then(r => r.data),

  updatePreferences: (data: Partial<UserPreferences>) =>
    api.put<UserPreferences>('/users/me/preferences', data).then(r => r.data),

  getDashboardStats: () => api.get<DashboardStats>('/users/me/dashboard').then(r => r.data),

  trackEvent: (event_type: string, event_data?: Record<string, unknown>) =>
    api.post('/users/me/analytics', { event_type, event_data }).then(r => r.data),

  getAnalyticsSummary: (days = 30) =>
    api.get(`/users/me/analytics/summary?days=${days}`).then(r => r.data),
}

// ─── Chat ─────────────────────────────────────────────────────────────────

export const chatApi = {
  createSession: (title?: string) =>
    api.post<ChatSession>('/chat/sessions', { title }).then(r => r.data),

  listSessions: (limit = 20, offset = 0) =>
    api.get<ChatSession[]>(`/chat/sessions?limit=${limit}&offset=${offset}`).then(r => r.data),

  getMessages: (sessionId: string) =>
    api.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`).then(r => r.data),

  deleteSession: (sessionId: string) =>
    api.delete(`/chat/sessions/${sessionId}`).then(r => r.data),

  sendMessage: (data: { content: string; session_id?: string; document_ids?: string[] }) =>
    api.post<ChatMessage>('/chat/message', data).then(r => r.data),

  getSuggestedPrompts: () =>
    api.get<{ prompts: string[] }>('/chat/suggested-prompts').then(r => r.data),

  // Streaming chat via native fetch (axios doesn't support SSE well)
  streamChat: async (
    content: string,
    sessionId: string | null,
    documentIds: string[],
    onChunk: (chunk: string) => void,
    onSessionId: (id: string) => void,
    onDone: (sessionId: string) => void,
    onError: (err: string) => void,
  ) => {
    const token = getAuthToken()
    const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        content,
        session_id: sessionId,
        document_ids: documentIds,
        use_rag: true,
      }),
    })

    if (!response.ok) {
      onError('Failed to connect to AI. Please try again.')
      return
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) return

    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      
      const lines = buffer.split('\n')
      // Save the last incomplete line back to the buffer for the next network packet
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) continue
        try {
          const data = JSON.parse(trimmed.slice(6))
          if (data.type === 'session_id') onSessionId(data.session_id)
          else if (data.type === 'chunk') onChunk(data.content)
          else if (data.type === 'done') onDone(data.session_id)
          else if (data.type === 'error') onError(data.message)
        } catch (err) {
          console.warn('Incomplete SSE line skipped or corrupted:', trimmed, err)
        }
      }
    }
  },
}

// ─── Tax Calculator ───────────────────────────────────────────────────────

export const taxApi = {
  calculate: (input: TaxInput) =>
    api.post<TaxCalculationResult>('/tax/calculate', input).then(r => r.data),

  calculatePublic: (input: TaxInput) =>
    api.post<TaxCalculationResult>('/tax/calculate/public', input).then(r => r.data),

  saveCalculation: (data: {
    title: string
    input_data: Record<string, unknown>
    old_regime_result: Record<string, unknown>
    new_regime_result: Record<string, unknown>
    recommended_regime: string
    tax_saved: number
    financial_year: string
  }) => api.post('/tax/calculations/save', data).then(r => r.data),

  listCalculations: () => api.get('/tax/calculations').then(r => r.data),

  getCalculation: (id: string) => api.get(`/tax/calculations/${id}`).then(r => r.data),

  getTaxSections: () => api.get('/tax/sections').then(r => r.data),

  generateReport: (data: { title: string; financial_year: string; calculation_id?: string }) =>
    api.post('/tax/reports/generate', data).then(r => r.data),
}

// ─── Documents ────────────────────────────────────────────────────────────

export const documentsApi = {
  upload: (file: File, documentType = 'other') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)
    return api.post<UploadedDocument>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },

  list: () => api.get<UploadedDocument[]>('/documents/').then(r => r.data),

  get: (id: string) => api.get<UploadedDocument>(`/documents/${id}`).then(r => r.data),

  getAnalysis: (id: string) => api.get(`/documents/${id}/analysis`).then(r => r.data),

  delete: (id: string) => api.delete(`/documents/${id}`).then(r => r.data),
}

export default api
