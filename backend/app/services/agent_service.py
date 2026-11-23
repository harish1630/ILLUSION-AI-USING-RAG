"""Agent Service coordinating intelligent hybrid routing, tool execution, and response synthesis.

Upgraded to use the new Intelligent Router pipeline:
  IntentClassifier → DecisionEngine → ExecutionEngine → ResponseSynthesizer
while maintaining full backward compatibility with existing chat endpoints.
"""

import asyncio
from typing import List, Dict, Any, Optional
from app.core.logging import logger
from app.tools.registry import tool_registry
from app.tools.base import ToolResult
from app.router.schemas import ToolSelectionMode, ExecutionStep
from app.router.intent_classifier import IntentClassifier
from app.router.decision_engine import DecisionEngine
from app.router.execution_engine import ExecutionEngine
from app.router.response_synthesizer import ResponseSynthesizer
from app.router.langgraph_router import langgraph_router


class AgentExecutionResult:
    """Encapsulates the final answer, executed tools, and tool outputs."""

    def __init__(
        self,
        answer: str,
        executed_tools: List[ToolResult],
        planned_tools: List[Any],
        mode_used: ToolSelectionMode,
        active_router: Optional[str] = "chat",
        requires_auth: bool = False,
        missing_auth_provider: Optional[str] = None,
        workflow_steps: Optional[List[Dict[str, Any]]] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ):
        self.answer = answer
        self.executed_tools = executed_tools
        self.planned_tools = planned_tools
        self.mode_used = mode_used
        self.active_router = active_router
        self.requires_auth = requires_auth
        self.missing_auth_provider = missing_auth_provider
        self.workflow_steps = workflow_steps or []
        self.sources = sources or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "mode": self.mode_used.value,
            "active_router": self.active_router,
            "requires_auth": self.requires_auth,
            "missing_auth_provider": self.missing_auth_provider,
            "workflow_steps": self.workflow_steps,
            "sources": self.sources,
            "executed_tools": [
                {
                    "name": t.tool_name,
                    "success": t.success,
                    "data": t.data,
                    "error": t.error,
                }
                for t in self.executed_tools
            ],
            "tool_count": len(self.executed_tools),
        }


class AgentService:
    """
    Executes AI agent workflows using the Intelligent Hybrid Router:
      1. IntentClassifier – analyses prompt
      2. DecisionEngine – plans tool calls
      3. ExecutionEngine – runs tools with timeouts
      4. ResponseSynthesizer – merges results into answer

    Maintains full backward compatibility with the existing chat endpoint.
    """

    @classmethod
    async def run_agent(
        cls,
        user_prompt: str,
        mode: ToolSelectionMode = ToolSelectionMode.AUTO,
        selected_tools: Optional[List[str]] = None,
        tool_args: Optional[Dict[str, Dict[str, Any]]] = None,
        language: str = "en",
        uploaded_file_data: Optional[Dict[str, Any]] = None,
        user_id: str = "guest_user",
        session_id: str = "default_session",
    ) -> AgentExecutionResult:
        """
        Coordinates AI workflows through the 6-branch LangGraph state machine.
        Falls back smoothly to manual or sequential planning if explicit manual tools are supplied.
        """
        logger.info(f"AgentService.run_agent: mode={mode.value}, language={language}, user_id={user_id}")

        # Inject uploaded file data if provided
        if uploaded_file_data:
            selected_tools = selected_tools or []
            if "file_reader" not in selected_tools:
                selected_tools.append("file_reader")
            tool_args = tool_args or {}
            tool_args["file_reader"] = uploaded_file_data

        # 1. AUTO mode: Execute via LangGraph 6-Branch Intelligent Router
        if mode == ToolSelectionMode.AUTO and not selected_tools:
            try:
                lg_result = await langgraph_router.run(
                    prompt=user_prompt,
                    user_id=user_id,
                    session_id=session_id,
                    language=language,
                )

                # Convert executed tools to ToolResult format
                tool_results = []
                for t in lg_result.get("executed_tools", []):
                    tool_results.append(
                        ToolResult(
                            tool_name=t.get("name", "unknown"),
                            success=t.get("success", True),
                            data=t.get("data"),
                            error=t.get("error"),
                        )
                    )

                return AgentExecutionResult(
                    answer=lg_result.get("answer", ""),
                    executed_tools=tool_results,
                    planned_tools=lg_result.get("planned_tools", []),
                    mode_used=mode,
                    active_router=lg_result.get("selected_router", "chat"),
                    requires_auth=lg_result.get("requires_auth", False),
                    missing_auth_provider=lg_result.get("missing_auth_provider"),
                    workflow_steps=lg_result.get("workflow_steps", []),
                    sources=lg_result.get("sources", []),
                )
            except Exception as e:
                logger.error(f"LangGraph router encountered error: {e}, falling back to legacy pipeline", exc_info=True)

        # 2. Manual / Hybrid / Fallback Pipeline
        analysis = await IntentClassifier.analyse(user_prompt, language)
        plan = DecisionEngine.plan(
            analysis=analysis,
            mode=mode,
            manual_tools=selected_tools,
            manual_tool_args=tool_args,
        )
        exec_result = await ExecutionEngine.execute(plan)
        answer = await ResponseSynthesizer.synthesise(
            analysis=analysis,
            steps=exec_result.steps,
            execution_mode=plan.execution_mode,
        )
        tool_results = ExecutionEngine.steps_to_tool_results(exec_result.steps)

        return AgentExecutionResult(
            answer=answer,
            executed_tools=tool_results,
            planned_tools=plan.steps,
            mode_used=mode,
            active_router="tool" if selected_tools else "chat",
        )
