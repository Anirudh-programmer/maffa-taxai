import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.models.models import User

async def delete_user(email: str):
    if not settings.DATABASE_URL:
        print("DATABASE_URL is not set!")
        return

    engine = create_async_engine(settings.DATABASE_URL)
    sess = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with sess() as session:
        async with session.begin():
            r = await session.execute(select(User).where(User.email == email))
            user = r.scalar_one_or_none()
            if not user:
                print(f"No user found with email: {email}")
                return

            await session.delete(user)
            print(f"Successfully deleted user '{email}' and all cascade-related data from the database.")

if __name__ == "__main__":
    email_to_delete = "anirudhsingh3019@gmail.com"
    if len(sys.argv) > 1:
        email_to_delete = sys.argv[1].strip()
    
    print(f"Attempting to delete user: {email_to_delete}")
    asyncio.run(delete_user(email_to_delete))
