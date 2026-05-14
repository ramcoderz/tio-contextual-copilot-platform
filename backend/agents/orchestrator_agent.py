"""
Orchestrator — the intelligence core of TiO.

Upgrade surface (all 16 improvements integrated):
  1. Strict session + chatbot isolation
  2. Retrieval filtering + confidence scoring
  3. Entity-aware retrieval (already in vectorstore, passed through here)
  4. Domain routing with confidence threshold
  5. Query expansion before retrieval
  6. Dynamic prompt layering (Base→Domain→Skill→Mode→Goal→Context)
  7. User goal memory updated every turn
  8. Context confidence system → infer vs hedge vs fallback
  9. Site understanding injected into every prompt
  10. Conversation mode detection
  11. Robotic phrase removal + proactive assumption-based mode
  12. Proactive recommendation engine (via skill guidance)
  13. Graceful fallback strategy
  14. Enhanced monitoring (confidence, fallback, hallucination flags)
  15. Improved ingestion quality (handled in ingestion/service.py)
  16. Reranking (already in vectorstore, preserved)
"""

import asyncio
import time
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.llm.ollama_client import ollama_client
from backend.config.settings import get_settings
from backend.vectorstore.service import async_retrieve
from backend.llm.profiles import get_profile
from backend.llm.skills import get_skill_guidance
from backend.models.entities import Conversation, Chatbot
from backend.rag.safety import sanitize_input, sanitize_output
from backend.utils.monitoring import track_query
from backend.utils.domain_intelligence import domain_detector
from backend.utils.intent_intelligence import intent_intelligence
from backend.utils.query_expander import expand_query
from backend.utils.goal_memory import update_goal, get_or_create_goal
from backend.utils.confidence import build_confidence_report, build_fallback_message
from backend.utils.site_intelligence import get_site_context_string
from backend.utils.context_intelligence import synthesize_context
from backend.memory.service import update_rolling_summary


logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# ROBOTIC PHRASE FILTER
# ---------------------------------------------------------------------------

_ROBOTIC_PHRASES = [
    r"i['']d be happy to help",
    r"i['']m happy to assist",
    r"i['']m here to help",
    r"as an ai",
    r"as a language model",
    r"based on the (?:retrieved )?context[,.]?",
    r"based on the (?:provided )?information[,.]?",
    r"based on what i(?:'ve| have) found[,.]?",
    r"could you (?:please )?clarify\??",
    r"could you (?:please )?specify\??",
    r"please (?:note that )?i cannot provide",
    r"i (?:must |need to )?clarify that",
    r"it['']s important to note that",
    r"please be aware that",
    r"i (?:do not|don['']t) have access to real.?time",
    r"i (?:am|'m) unable to provide",
    r"of course[,!]? (?:here|let me)",
    r"certainly[,!]? (?:here|let me|i)",
    r"absolutely[,!]? (?:here|let me|i)",
    r"great question[,!]?",
    r"sure[,!]? (?:here|let me|i)",
]

_ROBOTIC_RE = [re.compile(p, re.IGNORECASE) for p in _ROBOTIC_PHRASES]


def _strip_robotic_phrases(text: str) -> str:
    """Remove filler/robotic openings from generated text."""
    for pattern in _ROBOTIC_RE:
        text = pattern.sub("", text)
    # Clean up double spaces and leading punctuation from removal
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^\s*[,.:!]\s*", "", text)
    return text.strip()


def _has_placeholders(text: str) -> bool:
    """Detect if text contains bracket placeholders like [Place] or [Institution]."""
    return bool(re.search(r'\[[A-Z][^\]]{2,40}\]', text))


def _strip_placeholders(text: str) -> str:
    """Remove bracket placeholders and replace with natural language."""
    return re.sub(r'\[[A-Z][^\]]{2,40}\]', 'relevant content', text)


# ---------------------------------------------------------------------------
# INTENT DETECTION — keyword + semantic hybrid
# ---------------------------------------------------------------------------

