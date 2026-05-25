"""
Document endpoints - Upload, process, and analyze tax documents.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
import os
import structlog

from app.core.database import get_db
from app.core.config import settings
from app.middleware.auth import get_current_user
from app.models.models import User, UploadedDocument
from app.schemas.schemas import DocumentResponse, DocumentAnalysisResult
from app.services.pdf_service import pdf_processor
from app.services.rag_service import rag_service
from app.services.ai_service import gemini_ai

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = structlog.get_logger()

ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/jpg"}
MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(default="other"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a tax document (Form 16, salary slip, ITR PDF).
    Extracts text, classifies document, indexes for RAG.
    """
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: PDF, JPEG, PNG"
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Save file to disk
    file_path = await pdf_processor.save_upload(content, file.filename, current_user.id)

    # Create DB record
    doc = UploadedDocument(
        user_id=current_user.id,
        filename=os.path.basename(file_path),
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        document_type=document_type,
        status="uploaded",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Process in the background (async but awaited here for simplicity)
    try:
        doc.status = "processing"
        await db.commit()

        # Extract text from PDF/image
        if file.content_type == "application/pdf":
            processed = await pdf_processor.process_document(file_path, file.filename)
            extracted_text = processed["extracted_text"]
            detected_type = processed["document_type"]
            financial_year = processed["financial_year"]
        else:
            # Extract text using Gemini Vision OCR
            extracted_text = await gemini_ai.extract_text_from_image(content, file.content_type)
            detected_type = pdf_processor.detect_document_type(extracted_text, file.filename)
            financial_year = pdf_processor.extract_financial_year(extracted_text)

        # Auto-detect document type if not provided
        if document_type == "other" and detected_type != "other":
            doc.document_type = detected_type
        if financial_year:
            doc.financial_year = financial_year

        doc.extracted_text = extracted_text[:50000]  # Limit stored text

        # Index in ChromaDB for RAG
        if extracted_text:
            meta = {"filename": file.filename}
            if financial_year:
                meta["financial_year"] = financial_year
            chunk_ids = await rag_service.ingest_document(
                text=extracted_text,
                document_id=doc.id,
                document_type=doc.document_type,
                user_id=current_user.id,
                metadata=meta,
            )
            doc.chroma_ids = chunk_ids

        # Extract structured data using AI (wrapped to ensure upload resiliency)
        if extracted_text and len(extracted_text) > 100:
            try:
                extracted_data = await gemini_ai.analyze_document(extracted_text, doc.document_type)
                doc.extracted_data = extracted_data
            except Exception as ai_err:
                logger.error("AI structured analysis failed, proceeding with basic text profile", doc_id=doc.id, error=str(ai_err))
                doc.extracted_data = {
                    "summary": "Document successfully parsed and indexed. AI structured review timed out.",
                    "key_observations": ["Text extracted and index completed successfully"],
                    "tax_saving_opportunities": [],
                }

        doc.status = "processed"
        await db.commit()
        await db.refresh(doc)

    except Exception as e:
        logger.error("Document processing failed", doc_id=doc.id, error=str(e))
        doc.status = "failed"
        doc.processing_error = str(e)
        await db.commit()

    return DocumentResponse.model_validate(doc)


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """List all documents uploaded by the user."""
    result = await db.execute(
        select(UploadedDocument)
        .where(UploadedDocument.user_id == current_user.id)
        .order_by(desc(UploadedDocument.created_at))
        .limit(limit)
        .offset(offset)
    )
    docs = result.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    result = await db.execute(
        select(UploadedDocument).where(
            UploadedDocument.id == document_id,
            UploadedDocument.user_id == current_user.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.get("/{document_id}/analysis", response_model=dict)
async def get_document_analysis(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the AI analysis for an uploaded document."""
    result = await db.execute(
        select(UploadedDocument).where(
            UploadedDocument.id == document_id,
            UploadedDocument.user_id == current_user.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status == "processing":
        return {"status": "processing", "message": "Document is being analyzed"}

    if doc.status == "failed":
        return {"status": "failed", "error": doc.processing_error}

    return {
        "status": "processed",
        "document_type": doc.document_type,
        "financial_year": doc.financial_year,
        "extracted_data": doc.extracted_data or {},
        "has_text": bool(doc.extracted_text),
        "extracted_text": doc.extracted_text,
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and remove from ChromaDB."""
    result = await db.execute(
        select(UploadedDocument).where(
            UploadedDocument.id == document_id,
            UploadedDocument.user_id == current_user.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from ChromaDB
    await rag_service.delete_document(document_id)

    # Remove file from disk
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as e:
        logger.warning("File deletion failed", error=str(e))

    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted successfully"}
