"""
API v1 router - aggregates all endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, tax, documents, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(tax.router)
api_router.include_router(documents.router)
api_router.include_router(users.router)
