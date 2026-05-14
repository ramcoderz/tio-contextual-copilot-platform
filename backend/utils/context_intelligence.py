import logging
from typing import List, Dict, Any, Optional
from backend.llm.ollama_client import ollama_client
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ContextSnapshot:
    def __init__(self, facts: List[str], workflows: List[str], entities: List[str], relationships: List[str]):
        self.facts = facts
        self.workflows = workflows
        self.entities = entities
        self.relationships = relationships

    def __str__(self):
        res = []
        if self.facts: res.append(f"FACTS:\n- " + "\n- ".join(self.facts))
        if self.workflows: res.append(f"WORKFLOWS:\n- " + "\n- ".join(self.workflows))
        if self.entities: res.append(f"ENTITIES:\n- " + "\n- ".join(self.entities))
        if self.relationships: res.append(f"RELATIONSHIPS:\n- " + "\n- ".join(self.relationships))
        return "\n\n".join(res)

async def synthesize_context(query: str, chunks: List[Any], goal: Optional[str] = None) -> ContextSnapshot:
    """
    Transforms raw retrieval chunks into a structured ContextSnapshot.
    """
    if not chunks:
        return ContextSnapshot([], [], [], [])

    context_text = "\n".join([c.text for c in chunks])
    
    prompt = f"""
    Analyze the following retrieved context for the query: "{query}"
    User Goal: {goal or "General Inquiry"}
    
    Extract:
    1. Atomic Facts: Key data points (prices, names, dates, rules).
    2. Workflows: Step-by-step processes or "how-to" sequences.
    3. Entities: Names of products, people, or organizations.
    4. Relationships: Connections between entities.
    
    Return ONLY a JSON object:
    {{
        "facts": [],
        "workflows": [],
        "entities": [],
        "relationships": []
    }}
    
    CONTEXT:
    {context_text}
    """
    
    try:
        raw = await ollama_client.generate(prompt, model=settings.ollama_model)
        # Basic JSON extraction
        import re
        match = re.search(r"(\{.*\})", raw, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            return ContextSnapshot(
                facts=data.get("facts", []),
                workflows=data.get("workflows", []),
                entities=data.get("entities", []),
                relationships=data.get("relationships", [])
            )
    except Exception as e:
        logger.warning(f"[CONTEXT] Synthesis failed: {e}")
        
    return ContextSnapshot([], [], [], [])
