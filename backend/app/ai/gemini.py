"""Google Gemini LLM Provider implementation."""

from typing import Optional
import google.generativeai as genai
from app.core.config import settings
from app.core.logging import logger
from app.ai.llm_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.model_name = settings.GOOGLE_MODEL.strip() if settings.GOOGLE_MODEL else "gemini-1.5-flash"
        if self.api_key:
            genai.configure(api_key=self.api_key)

    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Optional[str]:
        if not self.api_key:
            logger.warning("Google API key not configured.")
            return None

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt,
                generation_config={"temperature": temperature, "max_output_tokens": 1500},
            )
            response = await model.generate_content_async(user_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Google Gemini API error ({self.model_name}): {e}")
            # Try fallback model
            try:
                fallback_model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_prompt,
                )
                fb_resp = await fallback_model.generate_content_async(user_prompt)
                return fb_resp.text
            except Exception as fe:
                logger.error(f"Gemini fallback error: {fe}")
            return None

