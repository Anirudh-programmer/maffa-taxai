// ─── User ─────────────────────────────────────────────────────────────────

export interface User {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  is_premium: boolean
  pan_number?: string
  financial_year: string
  preferred_regime?: string
  created_at: string
}

export interface UserPreferences {
  theme: 'dark' | 'light'
  language: string
  notifications_enabled: boolean
  email_reports: boolean
  ai_suggestions: boolean
  dashboard_widgets?: Record<string, unknown>
}

// ─── Auth ─────────────────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// ─── Chat ─────────────────────────────────────────────────────────────────

export interface ChatSession {
  id: string
  title: string
  summary?: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  rag_context_used: boolean
  created_at: string
}

export interface StreamChunk {
  type: 'session_id' | 'chunk' | 'done' | 'error'
  content?: string
  session_id?: string
  message?: string
}

// ─── Tax Calculator ───────────────────────────────────────────────────────

export interface TaxInput {
  basic_salary: number
  hra_received: number
  other_allowances: number
  business_income: number
  rental_income: number
  interest_income: number
  capital_gains_short: number
  capital_gains_long: number
  other_income: number
  rent_paid: number
  city_type: 'metro' | 'non_metro'
  section_80c: number
  section_80ccd_nps: number
  section_80d: number
  section_80e: number
  section_80g: number
  section_80tta: number
  section_80ttb: number
  home_loan_interest: number
  home_loan_principal: number
  lta_exemption: number
  professional_tax: number
  age: number
  is_senior_citizen: boolean
  is_super_senior_citizen: boolean
  financial_year: string
}

export interface TaxSlabDetail {
  slab: string
  rate: number
  taxable_income: number
  tax: number
}

export interface RegimeResult {
  gross_income: number
  total_deductions: number
  taxable_income: number
  basic_tax: number
  surcharge: number
  cess: number
  total_tax: number
  effective_rate: number
  take_home_monthly: number
  slab_details: TaxSlabDetail[]
  deduction_breakdown: Record<string, number>
}

export interface TaxCalculationResult {
  old_regime: RegimeResult
  new_regime: RegimeResult
  recommended_regime: 'old' | 'new'
  tax_saved: number
  savings_percentage: number
  key_recommendations: string[]
  financial_year: string
}

// ─── Documents ────────────────────────────────────────────────────────────

export interface UploadedDocument {
  id: string
  filename: string
  original_filename: string
  file_size: number
  document_type: 'form_16' | 'salary_slip' | 'itr' | 'investment_proof' | 'other'
  status: 'uploaded' | 'processing' | 'processed' | 'failed'
  extracted_data?: Record<string, unknown>
  financial_year?: string
  created_at: string
}

// ─── Dashboard ────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_chats: number
  total_documents: number
  total_calculations: number
  estimated_tax_savings: number
  current_financial_year: string
  recommended_regime?: string
  last_calculation?: {
    id: string
    title: string
    tax_saved: number
    created_at: string
  }
}

// ─── API ─────────────────────────────────────────────────────────────────

export interface ApiError {
  detail?: string
  message?: string
  error?: string
}

// ─── Analytics ────────────────────────────────────────────────────────────

export interface ChartDataPoint {
  name: string
  value: number
  [key: string]: string | number
}
