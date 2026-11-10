"""Abstract LLM Provider interface."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Optional[str]:
        """Generates text from LLM provider."""
        pass

