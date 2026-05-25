"""
Pydantic schemas for request validation and response serialization.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import enum


# ─── Auth Schemas ──────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: Optional[str] = None
    clerk_id: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class ClerkAuthRequest(BaseModel):
    clerk_token: str
    email: Optional[str] = None
    full_name: Optional[str] = None


# ─── User Schemas ──────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_premium: bool = False
    pan_number: Optional[str] = None
    financial_year: str = "2024-25"
    preferred_regime: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    pan_number: Optional[str] = None
    financial_year: Optional[str] = None
    preferred_regime: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_reports: Optional[bool] = None
    ai_suggestions: Optional[bool] = None
    dashboard_widgets: Optional[Dict[str, Any]] = None


class UserPreferencesResponse(BaseModel):
    theme: str = "dark"
    language: str = "en"
    notifications_enabled: bool = True
    email_reports: bool = True
    ai_suggestions: bool = True
    dashboard_widgets: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


# ─── Chat Schemas ──────────────────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    document_ids: Optional[List[str]] = None


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    rag_context_used: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class StreamingChatRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    use_rag: bool = True


# ─── Tax Calculation Schemas ───────────────────────────────────────────────

class TaxInput(BaseModel):
    """Input for tax calculation."""
    # Income
    basic_salary: float = Field(ge=0, default=0)
    hra_received: float = Field(ge=0, default=0)
    other_allowances: float = Field(ge=0, default=0)
    business_income: float = Field(ge=0, default=0)
    rental_income: float = Field(ge=0, default=0)
    interest_income: float = Field(ge=0, default=0)
    capital_gains_short: float = Field(ge=0, default=0)
    capital_gains_long: float = Field(ge=0, default=0)
    other_income: float = Field(ge=0, default=0)

    # HRA exemption inputs
    rent_paid: float = Field(ge=0, default=0)
    city_type: str = Field(default="non_metro")  # metro/non_metro

    # Deductions (Old Regime)
    section_80c: float = Field(ge=0, le=150000, default=0)  # EPF, PPF, ELSS, LIC
    section_80ccd_nps: float = Field(ge=0, le=50000, default=0)  # NPS additional
    section_80d: float = Field(ge=0, le=100000, default=0)  # Health insurance
    section_80e: float = Field(ge=0, default=0)  # Education loan interest
    section_80g: float = Field(ge=0, default=0)  # Donations
    section_80tta: float = Field(ge=0, le=10000, default=0)  # Savings interest
    section_80ttb: float = Field(ge=0, le=50000, default=0)  # Senior citizen interest
    home_loan_interest: float = Field(ge=0, le=200000, default=0)  # Section 24b
    home_loan_principal: float = Field(ge=0, le=150000, default=0)  # Part of 80C
    lta_exemption: float = Field(ge=0, default=0)
    professional_tax: float = Field(ge=0, le=2500, default=0)

    # Age & status
    age: int = Field(ge=18, le=100, default=30)
    is_senior_citizen: bool = False  # 60-79 years
    is_super_senior_citizen: bool = False  # 80+ years
    financial_year: str = "2024-25"


class TaxSlabDetail(BaseModel):
    slab: str
    rate: float
    taxable_income: float
    tax: float


class RegimeResult(BaseModel):
    gross_income: float
    total_deductions: float
    taxable_income: float
    basic_tax: float
    surcharge: float
    cess: float
    total_tax: float
    effective_rate: float
    take_home_monthly: float
    slab_details: List[TaxSlabDetail]
    deduction_breakdown: Dict[str, float]


class TaxCalculationResult(BaseModel):
    old_regime: RegimeResult
    new_regime: RegimeResult
    recommended_regime: str
    tax_saved: float
    savings_percentage: float
    key_recommendations: List[str]
    financial_year: str


class TaxCalculationSave(BaseModel):
    title: Optional[str] = "My Tax Calculation"
    input_data: Dict[str, Any]
    old_regime_result: Dict[str, Any]
    new_regime_result: Dict[str, Any]
    recommended_regime: str
    tax_saved: float
    financial_year: str = "2024-25"


# ─── Document Schemas ─────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    document_type: str
    status: str
    extracted_text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    financial_year: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentAnalysisResult(BaseModel):
    document_id: str
    document_type: str
    extracted_fields: Dict[str, Any]
    ai_summary: str
    tax_implications: List[str]
    recommended_actions: List[str]


# ─── Analytics Schemas ────────────────────────────────────────────────────

class AnalyticsEvent(BaseModel):
    event_type: str
    event_data: Optional[Dict[str, Any]] = None


class DashboardStats(BaseModel):
    total_chats: int
    total_documents: int
    total_calculations: int
    estimated_tax_savings: float
    current_financial_year: str
    recommended_regime: Optional[str] = None
    last_calculation: Optional[Dict[str, Any]] = None


class AnalyticsSummary(BaseModel):
    period: str
    chat_sessions: int
    messages_sent: int
    documents_uploaded: int
    calculations_done: int
    tax_savings_identified: float
    most_asked_topics: List[str]


# ─── Tax Report Schemas ───────────────────────────────────────────────────

class TaxReportCreate(BaseModel):
    title: str = "Tax Analysis Report"
    financial_year: str = "2024-25"
    calculation_id: Optional[str] = None
    include_recommendations: bool = True


class TaxReportResponse(BaseModel):
    id: str
    title: str
    financial_year: str
    report_type: str
    is_ready: bool
    created_at: datetime

    model_config = {"from_attributes": True}
