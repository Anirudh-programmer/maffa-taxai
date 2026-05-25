"""
Chat endpoints - AI chat with streaming, session management, history.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
import json
import asyncio
import structlog

from app.core.database import get_db
from app.core.config import settings
from app.middleware.auth import get_current_user
from app.models.models import User, ChatSession, ChatMessage, AISession, UploadedDocument
from app.schemas.schemas import (
    ChatSessionCreate, ChatSessionResponse, ChatMessageCreate,
    ChatMessageResponse, StreamingChatRequest
)
from app.services.ai_service import gemini_ai

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = structlog.get_logger()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    session_in: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        title=session_in.title or "New Chat",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return ChatSessionResponse.model_validate(session)


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """List all chat sessions for the current user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id, ChatSession.is_active == True)
        .order_by(desc(ChatSession.updated_at))
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a chat session."""
    # Verify ownership
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a chat session."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_active = False
    await db.commit()
    return {"message": "Session deleted"}


@router.post("/stream")
async def stream_chat(
    request: StreamingChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream AI chat response using Server-Sent Events.
    Creates or uses existing session, saves messages to DB.
    """
    # Get or create session
    if request.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == request.session_id,
                ChatSession.user_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(user_id=current_user.id, title="New Chat")
        db.add(session)
        await db.flush()

    # Get conversation history
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .limit(20)  # Last 20 messages for context
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in result.scalars().all()
    ]

    # Check if user has uploaded any successfully processed documents
    result_docs = await db.execute(
        select(func.count(UploadedDocument.id)).where(
            UploadedDocument.user_id == current_user.id,
            UploadedDocument.status == "processed"
        )
    )
    has_documents = (result_docs.scalar() or 0) > 0

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.content,
    )
    db.add(user_msg)
    session.message_count += 1
    await db.commit()

    async def generate():
        from app.core.database import AsyncSessionLocal

        full_response = ""
        rag_used = False

        try:
            # Send session_id first so frontend knows the session
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session.id})}\n\n"

            # Stream AI response
            async for chunk in gemini_ai.stream_chat(
                user_message=request.content,
                history=history,
                document_ids=request.document_ids,
                use_rag=request.use_rag,
                has_documents=has_documents,
            ):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Open a fresh database session to update the title and save the message
            # since the original request-scoped 'db' session is closed when stream_chat returns.
            async with AsyncSessionLocal() as fresh_db:
                result = await fresh_db.execute(
                    select(ChatSession).where(ChatSession.id == session.id)
                )
                fresh_session = result.scalar_one_or_none()
                if fresh_session:
                    # Auto-generate title from first message
                    if fresh_session.message_count <= 2:
                        title = await gemini_ai.generate_session_title(request.content)
                        fresh_session.title = title

                    # Save assistant message
                    assistant_msg = ChatMessage(
                        session_id=fresh_session.id,
                        role="assistant",
                        content=full_response,
                        rag_context_used=rag_used,
                        model_used=settings.GEMINI_MODEL,
                    )
                    fresh_db.add(assistant_msg)
                    fresh_session.message_count += 1
                    await fresh_db.commit()

            yield f"data: {json.dumps({'type': 'done', 'session_id': session.id})}\n\n"

        except Exception as e:
            logger.error("Streaming error", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Non-streaming chat endpoint for simpler integrations.
    Returns complete response at once.
    """
    # Get or create session
    if message.session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == message.session_id,
                ChatSession.user_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(user_id=current_user.id, title="New Chat")
        db.add(session)
        await db.flush()

    # Get history
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .limit(20)
    )
    history = [{"role": m.role, "content": m.content} for m in result.scalars().all()]

    # Add current message to history for AI context
    history.append({"role": "user", "content": message.content})

    # Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=message.content)
    db.add(user_msg)
    session.message_count += 1

    # Get AI response
    ai_response = await gemini_ai.chat(
        user_message=message.content,
        history=history[:-1],
        document_ids=message.document_ids,
    )

    # Auto-title
    if session.message_count <= 1:
        session.title = await gemini_ai.generate_session_title(message.content)

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_response["content"],
        rag_context_used=ai_response.get("rag_used", False),
        model_used=ai_response.get("model"),
        tokens_used=ai_response.get("tokens", {}).get("total"),
    )
    db.add(assistant_msg)
    session.message_count += 1
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatMessageResponse.model_validate(assistant_msg)


@router.get("/suggested-prompts")
async def get_suggested_prompts():
    """Return suggested tax questions for the chat interface."""
    return {
        "prompts": [
            "Which tax regime is better for me - old or new?",
            "How can I save more tax this year?",
            "What is Section 80C and how to maximize it?",
            "Should I invest in NPS for tax saving?",
            "How is HRA exemption calculated?",
            "What are the key Budget 2024 changes for salaried employees?",
            "Help me understand my Form 16",
            "What is capital gains tax on mutual funds?",
            "How to claim home loan tax benefits?",
            "What documents do I need to file ITR?",
        ]
    }