INTENT_PATTERNS: dict[str, list[str]] = {
    # Tourism
    "tourism_planner":          ["plan", "itinerary", "trip", "travel", "visit", "schedule", "route", "weekend"],
    "attraction_recommender":   ["attractions", "things to do", "places to see", "must see", "popular", "best places"],
    "ride_optimizer":           ["wait time", "queue", "rides", "skip the line", "fast pass", "thrill"],

    # Education
    "course_finder":            ["course", "program", "major", "degree", "study", "curriculum", "syllabus"],
    "admission_assistant":      ["admission", "apply", "enroll", "deadline", "requirements", "eligibility"],
    "scholarship_helper":       ["scholarship", "financial aid", "grant", "funding", "bursary", "fees"],

    # Medical
    "dept_navigator":           ["department", "specialist", "pain", "symptom", "doctor", "consult", "hospital"],
    "appointment_guidance":     ["appointment", "book", "schedule", "visiting hours", "contact", "reserve"],
    "insurance_assistant":      ["insurance", "coverage", "billing", "payment", "claims", "premium"],

    # Developer
    "api_assistant":            ["api", "sdk", "code", "endpoint", "authenticate", "bearer", "token", "rest"],
    "integration_helper":       ["integrate", "integration", "webhook", "event", "flow", "setup", "connect"],
    "sdk_guide":                ["install", "library", "npm", "pip", "package", "init", "import"],

    # Ecommerce
    "shopping_guide":           ["product", "buy", "price", "pricing", "catalog", "compare", "best", "order"],

    # General
    "doc_summarizer":           ["summarize", "summary", "overview", "what is this", "tell me about", "highlights"],
}

DOMAIN_SKILL_MAP: dict[str, list[str]] = {
    "tourism":   ["tourism_planner", "attraction_recommender", "ride_optimizer", "doc_summarizer"],
    "education": ["course_finder", "admission_assistant", "scholarship_helper", "doc_summarizer"],
    "medical":   ["dept_navigator", "appointment_guidance", "insurance_assistant", "doc_summarizer"],
    "developer": ["api_assistant", "integration_helper", "sdk_guide", "doc_summarizer"],
    "ecommerce": ["shopping_guide", "doc_summarizer"],
    "general":   ["doc_summarizer"],
}

# ---------------------------------------------------------------------------
# PROACTIVE RECOMMENDATION ENGINE
# ---------------------------------------------------------------------------

def get_proactive_suggestions(domain: str, intent: str, goal: str | None = None) -> list[str]:
    """Build domain-specific proactive suggestions based on current intent/goal."""
    base_suggestions = {
        "tourism": ["Tell me about top attractions", "Plan a 3-day itinerary", "Show local hotels"],
        "education": ["View admission requirements", "Find available scholarships", "Browse course catalog"],
        "medical": ["Book an appointment", "Find a specialist", "View insurance coverage"],
        "developer": ["Show API authentication", "View integration guide", "Download SDK"],
        "ecommerce": ["View latest offers", "Track my order", "Check return policy"],
        "general": ["Summarize this site", "What services are offered?", "Contact support"],
    }
    
    intent_suggestions = {
        "tourism_planner": ["Add child-friendly spots", "Suggest budget options", "Check weather for my trip"],
        "admission_assistant": ["Check deadline for fall semester", "Required documents for application", "Contact admissions office"],
        "api_assistant": ["Show cURL examples", "View error codes", "Check rate limits"],
    }
    
    res = intent_suggestions.get(intent, [])
    if not res:
        res = base_suggestions.get(domain, base_suggestions["general"])
        
    return res[:3]

def extract_goal_from_history(history: list[dict]) -> str | None:
    """Extract a likely goal from the last few user messages."""
    for h in reversed(history):
        if h.get("role") == "user":
            msg = h.get("content", "").lower()
            if len(msg) > 10:
                # Basic extraction: try to find "i want to", "how do i", etc.
                match = re.search(r"(?:i want to|how do i|i'm looking for|tell me about)\s+(.+)", msg)
                if match:
                    return match.group(1).capitalize()
    return None


