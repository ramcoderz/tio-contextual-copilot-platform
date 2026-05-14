import json
import httpx
import logging
import asyncio
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class OllamaClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.ollama_base_url

    async def generate(self, prompt: str, model: str = "llama3") -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 4096
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"[OLLAMA] Error generating: {e}")
            return f"Error: {str(e)}"

    async def generate_stream(self, prompt: str, model: str = "llama3"):
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.3,
                "num_ctx": 4096
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    async for line in response.aiter_lines():
                        if not line: continue
                        data = json.loads(line)
                        yield data.get("response", "")
                        if data.get("done"): break
        except Exception as e:
            logger.error(f"[OLLAMA] Stream error: {e}")
            yield f"Error: {str(e)}"

ollama_client = OllamaClient()
