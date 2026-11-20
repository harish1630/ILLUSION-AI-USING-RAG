"""LLM-based Intent Classifier with deterministic heuristic fallback.

Analyses every user prompt to produce a structured PromptAnalysis with:
- Intent domain and summary
- Complexity and risk assessment
- Required capabilities (RAG, web, calculator, file, MCP)
- Suggested tools and keywords
"""

import json
import re
from typing import Optional
from app.core.logging import logger
from app.core.config import settings
from app.ai.provider_manager import provider_manager
from app.router.schemas import (
    PromptAnalysis,
    IntentDomain,
    ComplexityLevel,
    RiskLevel,
)


class IntentClassifier:
    """Analyses user prompts via LLM structured output with heuristic fallback."""

    CLASSIFIER_SYSTEM_PROMPT = """You are the Intent Analysis Engine for ILLUSION AI, a startup and government scheme advisor for Tamil Nadu / India.

Analyse the user prompt and return a JSON object with these exact keys:
{
  "intent_domain": one of ["government_scheme", "business_startup", "legal_regulatory", "financial_calculation", "general_knowledge", "file_analysis", "web_lookup", "greeting", "unknown"],
  "intent_summary": "one-line summary of what the user wants",
  "complexity": one of ["trivial", "low", "medium", "high", "critical"],
  "risk_level": one of ["safe", "low", "medium", "high"],
  "requires_rag": true/false (needs verified government scheme data),
  "requires_web": true/false (needs fresh online information),
  "requires_calculation": true/false (needs math evaluation),
  "requires_file": true/false (needs file reading),
  "requires_mcp": false,
  "requires_memory": true/false (needs conversation history),
  "suggested_tools": list of tool names from ["calculator", "web_search", "rag_search", "file_reader"],
  "keywords": list of key terms from the prompt,
  "confidence": float 0.0 to 1.0
}

Rules:
- For scheme queries (NEEDS, UYEGP, PMEGP, Udyam, TANSEED, MUDRA, AABCS, subsidy, eligibility): set requires_rag=true and include "rag_search".
- For latest/current/news/2025/2026 queries: set requires_web=true and include "web_search".
- For math expressions, percentages, EMI, budget calculations: set requires_calculation=true and include "calculator".
- For simple greetings: set intent_domain="greeting", complexity="trivial", no tools.
- Multi-capability requests increase complexity to "medium" or "high".
- Never set risk_level="high" unless the prompt asks for data deletion or irreversible actions.

Return ONLY valid JSON without markdown code fences."""

    @classmethod
    async def analyse(cls, prompt: str, language: str = "en") -> PromptAnalysis:
        """Analyse the user prompt using LLM with heuristic fallback.

        Returns a fully populated PromptAnalysis regardless of LLM availability.
        """
        # Detect language
        detected_lang = cls._detect_language(prompt, language)

        # Try LLM-based classification first
        llm_analysis = await cls._llm_classify(prompt)
        if llm_analysis:
            llm_analysis.original_prompt = prompt
            llm_analysis.language = detected_lang
            return llm_analysis

        # Deterministic heuristic fallback
        logger.info("Intent classifier falling back to heuristic analysis.")
        return cls._heuristic_classify(prompt, detected_lang)

    @classmethod
    async def _llm_classify(cls, prompt: str) -> Optional[PromptAnalysis]:
        """Uses Groq/Gemini to produce structured intent analysis."""
        try:
            raw = await provider_manager.generate_response(
                cls.CLASSIFIER_SYSTEM_PROMPT, prompt
            )
            if not raw:
                return None

            cleaned = raw.strip()
            # Strip markdown code fences if present
            if "```" in cleaned:
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()

            parsed = json.loads(cleaned)

            return PromptAnalysis(
                original_prompt=prompt,
                intent_domain=IntentDomain(parsed.get("intent_domain", "unknown")),
                intent_summary=parsed.get("intent_summary", ""),
                complexity=ComplexityLevel(parsed.get("complexity", "low")),
                risk_level=RiskLevel(parsed.get("risk_level", "safe")),
                requires_rag=bool(parsed.get("requires_rag", False)),
                requires_web=bool(parsed.get("requires_web", False)),
                requires_calculation=bool(parsed.get("requires_calculation", False)),
                requires_file=bool(parsed.get("requires_file", False)),
                requires_mcp=bool(parsed.get("requires_mcp", False)),
                requires_memory=bool(parsed.get("requires_memory", False)),
                suggested_tools=parsed.get("suggested_tools", []),
                keywords=parsed.get("keywords", []),
                confidence=float(parsed.get("confidence", 0.8)),
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"LLM intent classification returned invalid structure: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM intent classification error: {e}")
            return None

    @classmethod
    def _heuristic_classify(cls, prompt: str, language: str) -> PromptAnalysis:
        """Fast deterministic classification when LLM is unavailable."""
        p = prompt.lower().strip()
        keywords = [w for w in p.split() if len(w) > 2]

        domain = IntentDomain.UNKNOWN
        complexity = ComplexityLevel.LOW
        risk = RiskLevel.SAFE
        needs_rag = False
        needs_web = False
        needs_calc = False
        needs_file = False
        suggested: list[str] = []
        summary = "General user request"

        # --- Greeting detection ---
        greeting_patterns = ["hello", "hi", "hey", "vanakkam", "வணக்கம்", "good morning", "good evening"]
        if any(p.startswith(g) or p == g for g in greeting_patterns):
            domain = IntentDomain.GREETING
            complexity = ComplexityLevel.TRIVIAL
            summary = "User greeting"
            return PromptAnalysis(
                original_prompt=prompt, language=language,
                intent_domain=domain, intent_summary=summary,
                complexity=complexity, risk_level=risk,
                keywords=keywords, confidence=0.95,
            )

        # --- Scheme / subsidy / eligibility ---
        scheme_terms = [
            "scheme", "subsidy", "needs", "uyegp", "pmegp", "udyam", "tanseed",
            "mudra", "aabcs", "eligibility", "msme", "grant", "government",
            "மானியம்", "உத்யாம்", "திட்டம்", "தகுதி",
        ]
        if any(t in p for t in scheme_terms):
            domain = IntentDomain.GOVERNMENT_SCHEME
            needs_rag = True
            suggested.append("rag_search")
            summary = "Government scheme or subsidy inquiry"

        # --- Web / latest / current ---
        web_terms = ["latest", "news", "recent", "current", "website", "online", "update", "2025", "2026"]
        if any(t in p for t in web_terms):
            needs_web = True
            suggested.append("web_search")
            if domain == IntentDomain.UNKNOWN:
                domain = IntentDomain.WEB_LOOKUP
            summary = summary if domain != IntentDomain.WEB_LOOKUP else "Real-time information lookup"

        # --- Calculation ---
        math_ops = ["+", "-", "*", "/", "%", "^", "calculate", "subsidy for", "percentage", "emi", "budget of"]
        has_digits = any(c.isdigit() for c in prompt)
        if has_digits and any(op in p for op in math_ops):
            needs_calc = True
            suggested.append("calculator")
            if domain == IntentDomain.UNKNOWN:
                domain = IntentDomain.FINANCIAL_CALCULATION
            summary = "Mathematical or financial calculation"

        # --- File ---
        file_terms = ["file", "pdf", "document", "docx", "upload", "extract"]
        if any(t in p for t in file_terms):
            needs_file = True
            suggested.append("file_reader")
            if domain == IntentDomain.UNKNOWN:
                domain = IntentDomain.FILE_ANALYSIS
            summary = "File reading or document analysis"

        # --- Business startup ---
        biz_terms = ["startup", "business", "entrepreneur", "company", "incorporate", "register", "gst", "license"]
        if any(t in p for t in biz_terms):
            if domain == IntentDomain.UNKNOWN:
                domain = IntentDomain.BUSINESS_STARTUP
                summary = "Business startup guidance"

        # --- Complexity ---
        tool_count = len(suggested)
        if tool_count == 0:
            complexity = ComplexityLevel.LOW
        elif tool_count == 1:
            complexity = ComplexityLevel.LOW
        elif tool_count == 2:
            complexity = ComplexityLevel.MEDIUM
        else:
            complexity = ComplexityLevel.HIGH

        confidence = 0.7 if suggested else 0.5

        return PromptAnalysis(
            original_prompt=prompt, language=language,
            intent_domain=domain, intent_summary=summary,
            complexity=complexity, risk_level=risk,
            requires_rag=needs_rag, requires_web=needs_web,
            requires_calculation=needs_calc, requires_file=needs_file,
            requires_mcp=False, requires_memory=False,
            suggested_tools=suggested, keywords=keywords,
            confidence=confidence,
        )

    @staticmethod
    def _detect_language(text: str, default: str = "en") -> str:
        """Detects Tamil if Unicode block U+0B80-U+0BFF is present."""
        if re.search(r"[\u0B80-\u0BFF]", text):
            return "ta"
        return default or "en"
