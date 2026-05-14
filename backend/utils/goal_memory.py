import re
import json
import logging
from typing import Any, Optional
from backend.models.entities import ConversationGoal, Chatbot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_or_create_goal(db: AsyncSession, session_id: str, chatbot_id: int) -> ConversationGoal:
    stmt = select(ConversationGoal).where(
        ConversationGoal.session_id == session_id,
        ConversationGoal.chatbot_id == chatbot_id
    )
    res = await db.execute(stmt)
    goal = res.scalar_one_or_none()
    
    if not goal:
        goal = ConversationGoal(
            session_id=session_id,
            chatbot_id=chatbot_id,
            state_json={}
        )
        db.add(goal)
        await db.commit()
        await db.refresh(goal)
    return goal

async def update_goal(
    db: AsyncSession, 
    session_id: str, 
    chatbot_id: int, 
    query: str, 
    intent: str, 
    domain: str = "general"
) -> ConversationGoal:
    goal = await get_or_create_goal(db, session_id, chatbot_id)
    
    # 1. Detect Goal from Query
    q = query.lower()
    detected_goal = None
    if any(k in q for k in ["how to", "how do i", "steps to", "guide"]):
        detected_goal = f"Learn how to {query}"
        goal.conversation_mode = "support"
    elif any(k in q for k in ["plan", "itinerary", "schedule"]):
        detected_goal = f"Plan {query}"
        goal.conversation_mode = "planning"
    elif any(k in q for k in ["price", "cost", "buy", "compare"]):
        detected_goal = f"Evaluate {query}"
        goal.conversation_mode = "comparison"
    
    if detected_goal:
        goal.current_goal = detected_goal

    # 2. Map Intent to Workflow
    workflow_map = {
        "admission_assistant": "Admissions",
        "scholarship_helper": "Financial Aid",
        "appointment_guidance": "Booking",
        "tourism_planner": "Itinerary Planning",
        "api_assistant": "Integration",
        "integration_helper": "Integration",
        "shopping_guide": "Purchasing"
    }
    
    if intent in workflow_map:
        goal.active_workflow = workflow_map[intent]
        goal.workflow_stage = "in_progress"

    # 3. Update State
    state = goal.state_json or {}
    history = state.get("history", [])
    history.append({"query": query, "intent": intent, "timestamp": datetime.utcnow().isoformat()})
    state["history"] = history[-10:]
    goal.state_json = state
    
    await db.commit()
    await db.refresh(goal)
    return goal

def clear_goal(session_id: str, chatbot_id: int):
    # This is handled by DB persistence now, but we could add cleanup here
    pass
