"""
TaxAI FastAPI Application - Main entry point.
Configures middleware, CORS, error handling, startup events.
"""
import time
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import create_tables
from app.api.v1.router import api_router
from app.services.rag_service import rag_service

logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Create database tables
    try:
        await create_tables()
        logger.info("Database connected and tables verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

    # Seed tax knowledge base
    try:
        await rag_service.ingest_tax_knowledge()
        logger.info("Tax knowledge base ready")
    except Exception as e:
        logger.warning(f"RAG initialization failed (non-fatal): {e}")

    logger.info("Application startup complete")
    yield

    logger.info("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Indian Tax Advisor SaaS API",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# State for rate limiter
app.state.limiter = limiter

# ─── Middleware ───────────────────────────────────────────────────────────────

# CORS
allowed_origins = [
    "http://localhost:3000",
    "https://taxai-beta.vercel.app",
    "https://maffa-taxai.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        "Request processed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )
    return response


# ─── Error Handlers ───────────────────────────────────────────────────────────

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "message": str(exc) if settings.DEBUG else "Something went wrong"},
    )


# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
