"""FastAPI routes for the Intelligent Hybrid Router.

Endpoints:
- POST /api/router/analyze  – Analyse a prompt and return the execution plan (no execution)
- POST /api/router/execute  – Analyse, plan, execute, and synthesise a full answer
- GET  /api/router/status   – Router health and configuration status
"""

from typing import Optional
from fastapi import APIRouter, Depends
from app.core.logging import logger
from app.core.config import settings
from app.routes.auth import get_current_user_optional, CurrentUser
from app.router.schemas import (
    RouterAnalyzeRequest,
    RouterAnalyzeResponse,
    RouterExecuteRequest,
    RouterExecuteResponse,
    ToolSelectionMode,
)
from app.router.intent_classifier import IntentClassifier
from app.router.decision_engine import DecisionEngine
from app.router.execution_engine import ExecutionEngine
from app.router.response_synthesizer import ResponseSynthesizer
from app.router.mcp_manager import mcp_manager

router = APIRouter(prefix="/router", tags=["Intelligent Router"])


@router.post("/analyze", response_model=RouterAnalyzeResponse)
async def analyze_prompt(req: RouterAnalyzeRequest) -> RouterAnalyzeResponse:
    """Analyse a user prompt and return the structured analysis + execution plan.

    Does NOT execute any tools – useful for debugging, UI previews, and testing.
    """
    logger.info(f"Router /analyze: prompt='{req.prompt[:80]}...' mode={req.tool_mode}")

    # 1. Intent classification
    analysis = await IntentClassifier.analyse(req.prompt, req.language or "en")

    # 2. Decision engine
    mode = _parse_mode(req.tool_mode)
    plan = DecisionEngine.plan(
        analysis=analysis,
        mode=mode,
        manual_tools=req.selected_tools,
        manual_tool_args=req.tool_args,
    )

    return RouterAnalyzeResponse(analysis=analysis, plan=plan)


@router.post("/execute", response_model=RouterExecuteResponse)
async def execute_prompt(
    req: RouterExecuteRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional),
) -> RouterExecuteResponse:
    """Full pipeline: Analyse → Plan → Execute → Synthesise.

    Returns the final answer along with detailed execution metadata.
    """
    user_id = current_user.sub if current_user else "default_user"
    logger.info(f"Router /execute: user={user_id} prompt='{req.prompt[:80]}...' mode={req.tool_mode}")

    # 1. Intent classification
    analysis = await IntentClassifier.analyse(req.prompt, req.language or "en")

    # 2. Decision engine
    mode = _parse_mode(req.tool_mode)
    plan = DecisionEngine.plan(
        analysis=analysis,
        mode=mode,
        manual_tools=req.selected_tools,
        manual_tool_args=req.tool_args,
    )
    if hasattr(plan, "user_id"):
        plan.user_id = user_id

    # 3. Execution engine
    exec_result = await ExecutionEngine.execute(plan)

    # 4. Response synthesis
    answer = await ResponseSynthesizer.synthesise(
        analysis=analysis,
        steps=exec_result.steps,
        execution_mode=plan.execution_mode,
    )

    return RouterExecuteResponse(
        answer=answer,
        language=analysis.language,
        analysis=analysis,
        execution_mode=plan.execution_mode.value,
        executed_tools=exec_result.steps,
        tool_count=len(exec_result.steps),
        total_duration_ms=exec_result.total_duration_ms,
        metadata={
            "intent_domain": analysis.intent_domain.value,
            "complexity": analysis.complexity.value,
            "risk_level": analysis.risk_level.value,
            "classifier_confidence": analysis.confidence,
            "mcp_enabled": mcp_manager.is_enabled,
            "mcp_tools": mcp_manager.tool_count,
        },
    )


@router.get("/status")
async def router_status():
    """Return router health, configuration, and capability summary."""
    from app.tools.registry import tool_registry

    return {
        "status": "operational",
        "max_steps": settings.ROUTER_MAX_STEPS,
        "tool_timeout_seconds": settings.ROUTER_TOOL_TIMEOUT,
        "mcp_enabled": mcp_manager.is_enabled,
        "mcp_tools_discovered": mcp_manager.tool_count,
        "registered_tools": tool_registry.list_available_names(),
        "tool_count": len(tool_registry.list_available_names()),
    }


def _parse_mode(mode_str: str | None) -> ToolSelectionMode:
    """Safely parse tool selection mode from string."""
    try:
        return ToolSelectionMode((mode_str or "auto").lower())
    except ValueError:
        return ToolSelectionMode.AUTO
