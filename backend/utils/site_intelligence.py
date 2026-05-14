import logging
import re
import json
from typing import Dict, Any, List
from backend.llm.ollama_client import ollama_client
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def _detect_relationships(text: str) -> List[str]:
    """Lightweight regex-based relationship detection."""
    patterns = [
        (r"(\w+)\s+(?:requires|needs|depends on)\s+(\w+)", "requires"),
        (r"(\w+)\s+(?:is part of|belongs to)\s+(\w+)", "belongs_to"),
        (r"(\w+)\s+(?:powers|enables|supports)\s+(\w+)", "enables"),
        (r"(\w+)\s+(?:located in|found at)\s+(\w+)", "location"),
    ]
    rels = []
    for p, label in patterns:
        matches = re.findall(p, text, re.I)
        for m1, m2 in matches:
            rels.append(f"{m1} {label} {m2}")
    return list(set(rels))

async def build_site_profile(all_text: str, domain: str, site_url: str) -> Dict[str, Any]:
    """Generates a structured summary and intelligence layer for a website."""
    
    # Use only a sample of the text for the summary to save tokens
    sample = all_text[:8000]
    
    prompt = f"""
    Analyze this website content from {site_url} (Domain: {domain}).
    Provide a professional site profile including:
    1. Summary: 2-3 sentences describing the site's purpose.
    2. Key Entities: List the most important products, organizations, or people.
    3. Detected Workflows: List 3-5 user processes (e.g., 'Booking a Room', 'API Authentication').
    
    Return ONLY a JSON object:
    {{
        "summary": "...",
        "top_entities": [],
        "workflows": []
    }}
    
    CONTENT:
    {sample}
    """
    
    profile = {
        "summary": f"A {domain} website at {site_url}.",
        "top_entities": [],
        "workflows": [],
        "relationships": _detect_relationships(all_text[:20000]) # Scan more for relationships
    }
    
    try:
        raw = await ollama_client.generate(prompt, model=settings.ollama_model)
        import re
        match = re.search(r"(\{.*\})", raw, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            profile.update(data)
    except Exception as e:
        logger.error(f"[SITE-INTEL] Profile generation failed: {e}")
        
    return profile

def get_site_context_string(profile: Dict[str, Any]) -> str:
    """Formats the profile for injection into prompts."""
    if not profile: return ""
    
    res = [f"SITE SUMMARY: {profile.get('summary', '')}"]
    if profile.get("top_entities"):
        res.append(f"KEY ENTITIES: {', '.join(profile['top_entities'])}")
    if profile.get("workflows"):
        res.append(f"COMMON WORKFLOWS: {', '.join(profile['workflows'])}")
        
    return "\n".join(res)