def detect_intent(query: str, domain: str | None) -> tuple[str, int, float]:
    """
    Hybrid intent detection: keyword patterns + semantic similarity.
    Returns (intent_name, keyword_score, semantic_score).
    """
    q = query.lower()
    if domain and domain != "general":
        eligible = DOMAIN_SKILL_MAP.get(domain, ["doc_summarizer"])
    else:
        eligible = list(INTENT_PATTERNS.keys())

    # 1. Keyword scoring
    scores: dict[str, int] = {skill: 0 for skill in eligible}
    for skill in eligible:
        for kw in INTENT_PATTERNS.get(skill, []):
            if kw in q:
                scores[skill] += 1

    best_kw_skill = max(scores, key=scores.get, default="general_chat")
    kw_score = scores.get(best_kw_skill, 0)
    if kw_score > 0:
        return best_kw_skill, kw_score, 0.6

    # 2. Semantic fallback
    sem_intent = intent_intelligence.detect(query, eligible_skills=eligible)
    return sem_intent, 0, 0.5


# ---------------------------------------------------------------------------
# CONTEXT RETRIEVAL — strict scoping
# ---------------------------------------------------------------------------

async def _get_context(
    query: str, chatbot_id: int | None, domain: str | None = None, workflow: str | None = None
) -> tuple[list, str, float]:
    """Hybrid retrieval with strict chatbot_id scoping and workflow boosting."""
    t0 = time.monotonic()
    chunks = await async_retrieve(query, top_k=settings.top_k, chatbot_id=chatbot_id, domain=domain, workflow=workflow)

    elapsed = (time.monotonic() - t0) * 1000

    # STRICT SECURITY: Double-check every chunk belongs to this chatbot
    if chatbot_id:
        before = len(chunks)
        chunks = [c for c in chunks if c.metadata.get("chatbot_id") == chatbot_id]
        filtered = before - len(chunks)
        if filtered > 0:
            logger.warning(
                f"[SECURITY] Filtered {filtered} cross-chatbot chunks for chatbot_id={chatbot_id}"
            )

    if not chunks:
        return [], "", elapsed

    context_str = "\n\n".join(
        f"[Source {i+1}: {c.document}]\n{c.text}"
        for i, c in enumerate(chunks)
    )
    return chunks, context_str, elapsed


# ---------------------------------------------------------------------------
# CHATBOT LOOKUP — strict session isolation
# ---------------------------------------------------------------------------

async def _get_chatbot(
    db: AsyncSession,
    chatbot_id: int | None = None,
    session_id: str | None = None,
) -> "Chatbot | None":
    chatbot = None
    if chatbot_id:
        chatbot = await db.get(Chatbot, chatbot_id)

    if session_id and chatbot_id:
        # Verify session belongs to THIS chatbot (prevent cross-contamination)
        stmt = select(Conversation).where(
            Conversation.session_id == session_id,
            Conversation.chatbot_id == chatbot_id,
        )
        conv = (await db.execute(stmt)).scalar_one_or_none()
        if conv is None:
            # Session exists for a different chatbot — isolation enforced
            other = (await db.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            )).scalar_one_or_none()
            if other and other.chatbot_id != chatbot_id:
                logger.error(
                    f"[SECURITY] Session isolation violation: session={session_id} "
                    f"belongs to chatbot={other.chatbot_id}, requested chatbot={chatbot_id}. Denying."
                )
                return None

    return chatbot


# ---------------------------------------------------------------------------
# DYNAMIC PROMPT LAYERING
# ---------------------------------------------------------------------------

