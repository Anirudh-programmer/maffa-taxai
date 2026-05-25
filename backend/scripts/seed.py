"""
Seed script - populates tax knowledge base and creates test data.
Run: python scripts/seed.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import AsyncSessionLocal, create_tables
from app.models.models import User, UserPreferences
from app.core.security import get_password_hash
from app.services.rag_service import rag_service
import structlog

logger = structlog.get_logger()


async def seed_demo_user():
    """Create a demo user for testing."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == "demo@taxai.app"))
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("Demo user already exists")
            return

        user = User(
            email="demo@taxai.app",
            full_name="Demo User",
            hashed_password=get_password_hash("demo123"),
            is_active=True,
            financial_year="2024-25",
        )
        db.add(user)
        await db.flush()

        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
        await db.commit()
        logger.info("Demo user created", email="demo@taxai.app", password="demo123")


async def main():
    logger.info("Starting seed...")
    await create_tables()
    await seed_demo_user()
    await rag_service.ingest_tax_knowledge()
    logger.info("Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
