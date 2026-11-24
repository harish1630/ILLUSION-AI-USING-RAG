"""Bilingual RAG & Hybrid Tool Chat Assistant endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatExecutedTool, ChatSourceCitation
from app.rag.answer_generator import AnswerGenerator, detect_language
from app.services.agent_service import AgentService
from app.router.schemas import ToolSelectionMode
from app.core.constants import DISCLAIMER_EN, DISCLAIMER_TA
from app.routes.auth import get_current_user_optional, CurrentUser

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatMessageResponse)
async def chat_message(
    req: ChatMessageRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """
    Bilingual Chatbot powered by Hybrid Tool Calling.
    Supports:
    - 'auto': AI automatically selects necessary tools (Web Search, RAG Search, Calculator, File Reader).
    - 'manual': User explicitly selects tools to invoke.
    - 'hybrid': User specifies base tools and AI augments complementary tools.
    Falls back gracefully to authentic scheme knowledge.
    """
    mode_str = (req.tool_mode or "auto").lower()
    try:
        mode = ToolSelectionMode(mode_str)
    except ValueError:
        mode = ToolSelectionMode.AUTO

    # If manual or hybrid requested, or if auto mode is selected with tools/calc query
    # Execute through AgentService
    lang = detect_language(req.question, default_lang=req.language or "en")
    is_tamil = lang == "ta"

    resolved_user_id = current_user.sub if current_user else (req.user_id or "guest_user")

    agent_result = await AgentService.run_agent(
        user_prompt=req.question,
        mode=mode,
        selected_tools=req.selected_tools,
        tool_args=req.tool_args,
        language=lang,
        user_id=resolved_user_id,
        session_id=req.conversation_id or "default_session",
    )

    executed_tools_schema = []
    sources = []

    # Map sources from agent_result if present
    for src in getattr(agent_result, "sources", []):
        sources.append(
            ChatSourceCitation(
                title=src.get("title", "Verified Source"),
                url=src.get("url", "https://msmeonline.tn.gov.in/"),
                document_id=src.get("document_id"),
                section=src.get("section"),
            )
        )

    for tool_res in agent_result.executed_tools:
        executed_tools_schema.append(
            ChatExecutedTool(
                tool_name=tool_res.tool_name,
                success=tool_res.success,
                data=tool_res.data,
                error=tool_res.error,
            )
        )
        # Extract sources if web_search or rag_search was executed without prior sources
        if not sources:
            if tool_res.tool_name == "web_search" and tool_res.success and isinstance(tool_res.data, dict):
                for res_item in tool_res.data.get("results", []):
                    sources.append(
                        ChatSourceCitation(
                            title=res_item.get("title", "Web Source"),
                            url=res_item.get("url", ""),
                            document_id="web",
                        )
                    )
            elif tool_res.tool_name == "rag_search" and tool_res.success and isinstance(tool_res.data, dict):
                for chunk in tool_res.data.get("chunks", []):
                    sources.append(
                        ChatSourceCitation(
                            title=chunk.get("title", "Verified Government Scheme"),
                            url=chunk.get("url", "https://msmeonline.tn.gov.in/"),
                            document_id=chunk.get("id"),
                        )
                    )

    follow_ups = (
        [
            "இத்திட்டத்திற்கு தேவையான ஆவணங்கள் யாவை?",
            "உத்யாம் இலவச பதிவை எவ்வாறு மேற்கொள்வது?",
            "எனது முதலீட்டிற்குரிய மானியத்தை கணக்கிடவும்.",
        ]
        if is_tamil
        else [
            "What documents are required to apply for this scheme?",
            "How do I complete zero-cost Udyam registration?",
            "Can you calculate the subsidy amount for my budget?",
        ]
    )

    return ChatMessageResponse(
        answer=agent_result.answer,
        language=lang,
        sources=sources,
        eligibility_status="potentially_eligible" if sources else "insufficient_information",
        follow_up_questions=follow_ups,
        matched_schemes=[],
        disclaimer=DISCLAIMER_TA if is_tamil else DISCLAIMER_EN,
        conversation_id=req.conversation_id,
        executed_tools=executed_tools_schema,
        tool_mode_used=agent_result.mode_used.value,
        active_router=agent_result.active_router,
        requires_auth=agent_result.requires_auth,
        missing_auth_provider=agent_result.missing_auth_provider,
        workflow_steps=agent_result.workflow_steps,
    )