def _build_prompt(
    query: str,
    history: list[dict],
    context_str: str,
    bp,
    intent: str,
    conversation_mode: str = "exploratory",
    user_goal: str | None = None,
    workflow_stage: str = "browsing",
    user_type: str = "new_visitor",
    site_context: str = "",
    confidence_note: str = "",
    response_plan: str = "",
    context_snapshot: str = "",
) -> str:
    """
    Dynamic prompt layering:
      Layer 1: Base instructions (entity rules, security, citation rules)
      Layer 2: Domain behavior profile
      Layer 3: Skill guidance (intent-specific task instructions)
      Layer 4: Conversation mode adaptation
      Layer 5: User goal + workflow context
      Layer 6: Site intelligence (persistent contextual awareness)
      Layer 7: Retrieved context (grounding)
    """
    no_context_note = (
        "No specific content was retrieved from the knowledge base for this query. "
        "Provide the most helpful answer you can from domain knowledge. "
        "Do NOT fabricate specific names, prices, or details."
    )

    skill_guidance = get_skill_guidance(intent)

    # Layer 4: Conversation mode adaptation
    mode_instructions = {
        "planning": (
            "USER MODE: Planning — the user wants to create a structured plan or itinerary. "
            "Respond with a concrete plan, not just information. Use Morning/Afternoon/Evening breakdowns where relevant."
        ),
        "troubleshooting": (
            "USER MODE: Troubleshooting — the user has a problem. "
            "Lead with the solution. Skip preamble. Use numbered steps."
        ),
        "comparison": (
            "USER MODE: Comparison — the user is evaluating options. "
            "Use a structured comparison format (table or bullet list). Highlight key differences."
        ),
        "support": (
            "USER MODE: Support — the user needs actionable assistance. "
            "Provide direct next steps with contact info or links where available."
        ),
        "onboarding": (
            "USER MODE: Onboarding — the user is new and unfamiliar. "
            "Be welcoming. Explain with context. Avoid jargon."
        ),
        "exploratory": (
            "USER MODE: Exploratory — the user is browsing and learning. "
            "Be informative and suggest related topics proactively."
        ),
    }
    mode_note = mode_instructions.get(conversation_mode, mode_instructions["exploratory"])

    # Layer 5: User goal
    goal_note = ""
    if user_goal:
        goal_note = (
            f"USER GOAL: {user_goal} | Stage: {workflow_stage} | Type: {user_type}\n"
            "Use this goal context to make your response more targeted and proactive."
        )

    # Layer 6: Site intelligence
    site_note = f"SITE CONTEXT:\n{site_context}\n" if site_context else ""

    # Assemble system prompt
    system_parts = [
        bp.instructions,
        f"TONE: {bp.tone}",
        f"SKILL GUIDANCE: {skill_guidance}",
        mode_note,
    ]
    if goal_note:
        system_parts.append(goal_note)
    if site_note:
        system_parts.append(site_note)
    if confidence_note:
        system_parts.append(f"CONFIDENCE NOTE: {confidence_note}")

    if response_plan:
        system_parts.append(f"RESPONSE PLAN:\n{response_plan}")
    if context_snapshot:
        system_parts.append(f"CONTEXT SNAPSHOT (Analyzed Facts):\n{context_snapshot}")
        
    system = "\n\n".join(system_parts)

    # Hard constraints injected last (recency bias)
    constraints = (
        "ABSOLUTE CONSTRAINTS (highest priority — override everything above):\n"
        "- NEVER use bracketed placeholders: no [Name], [Place], [Details], [etc].\n"
        "- NEVER use generic templates or placeholders in your response.\n"
        "- NEVER use robot-filler: 'I'd be happy to help', 'Based on the context', 'Let's dive into', "
        "'Could you clarify?', 'As an AI', 'Certainly!', 'Of course!', 'Great question!', 'I understand'.\n"
        "- START DIRECTLY with the information. No conversational fluff or introductions.\n"
        "- If context is missing specific names, say 'The system does not specify the name' naturally.\n"
        "- Every factual claim must be grounded in the RETRIEVED CONTEXT above.\n"
        "- NEVER fabricate names, prices, phone numbers, or dates not in the context.\n"
        "- If you are not 100% sure about a specific detail, omit it or describe it generally."
    )

    parts = [f"SYSTEM: {system}"]
    for h in history[-8:]:
        role = h.get("role", "user").upper()
        parts.append(f"{role}: {h['content']}")

    parts.append(f"INSTRUCTION: {constraints}")
    parts.append(f"USER: {query}")
    parts.append("ASSISTANT:")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# POST-PROCESSING
# ---------------------------------------------------------------------------

