from backend.llm.ollama_client import generate
from backend.config.settings import get_settings

settings = get_settings()

async def summarize_history(history: list) -> str:
    """Compresses conversation history into a semantic summary."""
    if not history: return ""
    
    formatted = "\n".join([f"{m['role']}: {m['content']}" for m in history])
    prompt = f"Summarize the key entities, goals, and results of this conversation so far:\n\n{formatted}"
    
    return await generate(prompt, model=settings.ollama_model)
