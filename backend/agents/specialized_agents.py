import re
import json
from backend.llm import ollama_client
from backend.config.settings import get_settings
from typing import Any

settings = get_settings()

PROACTIVE_RULES = """
- Be proactive. If a user asks a question, anticipate their next step.
- Grounded: Only use the provided context.
- Workflow-Aware: If a process is detected, guide the user through the next logical step.
"""

async def tour_guide_skill(query: str, website_context: str) -> str:
    """Tourism: Recommends places and plans itineraries."""
    prompt = f"""You are an expert tour guide. Based on the query: {query}
    {PROACTIVE_RULES}
    
    CONTEXT: {website_context}
    
    REQUIREMENTS:
    - List the top 3 spots with specific descriptions from the context.
    - Provide a mini-itinerary for one day.
    - Mention one "local tip" found in the context.
    """
    return await ollama_client.generate(prompt, model=settings.ollama_model)

async def admission_assistant_skill(query: str, website_context: str) -> str:
    """Education: Admissions and Financial Aid."""
    prompt = f"""You are an Admissions Officer. Help the user with: {query}
    {PROACTIVE_RULES}
    
    CONTEXT: {website_context}
    
    REQUIREMENTS:
    - List key admission deadlines mentioned in the context.
    - Detail the required documents (ID, Transcripts, etc.).
    - Provide the exact link or email for the admissions office.
    """
    return await ollama_client.generate(prompt, model=settings.ollama_model)

async def financial_aid_skill(query: str, website_context: str) -> str:
    """Education: Scholarships and Funding."""
    prompt = f"""Identify scholarship and financial aid opportunities for: {query}
    {PROACTIVE_RULES}
    
    CONTEXT: {website_context}
    
    REQUIREMENTS:
    - List specific scholarships with their eligibility criteria.
    - State the award amounts and deadlines.
    - Provide application steps.
    """
    return await ollama_client.generate(prompt, model=settings.ollama_model)

async def appointment_guidance_skill(query: str, website_context: str) -> str:
    """Medical: Booking guidance."""
    prompt = f"""Guide the user on how to book an appointment for: {query}
    {PROACTIVE_RULES}
    
    CONTEXT: {website_context}
    
    REQUIREMENTS:
    - Provide the central booking number or link.
    - Detail what the user needs to bring (ID, insurance, etc.).
    - List available time slots or office hours if mentioned.
    """
    return await ollama_client.generate(prompt, model=settings.ollama_model)

async def insurance_assistant_skill(query: str, website_context: str) -> str:
    """Medical: Coverage details."""
    prompt = f"""Clarify insurance coverage and billing for: {query}
    {PROACTIVE_RULES}
    
    CONTEXT: {website_context}
    
    REQUIREMENTS:
    - List accepted insurance providers found in the context.
    - Explain the billing process or co-pay requirements.
    - Be precise — do not guess if not in the context.
    """
    return await ollama_client.generate(prompt, model=settings.ollama_model)

async def integration_helper_skill(query: str, website_context: str) -> str:
    """Developer: Complex integration architecture."""
    prompt = f"""Design a system integration flow for: {query}
    {PROACTIVE_RULES}
    
    CONTEXT: {website_context}
    
    REQUIREMENTS:
    - Focus on webhooks, event flows, and error handling.
    - Provide a sequence diagram or logic flow (in Markdown).
    - Detail security best practices (retry logic, signature verification).
    """
    return await ollama_client.generate(prompt, model=settings.ollama_model)

async def sdk_guide_skill(query: str, website_context: str) -> str:
    """Developer: SDK setup."""
    prompt = f"""Provide a setup guide for the SDK: {query}
    {PROACTIVE_RULES}
    
    CONTEXT: {website_context}
    
    REQUIREMENTS:
    - Show installation commands (npm, pip, etc.).
    - Show the initialization code block.
    - Detail 3 common SDK functions and their parameters.
    """
    return await ollama_client.generate(prompt, model=settings.ollama_model)

async def shopping_guide_skill(query: str, website_context: str) -> str:
    """Ecommerce: Product recommendation and comparison."""
    prompt = f"""Compare the best product options for: {query}
    {PROACTIVE_RULES}
    
    CONTEXT: {website_context}
    
    REQUIREMENTS:
    - Use a Markdown table to compare 3-5 products.
    - Categories: Product Name, Price, Key Feature, Best For.
    - Recommend the best overall choice with a reason.
    """
    return await ollama_client.generate(prompt, model=settings.ollama_model)


# ---------------------------------------------------------------------------
# LEGACY / UTILITY AGENTS (to be kept for backend processing)
# ---------------------------------------------------------------------------

async def extract_structured_data(text: str) -> dict:
    """Extracts business metrics and entities into a structured JSON format."""
    prompt = f"""
    Extract key business metrics, entities, and dates from the following text.
    Return ONLY a valid JSON object.
    
    Schema:
    {{
        "entities": ["names"],
        "metrics": {{ "key": "val" }},
        "dates": ["YYYY-MM-DD"],
        "confidence": 0.0-1.0
    }}
    
    Text: {text}
    """
    raw = await ollama_client.generate(prompt, model=settings.ollama_model)
    try:
        match = re.search(r"(\{.*\})", raw, re.DOTALL)
        if match: return json.loads(match.group(1))
        return {}
    except: return {}


async def orchestrate_tasks(text: str, session_id: str | None = None, db: Any = None) -> list[dict]:
    """Identifies and logs action items from conversational or document text."""
    prompt = f"""
    Identify all action items, owners, and deadlines from the text.
    Return ONLY a valid JSON list of objects:
    [
        {{ "task": "description", "owner": "name", "deadline": "date" }}
    ]
    
    Text: {text}
    """
    raw = await ollama_client.generate(prompt, model=settings.ollama_model)
    try:
        match = re.search(r"(\[.*\])", raw, re.DOTALL)
        if not match: return []
        tasks_data = json.loads(match.group(1))
        return tasks_data
    except: return []
