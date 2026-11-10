"""Groq LLM Provider implementation."""

from typing import Optional
from groq import AsyncGroq
from app.core.config import settings
from app.core.logging import logger
from app.ai.llm_provider import BaseLLMProvider


class GroqProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.client = AsyncGroq(api_key=self.api_key) if self.api_key else None

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Optional[str]:
        if not self.client:
            logger.warning("Groq API key not configured.")
            return None

        # Clean model name in case of tab/whitespace
        model_name = self.model.strip() if self.model else "qwen/qwen3.8-27b"
        
        try:
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=1500,
                timeout=20.0,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error ({model_name}): {e}")
            # Try versatile fallback model if specific model failed
            if "model" in str(e).lower() or "not found" in str(e).lower():
                try:
                    logger.info("Attempting fallback Groq model llama-3.3-70b-versatile...")
                    fallback_resp = await self.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=temperature,
                        max_tokens=1500,
                        timeout=20.0,
                    )
                    return fallback_resp.choices[0].message.content
                except Exception as fe:
                    logger.error(f"Groq fallback model error: {fe}")
            return None

