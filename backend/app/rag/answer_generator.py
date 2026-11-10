"""Bilingual Answer Generator using retrieved evidence and LLM inference."""

import re
from typing import List, Dict, Any, Optional
from app.core.constants import DISCLAIMER_EN, DISCLAIMER_TA, EligibilityStatus
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatSourceCitation
from app.db.repositories import DocumentChunkRepository, SchemeRepository
from app.ai.provider_manager import provider_manager
from app.rag.prompt_builder import build_rag_system_prompt, build_rag_user_prompt


def detect_language(text: str, default_lang: str = "en") -> str:
    """Detects if query contains Tamil Unicode characters (U+0B80 - U+0BFF)."""
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "ta"
    return default_lang or "en"


class AnswerGenerator:
    @staticmethod
    async def generate_answer(req: ChatMessageRequest) -> ChatMessageResponse:
        # Determine language: auto-detect Tamil characters or use requested
        lang = detect_language(req.question, default_lang=req.language or "en")
        is_tamil = lang == "ta"

        # 1. Retrieve evidence chunks
        evidence_chunks = DocumentChunkRepository.search(req.question, limit=4)

        # 2. Check if specific scheme matches query keywords
        q_lower = req.question.lower()
        matched_schemes = []
        for s in SchemeRepository.list_schemes():
            if (
                s["id"].split("-")[1] in q_lower
                or s["name"].lower().split("(")[0].strip() in q_lower
                or ("needs" in q_lower and "needs" in s["id"])
                or ("uyegp" in q_lower and "uyegp" in s["id"])
                or ("pmegp" in q_lower and "pmegp" in s["id"])
                or ("udyam" in q_lower and "udyam" in s["id"])
            ):
                matched_schemes.append(s)

        # 3. Build prompts
        system_prompt = build_rag_system_prompt(language=lang)
        user_prompt = build_rag_user_prompt(
            question=req.question,
            evidence_chunks=evidence_chunks,
            profile=req.profile,
            language=lang,
        )

        # 4. Attempt LLM generation
        llm_text = await provider_manager.generate_response(system_prompt, user_prompt)

        # 5. Format sources
        sources: List[ChatSourceCitation] = []
        for c in evidence_chunks:
            sources.append(
                ChatSourceCitation(
                    title=c.get("title", "Official Govt Portal"),
                    url=c.get("url", "https://msmeonline.tn.gov.in/"),
                    document_id=c.get("id"),
                    page=1,
                    last_verified_at=c.get("last_verified_at"),
                )
            )

        # 6. Fallback response if LLM was unavailable
        if not llm_text:
            if evidence_chunks:
                top = evidence_chunks[0]
                if is_tamil:
                    llm_text = (
                        f"உங்கள் கேள்விக்குரிய அரசு திட்ட விவரங்கள்:\n\n"
                        f"**{top.get('title')}**\n"
                        f"{top.get('content')}\n\n"
                        f"அதிகாரப்பூர்வ போர்ட்டல் மூலம் விண்ணப்பிக்கவும்: {top.get('url')}\n"
                        f"மேலும் விவரங்களுக்கு உங்கள் மாவட்ட தொழில் மையத்தை (DIC) அணுகவும்."
                    )
                else:
                    llm_text = (
                        f"Based on verified government records, here is the relevant scheme information:\n\n"
                        f"**{top.get('title')}**\n"
                        f"{top.get('content')}\n\n"
                        f"You can explore and apply on the official portal: {top.get('url')}\n"
                        f"We recommend consulting your local District Industries Centre (DIC) for procedural guidance."
                    )
            else:
                if is_tamil:
                    llm_text = (
                        "மன்னிக்கவும், தங்களின் கேள்விக்கான அதிகாரப்பூர்வ அரசு தகவல் தற்போது எங்கள் தரவுதளத்தில் கிடைக்கவில்லை. "
                        "தவறான தகவல்களை தவிர்க்க, நீங்கள் அதிகாரப்பூர்வ தமிழ்நாடு MSME போர்ட்டல் (msmeonline.tn.gov.in) "
                        "அல்லது உங்கள் மாவட்ட தொழில் மையத்தை (DIC) நேரடியாக அணுகுமாறு பரிந்துரைக்கிறோம்."
                    )
                else:
                    llm_text = (
                        "I cannot verify the answer for this specific query from currently available official records. "
                        "To prevent misinformation, please consult the official Tamil Nadu MSME portal (msmeonline.tn.gov.in) "
                        "or your District Industries Centre (DIC) directly."
                    )

        # 7. Follow-up questions
        follow_up = []
        if is_tamil:
            follow_up = [
                "இத்திட்டத்திற்கு தேவையான ஆவணங்கள் யாவை?",
                "உத்யாம் இலவச பதிவை எவ்வாறு மேற்கொள்வது?",
                "எனது தொழிலுக்கான வரைபடத்தை உருவாக்குவது எப்படி?",
            ]
        else:
            follow_up = [
                "What documents are required to apply for this scheme?",
                "How do I complete zero-cost Udyam registration?",
                "How do I generate an actionable launch roadmap for my business?",
            ]

        eligibility_status = (
            EligibilityStatus.POTENTIALLY_ELIGIBLE
            if matched_schemes
            else EligibilityStatus.INSUFFICIENT_INFORMATION
        )

        return ChatMessageResponse(
            answer=llm_text,
            language=lang,
            sources=sources,
            eligibility_status=eligibility_status,
            follow_up_questions=follow_up,
            matched_schemes=matched_schemes,
            disclaimer=DISCLAIMER_TA if is_tamil else DISCLAIMER_EN,
            conversation_id=req.conversation_id,
        )

