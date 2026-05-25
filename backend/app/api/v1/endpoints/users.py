"""
User profile, preferences, and analytics endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timezone, timedelta
from typing import List
import structlog

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import User, UserPreferences, UserAnalytics, ChatSession, UploadedDocument, SavedCalculation
from app.schemas.schemas import (
    UserResponse, UserUpdate, UserPreferencesUpdate, UserPreferencesResponse,
    AnalyticsEvent, DashboardStats
)
from app.utils.helpers import current_financial_year

router = APIRouter(prefix="/users", tags=["Users"])
logger = structlog.get_logger()


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile."""
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user preferences."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return UserPreferencesResponse.model_validate(prefs)


@router.put("/me/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    updates: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user preferences."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)

    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(prefs, field, value)
    await db.commit()
    await db.refresh(prefs)
    return UserPreferencesResponse.model_validate(prefs)


@router.get("/me/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics for the current user."""
    # Count chats
    chat_result = await db.execute(
        select(func.count()).where(
            ChatSession.user_id == current_user.id,
            ChatSession.is_active == True
        )
    )
    total_chats = chat_result.scalar() or 0

    # Count documents
    doc_result = await db.execute(
        select(func.count()).where(UploadedDocument.user_id == current_user.id)
    )
    total_documents = doc_result.scalar() or 0

    # Count calculations
    calc_result = await db.execute(
        select(func.count()).where(SavedCalculation.user_id == current_user.id)
    )
    total_calculations = calc_result.scalar() or 0

    # Get maximum tax savings identified across calculations (avoid double-counting multiple runs)
    savings_result = await db.execute(
        select(func.max(SavedCalculation.tax_saved)).where(
            SavedCalculation.user_id == current_user.id,
            SavedCalculation.tax_saved.isnot(None)
        )
    )
    total_savings = savings_result.scalar() or 0.0

    # Query last calculation to get the recommended regime
    calc_latest = await db.execute(
        select(SavedCalculation)
        .where(SavedCalculation.user_id == current_user.id)
        .order_by(desc(SavedCalculation.created_at))
        .limit(1)
    )
    last_calc = calc_latest.scalar_one_or_none()
    recommended_regime = last_calc.recommended_regime if last_calc else None

    # Fallback: if no calculations are saved yet, check if there is an uploaded salary slip or Form 16,
    # and automatically project savings based on its parameters!
    if total_savings == 0.0:
        doc_res = await db.execute(
            select(UploadedDocument)
            .where(
                UploadedDocument.user_id == current_user.id,
                UploadedDocument.status == "processed",
                UploadedDocument.extracted_data.isnot(None)
            )
            .order_by(desc(UploadedDocument.created_at))
            .limit(1)
        )
        last_doc = doc_res.scalar_one_or_none()
        if last_doc and last_doc.extracted_data:
            ext = last_doc.extracted_data
            # Smart estimation of potential tax savings based on monthly or annual basic salary:
            basic = float(ext.get("basic_salary") or ext.get("total_income") or 0.0)
            if basic > 0:
                if basic < 200000:
                    basic = basic * 12  # Convert monthly to annual
                
                # Estimate tax savings of 6.5% of basic salary (representing the delta between NPS, HRA, and optimal regimes)
                total_savings = round(basic * 0.065, 2)
                recommended_regime = "new"  # Budget 2024 New regime is default recommended

    # Get last calculation
    last_calc_result = await db.execute(
        select(SavedCalculation)
        .where(SavedCalculation.user_id == current_user.id)
        .order_by(desc(SavedCalculation.created_at))
        .limit(1)
    )
    last_calc = last_calc_result.scalar_one_or_none()

    return DashboardStats(
        total_chats=total_chats,
        total_documents=total_documents,
        total_calculations=total_calculations,
        estimated_tax_savings=float(total_savings),
        current_financial_year=current_financial_year(),
        recommended_regime=recommended_regime,
        last_calculation={
            "id": last_calc.id,
            "title": last_calc.title,
            "tax_saved": last_calc.tax_saved,
            "created_at": last_calc.created_at.isoformat(),
        } if last_calc else None,
    )


@router.post("/me/analytics")
async def track_event(
    event: AnalyticsEvent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Track a user analytics event."""
    analytics = UserAnalytics(
        user_id=current_user.id,
        event_type=event.event_type,
        event_data=event.event_data,
    )
    db.add(analytics)
    await db.commit()
    return {"status": "tracked"}


@router.get("/me/analytics/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = 30,
):
    """Get analytics summary for the user."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    events_result = await db.execute(
        select(UserAnalytics.event_type, func.count().label("count"))
        .where(
            UserAnalytics.user_id == current_user.id,
            UserAnalytics.created_at >= since
        )
        .group_by(UserAnalytics.event_type)
        .order_by(desc("count"))
    )
    events = events_result.all()

    # Chat activity
    chat_result = await db.execute(
        select(func.count()).where(
            ChatSession.user_id == current_user.id,
            ChatSession.created_at >= since
        )
    )
    recent_chats = chat_result.scalar() or 0

    return {
        "period_days": days,
        "recent_chats": recent_chats,
        "event_breakdown": [{"event": e.event_type, "count": e.count} for e in events],
        "top_events": [e.event_type for e in events[:3]],
    }
