"""Async Execution Engine with parallel, sequential, and mixed execution support.

Executes the tool calls planned by the DecisionEngine with:
- Per-tool timeout enforcement
- Parallel execution for independent tools
- Sequential execution for dependent tools
- Error isolation (one tool failure doesn't crash others)
- Timing instrumentation
"""

import asyncio
import time
from typing import List, Dict, Any
from app.core.logging import logger
from app.core.config import settings
from app.tools.registry import tool_registry
from app.tools.base import ToolResult
from app.router.schemas import (
    ExecutionPlan,
    ExecutionMode,
    ExecutionStep,
    ExecutionResult,
    RoutingDecision,
)


class ExecutionEngine:
    """Executes an ExecutionPlan by invoking tools with proper concurrency control."""

    @classmethod
    async def execute(cls, plan: ExecutionPlan) -> ExecutionResult:
        """Execute all steps in the plan according to its execution mode.

        Returns an ExecutionResult with per-step timing and success flags.
        """
        if not plan.steps:
            return ExecutionResult(
                plan=plan, steps=[], all_succeeded=True, total_duration_ms=0.0,
            )

        overall_start = time.perf_counter()

        if plan.execution_mode == ExecutionMode.PARALLEL:
            completed_steps = await cls._run_parallel(plan.steps)
        elif plan.execution_mode == ExecutionMode.SEQUENTIAL:
            completed_steps = await cls._run_sequential(plan.steps)
        elif plan.execution_mode == ExecutionMode.SINGLE_TOOL:
            completed_steps = await cls._run_parallel(plan.steps)  # single = trivial parallel
        else:
            # MIXED / DIRECT_LLM – run whatever we have in parallel
            completed_steps = await cls._run_parallel(plan.steps)

        total_ms = (time.perf_counter() - overall_start) * 1000
        all_ok = all(s.success for s in completed_steps)

        return ExecutionResult(
            plan=plan,
            steps=completed_steps,
            all_succeeded=all_ok,
            total_duration_ms=round(total_ms, 2),
        )

    # ---------------------------------------------------------------
    # Parallel execution
    # ---------------------------------------------------------------

    @classmethod
    async def _run_parallel(cls, decisions: List[RoutingDecision]) -> List[ExecutionStep]:
        """Execute all tool calls concurrently."""
        tasks = [cls._execute_one(d) for d in decisions]
        return list(await asyncio.gather(*tasks))

    # ---------------------------------------------------------------
    # Sequential execution (respects depends_on ordering)
    # ---------------------------------------------------------------

    @classmethod
    async def _run_sequential(cls, decisions: List[RoutingDecision]) -> List[ExecutionStep]:
        """Execute tool calls one after another in priority order."""
        # Sort by priority (lower first)
        sorted_decisions = sorted(decisions, key=lambda d: d.priority)
        results: List[ExecutionStep] = []
        result_data_map: Dict[str, Any] = {}

        for decision in sorted_decisions:
            # If the tool depends on another, inject its output into arguments
            if decision.depends_on:
                for dep_name in decision.depends_on:
                    if dep_name in result_data_map:
                        decision.arguments[f"{dep_name}_output"] = result_data_map[dep_name]

            step = await cls._execute_one(decision)
            results.append(step)

            if step.success and step.result_data is not None:
                result_data_map[decision.tool_name] = step.result_data

        return results

    # ---------------------------------------------------------------
    # Single tool execution with timeout
    # ---------------------------------------------------------------

    @classmethod
    async def _execute_one(cls, decision: RoutingDecision) -> ExecutionStep:
        """Execute a single tool call with timeout and error boundary."""
        tool = tool_registry.get(decision.tool_name)
        if not tool:
            return ExecutionStep(
                tool_name=decision.tool_name,
                arguments=decision.arguments,
                success=False,
                error=f"Tool '{decision.tool_name}' is not registered.",
            )

        timeout = settings.ROUTER_TOOL_TIMEOUT
        start = time.perf_counter()

        try:
            result: ToolResult = await asyncio.wait_for(
                tool.execute(**decision.arguments), timeout=timeout
            )
            elapsed = (time.perf_counter() - start) * 1000

            return ExecutionStep(
                tool_name=decision.tool_name,
                arguments=decision.arguments,
                success=result.success,
                result_data=result.data,
                error=result.error,
                duration_ms=round(elapsed, 2),
            )

        except asyncio.TimeoutError:
            elapsed = (time.perf_counter() - start) * 1000
            logger.warning(f"Tool '{decision.tool_name}' timed out after {timeout}s.")
            return ExecutionStep(
                tool_name=decision.tool_name,
                arguments=decision.arguments,
                success=False,
                error=f"Tool timed out after {timeout} seconds.",
                duration_ms=round(elapsed, 2),
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"Tool '{decision.tool_name}' execution failed: {e}")
            return ExecutionStep(
                tool_name=decision.tool_name,
                arguments=decision.arguments,
                success=False,
                error=f"Execution error: {str(e)}",
                duration_ms=round(elapsed, 2),
            )

    # ---------------------------------------------------------------
    # Utility: convert ExecutionSteps to ToolResults for compatibility
    # ---------------------------------------------------------------

    @staticmethod
    def steps_to_tool_results(steps: List[ExecutionStep]) -> List[ToolResult]:
        """Convert ExecutionStep list to ToolResult list for backward compatibility."""
        return [
            ToolResult(
                tool_name=s.tool_name,
                success=s.success,
                data=s.result_data,
                error=s.error,
                metadata={"duration_ms": s.duration_ms},
            )
            for s in steps
        ]
