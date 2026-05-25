"""
SQLAlchemy async ORM models for TaxAI platform.
All models use UUID primary keys and JSONB for flexible metadata.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String, Text, Boolean, Float, Integer, DateTime,
    ForeignKey, Index, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import enum
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


# ─── Enums ──────────────────────────────────────────────────────────────────

class TaxRegime(str, enum.Enum):
    OLD = "old"
    NEW = "new"


class DocumentType(str, enum.Enum):
    FORM_16 = "form_16"
    SALARY_SLIP = "salary_slip"
    ITR = "itr"
    INVESTMENT_PROOF = "investment_proof"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ─── Models ──────────────────────────────────────────────────────────────────

class User(Base):
    """Core user profile. Synced from Clerk auth."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    clerk_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Tax profile
    pan_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    financial_year: Mapped[str] = mapped_column(String(7), default="2024-25")
    preferred_regime: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Metadata
    extra_data: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    chat_sessions: Mapped[List["ChatSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[List["UploadedDocument"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tax_reports: Mapped[List["TaxReport"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_calculations: Mapped[List["SavedCalculation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    preferences: Mapped[Optional["UserPreferences"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    analytics: Mapped[List["UserAnalytics"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
    )


class UserPreferences(Base):
    """User app preferences and settings."""
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    theme: Mapped[str] = mapped_column(String(10), default="dark")
    language: Mapped[str] = mapped_column(String(10), default="en")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_reports: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_suggestions: Mapped[bool] = mapped_column(Boolean, default=True)
    dashboard_widgets: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="preferences")


class ChatSession(Base):
    """A conversation session between user and AI."""
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    session_metadata: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    __table_args__ = (
        Index("ix_chat_sessions_user_updated", "user_id", "updated_at"),
    )


class ChatMessage(Base):
    """Individual message in a chat session."""
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user/assistant/system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rag_context_used: Mapped[bool] = mapped_column(Boolean, default=False)
    function_calls: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True)
    message_metadata: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
    )


class UploadedDocument(Base):
    """Tax documents uploaded by users (Form 16, salary slips, ITR)."""
    __tablename__ = "uploaded_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_type: Mapped[str] = mapped_column(String(30), default="other")
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True)
    chroma_ids: Mapped[Optional[List]] = mapped_column(JSONB, nullable=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    financial_year: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="documents")


class SavedCalculation(Base):
    """Saved tax calculations for users."""
    __tablename__ = "saved_calculations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="Tax Calculation")
    financial_year: Mapped[str] = mapped_column(String(7), default="2024-25")
    input_data: Mapped[Dict] = mapped_column(JSONB, nullable=False)
    old_regime_result: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True)
    new_regime_result: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True)
    recommended_regime: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    tax_saved: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="saved_calculations")


class TaxReport(Base):
    """Generated PDF tax reports."""
    __tablename__ = "tax_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    financial_year: Mapped[str] = mapped_column(String(7), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), default="full_analysis")
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_data: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True)
    is_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="tax_reports")


class UserAnalytics(Base):
    """Analytics events and usage tracking."""
    __tablename__ = "user_analytics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_data: Mapped[Optional[Dict]] = mapped_column(JSONB, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped["User"] = relationship(back_populates="analytics")

    __table_args__ = (
        Index("ix_analytics_user_type_date", "user_id", "event_type", "created_at"),
    )


class AISession(Base):
    """Tracks AI model sessions and token usage."""
    __tablename__ = "ai_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    chat_session_id: Mapped[Optional[str]] = mapped_column(ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rag_used: Mapped[bool] = mapped_column(Boolean, default=False)
    function_calls_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
