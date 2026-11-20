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


class AgentExecutionResult:
    """Encapsulates the final answer, executed tools, and tool outputs."""

    def __init__(
        self,
        answer: str,
        executed_tools: List[ToolResult],
        planned_tools: List[Any],
        mode_used: ToolSelectionMode,
    ):
        self.answer = answer
        self.executed_tools = executed_tools
        self.planned_tools = planned_tools
        self.mode_used = mode_used

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "mode": self.mode_used.value,
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
    ) -> AgentExecutionResult:
        """
        Full intelligent routing pipeline:
        Analyse → Plan → Execute → Synthesise.
        """
        logger.info(f"AgentService.run_agent: mode={mode.value}, language={language}")

        # Inject uploaded file data if provided
        if uploaded_file_data:
            selected_tools = selected_tools or []
            if "file_reader" not in selected_tools:
                selected_tools.append("file_reader")
            tool_args = tool_args or {}
            tool_args["file_reader"] = uploaded_file_data

        # 1. Intent Classification
        analysis = await IntentClassifier.analyse(user_prompt, language)
        logger.info(
            f"IntentClassifier: domain={analysis.intent_domain.value}, "
            f"complexity={analysis.complexity.value}, "
            f"tools={analysis.suggested_tools}"
        )

        # 2. Decision Engine – build execution plan
        plan = DecisionEngine.plan(
            analysis=analysis,
            mode=mode,
            manual_tools=selected_tools,
            manual_tool_args=tool_args,
        )
        logger.info(
            f"DecisionEngine: mode={plan.execution_mode.value}, "
            f"steps={len(plan.steps)}, "
            f"approval_needed={plan.requires_approval}"
        )

        # 3. Execution Engine – run tools
        exec_result = await ExecutionEngine.execute(plan)
        logger.info(
            f"ExecutionEngine: {len(exec_result.steps)} tools executed in "
            f"{exec_result.total_duration_ms:.0f}ms, "
            f"all_succeeded={exec_result.all_succeeded}"
        )

        # 4. Response Synthesis
        answer = await ResponseSynthesizer.synthesise(
            analysis=analysis,
            steps=exec_result.steps,
            execution_mode=plan.execution_mode,
        )

        # Convert ExecutionSteps to ToolResults for backward compatibility
        tool_results = ExecutionEngine.steps_to_tool_results(exec_result.steps)

        return AgentExecutionResult(
            answer=answer,
            executed_tools=tool_results,
            planned_tools=plan.steps,
            mode_used=mode,
        )