def _post_process_answer(answer: str) -> tuple[str, bool]:
    """
    Clean up the generated answer.
    Returns (cleaned_answer, had_hallucination_warning).
    """
    had_warning = False

    # 1. Robotic Phrase Stripping
    answer = _strip_robotic_phrases(answer)

    # 2. Sanitization (Safety Layer)
    answer = sanitize_output(answer)

    # 3. Placeholder Detection & Cleanup
    if _has_placeholders(answer):
        had_warning = True
        logger.warning("[ORCHESTRATOR] Bracket placeholder detected in answer — stripping.")
        answer = _strip_placeholders(answer)
        if _has_placeholders(answer):
             # Final fallback if stripping failed
             answer = "The specific details for that query (such as exact names or dates) weren't clearly identified in the site content. I can provide a general overview instead."

    # 4. Final Cleanup (double spaces, trailings)
    answer = re.sub(r'\s+', ' ', answer).strip()
    
    return answer, had_warning


# ---------------------------------------------------------------------------
# DOMAIN DETECTION with confidence
# ---------------------------------------------------------------------------

def _detect_domain_with_confidence(
    query: str, chatbot: "Chatbot | None"
) -> tuple[str, float]:
    """
    Returns (domain, confidence_score).
    Uses the hardened DomainDetector logic.
    """
    chatbot_domain = chatbot.domain if chatbot else None
    if chatbot_domain and chatbot_domain != "general":
        return chatbot_domain, 0.95

    # Use the centralized detector which already has confidence logic
    detected_domain = domain_detector.detect(query, {"url": chatbot.website_url if chatbot else ""})
    
    # Calculate confidence for the report
    scores = domain_detector.get_scores(query, {"url": chatbot.website_url if chatbot else ""})
    if not scores:
        return "general", 0.3
        
    sorted_scores = sorted(scores, key=lambda x: x.score, reverse=True)
    top = sorted_scores[0]
    second = sorted_scores[1].score if len(sorted_scores) > 1 else 0.0
    
    gap = (top.score - second) / (top.score + 1e-9)
    conf = min(0.4 + gap * 0.5, 0.95) if top.score > 1.0 else 0.3
    
    return detected_domain, round(conf, 2)


# ---------------------------------------------------------------------------
# PUBLIC API — Non-streaming (HTTP /chat fallback)
# ---------------------------------------------------------------------------

