import logging
import asyncio
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.db.session import SessionLocal
from backend.models.entities import Message, Conversation
from backend.llm.ollama_client import ollama_client
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def get_or_create_conversation(db: AsyncSession, session_id: str, chatbot_id: int, user_id: Optional[int] = None) -> Conversation:
    stmt = select(Conversation).where(
        Conversation.session_id == session_id,
        Conversation.chatbot_id == chatbot_id
    )
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    
    if not conv:
        conv = Conversation(
            session_id=session_id,
            chatbot_id=chatbot_id,
            user_id=user_id
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
    return conv

async def add_message(db: AsyncSession, conversation_id: int, role: str, content: str, citations: Optional[dict] = None, confidence: float = 0.0):
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        citations=citations or {},
        confidence=confidence
    )
    db.add(msg)
    await db.commit()

async def get_all_history(db: AsyncSession, conversation_id: int) -> List[dict]:
    stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    res = await db.execute(stmt)
    messages = res.scalars().all()
    return [{"role": m.role, "content": m.content} for m in messages]

async def update_rolling_summary(db: AsyncSession, conversation_id: int) -> str:
    """Generates a rolling summary of the conversation to keep history compact."""
    history = await get_all_history(db, conversation_id)
    if len(history) < 4: return ""
    
    # Only summarize if it's long
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])
    prompt = f"""
    Summarize the following conversation in 2-3 concise sentences.
    Focus on:
    1. The user's main goal.
    2. Key facts shared.
    3. Any pending questions.
    
    CONVERSATION:
    {history_text}
    """
    try:
        summary = await ollama_client.generate(prompt, model=settings.ollama_model)
        # We could store this in the Conversation model if we had a summary column
        return summary
    except Exception as e:
        logger.warning(f"[MEMORY] Summary failed: {e}")
        return ""
