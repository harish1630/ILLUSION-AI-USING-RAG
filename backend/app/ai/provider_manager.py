"""LLM Provider Manager orchestrating Groq and Google Gemini with fallback."""

from typing import Optional
from app.core.logging import logger
from app.ai.groq import GroqProvider
from app.ai.gemini import GeminiProvider


class ProviderManager:
    def __init__(self):
        self.groq = GroqProvider()
        self.gemini = GeminiProvider()

    async def generate_response(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        # Try Groq first (high speed)
        if self.groq.api_key:
            logger.info("Attempting inference via Groq...")
            res = await self.groq.generate_text(system_prompt, user_prompt)
            if res:
                return res

        # Try Google Gemini
        if self.gemini.api_key:
            logger.info("Attempting inference via Google Gemini...")
            res = await self.gemini.generate_text(system_prompt, user_prompt)
            if res:
                return res

        logger.warning("No external LLM provider succeeded.")
        return None


provider_manager = ProviderManager()