async def run_orchestration(
    query: str,
    history: list[dict],
    db: AsyncSession,
    chatbot_id: int | None = None,
    session_id: str | None = None,
    domain: str | None = None,
    profile: str | None = None,
) -> dict:
    query = sanitize_input(query)

    # --- 1. Session isolation ---
    chatbot = await _get_chatbot(db, chatbot_id, session_id)
    if chatbot is None and chatbot_id:
        logger.error(f"[SECURITY] Session isolation denied access for chatbot_id={chatbot_id}")
        return {
            "answer": "Session error: unable to verify chatbot identity. Please refresh and try again.",
            "citations": [], "intent": "error", "domain": "general", "profile": "general",
        }

    effective_id = chatbot.id if chatbot else None

    # --- 2. Domain detection with confidence ---
    effective_domain, domain_conf = _detect_domain_with_confidence(query, chatbot)
    if domain:
        effective_domain = domain  # caller override
        domain_conf = 0.95

    # --- 3. Intent detection ---
    intent, kw_score, sem_score = detect_intent(query, effective_domain)

    # --- 4. Query expansion before retrieval ---
    expanded_query = expand_query(query, domain=effective_domain)
    if expanded_query != query.lower():
        logger.debug(f"[EXPAND] '{query}' → '{expanded_query}'")

    # --- 5. Retrieval with expanded query ---
    chunks, context_str, retrieval_ms = await _get_context(expanded_query, effective_id, domain=effective_domain)

    # --- 6. Confidence scoring ---
    from backend.utils.domain_intelligence import domain_detector as _dd
    domain_scores = _dd.get_scores(query, {"url": chatbot.website_url if chatbot else ""})
    confidence = build_confidence_report(
        chunks=chunks,
        query=query,
        domain=effective_domain,
        intent=intent,
        keyword_score=kw_score,
        semantic_score=sem_score,
        detected_scores=domain_scores,
    )

    # --- 7. User goal memory & Rolling Summary ---
    goal = None
    rolling_summary = ""
    if session_id and effective_id:
        from backend.memory.service import get_conversation_by_session
        conv = await get_conversation_by_session(db, session_id, effective_id)
        goal = await update_goal(db, session_id, effective_id, query, intent, domain=effective_domain)
        if conv:
            rolling_summary = await update_rolling_summary(db, conv.id)


    # --- 8. Site intelligence ---
    site_context = ""
    if chatbot and chatbot.site_profile:
        site_context = get_site_context_string(chatbot.site_profile)
        # Inject relationship mappings into site context if present
        if chatbot.site_profile.get("relationships"):
            site_context += "\nKNOWN RELATIONSHIPS:\n- " + "\n- ".join(chatbot.site_profile["relationships"])

    # --- 8b. Workflow-Aware Retrieval (Turn 2) ---
    # If we have a clear workflow but first retrieval was generic, try again with boosting
    if goal and goal.active_workflow and not chunks:
        chunks, context_str, _ = await _get_context(expanded_query, effective_id, domain=effective_domain, workflow=goal.active_workflow)


    # --- 9. Graceful fallback if confidence too low ---
    # External Research Fallback (Tavily)
    external_context = ""
    if not chunks or (confidence.retrieval_confidence < 0.3 and len(query.split()) > 3):
        from backend.llm.tavily_client import tavily_client
        logger.info(f"[ORCHESTRATOR] Low confidence ({confidence.retrieval_confidence}). Triggering Tavily.")
        tavily_results = await tavily_client.search(query)
        if tavily_results:
            external_context = "\nEXTERNAL RESEARCH RESULTS:\n" + "\n".join(
                [f"Source: {r['url']}\nContent: {r['text']}" for r in tavily_results]
            )

    if not confidence.should_infer and not chunks and not external_context:
        fallback_msg = build_fallback_message(confidence, effective_domain)
        # ... (tracking logic)
        return {
            "answer": fallback_msg,
            "citations": [],
            "intent": intent,
            "suggestions": [],
            "domain": effective_domain,
            "profile": "general",
            "confidence": confidence.overall,
        }

    # --- 10. Context Aggregation & Synthesis ---
    full_raw_context = context_str + external_context
    context_snapshot = None
    if full_raw_context:
        context_snapshot = await synthesize_context(
            query=query, 
            chunks=chunks, 
            goal=goal.current_goal if goal else None
        )
    
    context_snapshot_str = str(context_snapshot) if context_snapshot else ""


    # --- 11. Response Planning ---
    planning_prompt = f"""
    You are an expert architect planning a response for: {query}
    Context Snapshot: {context_snapshot}
    User Goal: {goal.current_goal if goal else 'General inquiry'}
    
    Create a structured plan covering:
    1. GOAL: What is the user trying to achieve?
    2. WORKFLOW: Which specific site workflow is relevant?
    3. REASONING: Step-by-step logic to solve the query.
    
    FORMAT: 
    GOAL: [Goal]
    WORKFLOW: [Workflow]
    PLAN: [Steps]
    """
    response_plan = ""
    try:
        response_plan = await ollama_client.generate(planning_prompt, model=settings.ollama_model)
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Response planning failed: {e}")
        response_plan = "Answer directly based on context."

    # --- 12. Build dynamic prompt ---
    bp = get_profile(effective_domain)
    confidence_note = (
        f"Retrieval confidence: {confidence.retrieval_confidence:.0%}. "
        + (f"Reason: {confidence.fallback_reason}" if confidence.fallback_reason else "")
    ) if confidence.retrieval_confidence < 0.4 else ""

    prompt = _build_prompt(
        query=query,
        history=history,
        context_str=full_raw_context,
        bp=bp,
        intent=intent,
        conversation_mode=goal.conversation_mode if goal else "exploratory",
        user_goal=goal.current_goal if goal else None,
        workflow_stage=goal.workflow_stage if goal else "browsing",
        user_type=goal.user_type if goal else "new_visitor",
        site_context=site_context + (f"\nCONVERSATION SUMMARY: {rolling_summary}" if rolling_summary else ""),
        confidence_note=confidence_note,
        response_plan=response_plan,
        context_snapshot=context_snapshot_str,
    )

    # --- 11. Generate ---
    t0 = time.monotonic()
    raw_answer = await ollama_client.generate(prompt, model=settings.ollama_model)
    llm_ms = (time.monotonic() - t0) * 1000

    # --- 12. Post-process ---
    answer, had_warning = _post_process_answer(raw_answer)

    # --- 13. Track ---
    await track_query(
        query=query,
        intent=intent,
        domain=effective_domain,
        retrieved_chunks=len(chunks),
        retrieval_ms=retrieval_ms,
        llm_ms=llm_ms,
        answered=bool(chunks),
        confidence=confidence.overall,
        fallback=not confidence.should_infer,
        hallucination_warning=had_warning,
        conversation_mode=goal.conversation_mode if goal else "exploratory",
    )

    suggestions = get_proactive_suggestions(effective_domain, intent, goal.current_goal if goal else None)
    
    return {
        "answer": answer,
        "citations": [c.__dict__ for c in chunks],
        "intent": intent,
        "suggestions": suggestions if not history else [],
        "domain": effective_domain,
        "profile": bp.name,
        "confidence": confidence.overall,
        "goal": goal.current_goal if goal else None,
        "conversation_mode": goal.conversation_mode if goal else "exploratory",
    }


