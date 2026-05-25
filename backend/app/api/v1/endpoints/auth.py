"""
Authentication endpoints - Registration, login, Clerk integration.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import structlog

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.models.models import User, UserPreferences
from app.schemas.schemas import UserCreate, UserLogin, TokenResponse, UserResponse, ClerkAuthRequest
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = structlog.get_logger()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user with email/password."""
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password) if user_in.password else None,
        clerk_id=user_in.clerk_id,
    )
    db.add(user)
    await db.flush()

    # Create default preferences
    prefs = UserPreferences(user_id=user.id)
    db.add(prefs)
    await db.commit()
    await db.refresh(user)

    # Send Welcome Email
    from app.services.email_service import email_service
    await email_service.send_welcome_email(user.email, user.full_name)

    # Generate token
    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/clerk/sync", response_model=TokenResponse)
async def sync_clerk_user(payload: ClerkAuthRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Sync a Clerk-authenticated user with our database.
    Called after Clerk authentication on the frontend.
    """
    # For dev/demo: parse Clerk JWT without full verification
    # In production, use proper Clerk JWT verification
    try:
        import base64
        import json
        parts = payload.clerk_token.split(".")
        if len(parts) >= 2:
            padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
            claims = json.loads(base64.urlsafe_b64decode(padded))
            clerk_id = claims.get("sub", "")
            email = payload.email or claims.get("email", "") or f"{clerk_id}@clerk.user"
            full_name = payload.full_name or claims.get("name", "") or claims.get("full_name", "")
        else:
            raise ValueError("Invalid token format")
    except Exception:
        clerk_id = payload.clerk_token[:50]
        email = payload.email or f"user_{clerk_id[:10]}@taxai.app"
        full_name = payload.full_name or "TaxAI User"

    # Find or create user
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()

    if not user:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    from sqlalchemy.exc import IntegrityError
    try:
        if not user:
            user = User(
                email=email,
                full_name=full_name,
                clerk_id=clerk_id,
            )
            db.add(user)
            await db.flush()
            prefs = UserPreferences(user_id=user.id)
            db.add(prefs)

            # Send Welcome Email on first sync via non-blocking BackgroundTasks (and only to valid email domains)
            from app.services.email_service import email_service
            if email and not email.endswith("@clerk.user") and not email.endswith("@taxai.app"):
                background_tasks.add_task(email_service.send_welcome_email, email, full_name)
        else:
            if clerk_id and not user.clerk_id:
                user.clerk_id = clerk_id
            if full_name and not user.full_name:
                user.full_name = full_name
            
            # If the database currently has a placeholder email and we received a real one, update it and send the welcome email!
            current_email_is_placeholder = not user.email or user.email.endswith("@clerk.user") or user.email.endswith("@taxai.app")
            new_email_is_real = email and not email.endswith("@clerk.user") and not email.endswith("@taxai.app")
            if current_email_is_placeholder and new_email_is_real:
                user.email = email
                from app.services.email_service import email_service
                background_tasks.add_task(email_service.send_welcome_email, email, user.full_name or full_name)

        await db.commit()
    except IntegrityError:
        # Gracefully handle race condition where a concurrent request inserted this user first
        await db.rollback()
        result = await db.execute(select(User).where(User.clerk_id == clerk_id))
        user = result.scalar_one_or_none()
        if not user:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User synchronization failed due to a database conflict."
            )
        
        # Ensure preferences exist even in retry path
        await db.commit()

    await db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token."""
    token = create_access_token({"sub": current_user.id, "email": current_user.email})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(current_user),
    )
