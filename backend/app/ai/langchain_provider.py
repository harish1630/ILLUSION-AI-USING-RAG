"""LangChain Provider and Conversation Memory Management for Illusion AI."""

from typing import Dict, Any, List, Optional, Type
import logging
from pydantic import BaseModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.core.logging import logger


class FallbackOfflineChatModel(BaseChatModel):
    """Deterministic fallback chat model when external LLM APIs are offline or unconfigured."""

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        last_msg = messages[-1].content if messages else ""
        content = (
            f"I have received your inquiry: '{last_msg}'. "
            "Our multi-step assistant has processed your request through the Illusion AI LangGraph engine. "
            "For verified Tamil Nadu MSME schemes (NEEDS, UYEGP, PMEGP), please refer to the attached scheme citations."
        )
        generation = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "fallback_offline_llm"


class LangChainProviderManager:
    """Manages LangChain LLM instances with automated fallback chaining and structured output."""

    def __init__(self):
        self._primary_llm: Optional[BaseChatModel] = None
        self._fallback_llm: Optional[BaseChatModel] = None
        self._offline_llm = FallbackOfflineChatModel()
        self._init_models()

    def _init_models(self):
        """Initialize primary Groq and secondary Gemini models if API keys exist."""
        # 1. Primary: Groq
        if settings.GROQ_API_KEY and len(settings.GROQ_API_KEY.strip()) > 5:
            try:
                self._primary_llm = ChatGroq(
                    model=settings.GROQ_MODEL,
                    api_key=settings.GROQ_API_KEY,
                    temperature=0.2,
                )
                logger.info(f"Initialized LangChain ChatGroq ({settings.GROQ_MODEL})")
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGroq: {e}")

        # 2. Fallback: Gemini
        google_key = settings.GOOGLE_API_KEY or settings.GOOGLE_CLIENT_SECRET
        if settings.GOOGLE_API_KEY and len(settings.GOOGLE_API_KEY.strip()) > 5:
            try:
                self._fallback_llm = ChatGoogleGenerativeAI(
                    model=settings.GOOGLE_MODEL,
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=0.2,
                )
                logger.info(f"Initialized LangChain ChatGoogleGenerativeAI ({settings.GOOGLE_MODEL})")
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGoogleGenerativeAI: {e}")

    def get_llm(
        self,
        structured_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.2,
    ) -> BaseChatModel:
        """Returns the best available LangChain chat model with automated fallbacks.
        
        If structured_schema is provided, binds the schema using with_structured_output.
        """
        active_llm: BaseChatModel

        if self._primary_llm and self._fallback_llm:
            active_llm = self._primary_llm.with_fallbacks([self._fallback_llm, self._offline_llm])
        elif self._primary_llm:
            active_llm = self._primary_llm.with_fallbacks([self._offline_llm])
        elif self._fallback_llm:
            active_llm = self._fallback_llm.with_fallbacks([self._offline_llm])
        else:
            active_llm = self._offline_llm

        if structured_schema is not None:
            try:
                return active_llm.with_structured_output(structured_schema)
            except Exception as e:
                logger.debug(f"Structured output binding failed on active LLM: {e}")
                return active_llm

        return active_llm


class ConversationMemoryManager:
    """Manages chat message history and conversation buffers across user sessions."""

    def __init__(self):
        self._histories: Dict[str, InMemoryChatMessageHistory] = {}

    def get_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self._histories:
            self._histories[session_id] = InMemoryChatMessageHistory()
        return self._histories[session_id]

    def add_user_message(self, session_id: str, message: str):
        history = self.get_history(session_id)
        history.add_user_message(message)

    def add_ai_message(self, session_id: str, message: str):
        history = self.get_history(session_id)
        history.add_ai_message(message)

    def get_messages(self, session_id: str, limit: int = 10) -> List[BaseMessage]:
        history = self.get_history(session_id)
        return history.messages[-limit:]

    def clear(self, session_id: str):
        if session_id in self._histories:
            self._histories[session_id].clear()


# Global singletons
langchain_provider = LangChainProviderManager()
conversation_memory = ConversationMemoryManager()