# ---------------------------------------------------------------------------
# PUBLIC API — Streaming (WebSocket /ws/chat)
# ---------------------------------------------------------------------------

async def run_orchestration_stream(
    query: str,
    history: list[dict],
    db: AsyncSession,
    chatbot_id: int | None = None,
    session_id: str | None = None,
):
    query = sanitize_input(query)

    # --- Session isolation ---
    chatbot = await _get_chatbot(db, chatbot_id, session_id)
    if chatbot is None and chatbot_id:
        yield {"type": "error", "content": "Session isolation: chatbot identity mismatch. Please refresh."}
        return

    effective_id = chatbot.id if chatbot else None

    # --- Domain + confidence ---
    effective_domain, domain_conf = _detect_domain_with_confidence(query, chatbot)

    # --- Intent ---
    intent, kw_score, sem_score = detect_intent(query, effective_domain)

    # --- Query expansion ---
    expanded_query = expand_query(query, domain=effective_domain)

    # --- Retrieval ---
    chunks, context_str, retrieval_ms = await _get_context(expanded_query, effective_id, domain=effective_domain)

    # --- Confidence ---
    from backend.utils.domain_intelligence import domain_detector as _dd
    domain_scores = _dd.get_scores(query, {"url": chatbot.website_url if chatbot else ""})
    confidence = build_confidence_report(
        chunks=chunks, query=query, domain=effective_domain, intent=intent,
        keyword_score=kw_score, semantic_score=sem_score, detected_scores=domain_scores,
    )

    # --- Goal memory & Rolling Summary ---
    goal = None
    rolling_summary = ""
    if session_id and effective_id:
        from backend.memory.service import get_conversation_by_session
        conv = await get_conversation_by_session(db, session_id, effective_id)
        goal = await update_goal(db, session_id, effective_id, query, intent, domain=effective_domain)
        if conv:
            rolling_summary = await update_rolling_summary(db, conv.id)


    # --- Site intelligence ---
    site_context = ""
    if chatbot and chatbot.site_profile:
        site_context = get_site_context_string(chatbot.site_profile)
        if chatbot.site_profile.get("relationships"):
            site_context += "\nKNOWN RELATIONSHIPS:\n- " + "\n- ".join(chatbot.site_profile["relationships"])

    # --- 8b. Workflow-Aware Retrieval (Turn 2) ---
    if goal and goal.active_workflow and not chunks:
        chunks, context_str, _ = await _get_context(expanded_query, effective_id, domain=effective_domain, workflow=goal.active_workflow)


    # Emit metadata
    yield {
        "type": "metadata",
        "citations": [c.__dict__ for c in chunks],
        "intent": intent,
        "domain": effective_domain,
        "confidence": confidence.overall,
        "conversation_mode": goal.conversation_mode if goal else "exploratory",
        "goal": goal.current_goal if goal else None,
    }

    # --- External Research Fallback (Tavily) ---
    external_context = ""
    if not chunks or (confidence.retrieval_confidence < 0.3 and len(query.split()) > 3):
        from backend.llm.tavily_client import tavily_client
        logger.info(f"[ORCHESTRATOR] Low confidence ({confidence.retrieval_confidence}). Triggering Tavily.")
        tavily_results = await tavily_client.search(query)
        if tavily_results:
            external_context = "\nEXTERNAL RESEARCH RESULTS:\n" + "\n".join(
                [f"Source: {r['url']}\nContent: {r['text']}" for r in tavily_results]
            )

    # --- Context Aggregation & Synthesis ---
    full_raw_context = context_str + external_context
    context_snapshot = None
    if full_raw_context:
        context_snapshot = await synthesize_context(
            query=query, 
            chunks=chunks, 
            goal=goal.current_goal if goal else None
        )
    
    context_snapshot_str = str(context_snapshot) if context_snapshot else ""


    # --- Response Planning ---
    planning_prompt = f"""
    You are an expert architect planning a response for: {query}
    Context Snapshot: {context_snapshot_str}
    User Goal: {goal.current_goal if goal else 'General inquiry'}

    
    Create a structured plan covering:
    1. GOAL: What is the user trying to achieve?
    2. WORKFLOW: Which specific site workflow is relevant?
    3. REASONING: Step-by-step logic to solve the query.
    
    FORMAT: 
    GOAL: [Goal]
    WORKFLOW: [Workflow]
    PLAN: [Steps]
    """
    response_plan = ""
    try:
        response_plan = await ollama_client.generate(planning_prompt, model=settings.ollama_model)
    except Exception as e:
        logger.warning(f"[ORCHESTRATOR] Response planning failed: {e}")
        response_plan = "Answer directly based on context."

    # Yield planning step for Reasoning Transparency
    yield {
        "type": "thought",
        "content": response_plan
    }

    # --- Build dynamic prompt ---
    bp = get_profile(effective_domain)
    confidence_note = (
        f"Retrieval confidence: {confidence.retrieval_confidence:.0%}. "
        + (f"Reason: {confidence.fallback_reason}" if confidence.fallback_reason else "")
    ) if confidence.retrieval_confidence < 0.4 else ""

    prompt = _build_prompt(
        query=query,
        history=history,
        context_str=full_raw_context,
        bp=bp,
        intent=intent,
        conversation_mode=goal.conversation_mode if goal else "exploratory",
        user_goal=goal.current_goal if goal else None,
        workflow_stage=goal.workflow_stage if goal else "browsing",
        user_type=goal.user_type if goal else "new_visitor",
        site_context=site_context + (f"\nCONVERSATION SUMMARY: {rolling_summary}" if rolling_summary else ""),
        confidence_note=confidence_note,
        response_plan=response_plan,
        context_snapshot=context_snapshot_str,
    )

    # --- Stream ---
    t0 = time.monotonic()
    full_answer = ""
    async for token in ollama_client.generate_stream(prompt, model=settings.ollama_model):
        full_answer += token
        yield {"type": "token", "content": token}

    llm_ms = (time.monotonic() - t0) * 1000

    # Post-process the full streamed answer
    cleaned, had_warning = _post_process_answer(full_answer)

    # Track
    await track_query(
        query=query,
        intent=intent,
        domain=effective_domain,
        retrieved_chunks=len(chunks),
        retrieval_ms=retrieval_ms,
        llm_ms=llm_ms,
        answered=bool(chunks),
        confidence=confidence.overall,
        fallback=not confidence.should_infer,
        hallucination_warning=had_warning,
        conversation_mode=goal.conversation_mode if goal else "exploratory",
    )

    # Final metadata
    suggestions = get_proactive_suggestions(effective_domain, intent, goal.current_goal if goal else None)
    yield {
        "type": "final",
        "answer": cleaned,
        "citations": [c.__dict__ for c in chunks],
        "confidence": confidence.overall,
        "suggestions": suggestions if not history else [],
        "goal": goal.current_goal if goal else None,
    }
