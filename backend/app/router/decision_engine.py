"""Deterministic Decision Engine combining LLM analysis with rule-based tool planning.

Takes a PromptAnalysis and produces an ExecutionPlan with:
- Which tools to invoke
- Their arguments
- Execution order and dependencies
- Whether user approval is required
"""

from typing import List, Dict, Any, Optional
from app.core.logging import logger
from app.core.config import settings
from app.tools.registry import tool_registry
from app.router.schemas import (
    PromptAnalysis,
    RoutingDecision,
    ExecutionPlan,
    ExecutionMode,
    ComplexityLevel,
    RiskLevel,
    IntentDomain,
    ToolSelectionMode,
)


class DecisionEngine:
    """Builds an execution plan from a PromptAnalysis.

    Combines:
    1. LLM-suggested tools from the analysis
    2. Deterministic rule overrides (domain → tool mapping)
    3. Tool availability validation
    4. Argument inference
    5. Dependency and ordering logic
    """

    @classmethod
    def plan(
        cls,
        analysis: PromptAnalysis,
        mode: ToolSelectionMode = ToolSelectionMode.AUTO,
        manual_tools: Optional[List[str]] = None,
        manual_tool_args: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> ExecutionPlan:
        """Produce a complete ExecutionPlan from an analysis and user preferences."""
        manual_tools = manual_tools or []
        manual_tool_args = manual_tool_args or {}

        steps: List[RoutingDecision] = []
        seen: set[str] = set()

        # -----------------------------------------------------------
        # 1. Manual mode: only user-specified tools
        # -----------------------------------------------------------
        if mode == ToolSelectionMode.MANUAL:
            for t_name in manual_tools:
                if tool_registry.get(t_name) and t_name not in seen:
                    args = manual_tool_args.get(t_name) or cls._infer_args(t_name, analysis)
                    steps.append(RoutingDecision(
                        tool_name=t_name, arguments=args,
                        reason="Manual user selection", priority=len(steps),
                    ))
                    seen.add(t_name)
            return cls._build_plan(analysis, steps)

        # -----------------------------------------------------------
        # 2. Hybrid mode: manual tools first, then AI augments
        # -----------------------------------------------------------
        if mode == ToolSelectionMode.HYBRID:
            for t_name in manual_tools:
                if tool_registry.get(t_name) and t_name not in seen:
                    args = manual_tool_args.get(t_name) or cls._infer_args(t_name, analysis)
                    steps.append(RoutingDecision(
                        tool_name=t_name, arguments=args,
                        reason="Manual user selection (hybrid)", priority=len(steps),
                    ))
                    seen.add(t_name)

        # -----------------------------------------------------------
        # 3. Auto / Hybrid: add tools from analysis + rules
        # -----------------------------------------------------------

        # 3a. Domain-specific mandatory tools
        domain_tools = cls._domain_to_tools(analysis.intent_domain)
        for t_name in domain_tools:
            if t_name not in seen and tool_registry.get(t_name):
                steps.append(RoutingDecision(
                    tool_name=t_name,
                    arguments=cls._infer_args(t_name, analysis),
                    reason=f"Domain rule: {analysis.intent_domain.value} requires {t_name}",
                    priority=len(steps),
                ))
                seen.add(t_name)

        # 3b. Capability flags from analysis
        capability_map = {
            "requires_rag": "rag_search",
            "requires_web": "web_search",
            "requires_calculation": "calculator",
            "requires_file": "file_reader",
        }
        for flag, t_name in capability_map.items():
            if getattr(analysis, flag, False) and t_name not in seen and tool_registry.get(t_name):
                steps.append(RoutingDecision(
                    tool_name=t_name,
                    arguments=cls._infer_args(t_name, analysis),
                    reason=f"Analysis flag: {flag}",
                    priority=len(steps),
                ))
                seen.add(t_name)

        # 3c. LLM-suggested tools not yet included
        for t_name in analysis.suggested_tools:
            if t_name not in seen and tool_registry.get(t_name):
                steps.append(RoutingDecision(
                    tool_name=t_name,
                    arguments=cls._infer_args(t_name, analysis),
                    reason="LLM classifier suggestion",
                    priority=len(steps),
                ))
                seen.add(t_name)

        # -----------------------------------------------------------
        # 4. Cap maximum steps
        # -----------------------------------------------------------
        max_steps = settings.ROUTER_MAX_STEPS
        if len(steps) > max_steps:
            logger.warning(f"Execution plan has {len(steps)} steps, capping to {max_steps}.")
            steps = steps[:max_steps]

        return cls._build_plan(analysis, steps)

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------

    @classmethod
    def _build_plan(cls, analysis: PromptAnalysis, steps: List[RoutingDecision]) -> ExecutionPlan:
        """Determine execution mode and build the final plan."""
        if not steps:
            exec_mode = ExecutionMode.DIRECT_LLM
        elif len(steps) == 1:
            exec_mode = ExecutionMode.SINGLE_TOOL
        else:
            # Check dependencies – if none, use parallel
            has_deps = any(s.depends_on for s in steps)
            exec_mode = ExecutionMode.SEQUENTIAL if has_deps else ExecutionMode.PARALLEL

        requires_approval = analysis.risk_level == RiskLevel.HIGH

        return ExecutionPlan(
            analysis=analysis,
            execution_mode=exec_mode,
            steps=steps,
            requires_approval=requires_approval,
            fallback_strategy="direct_llm",
            metadata={
                "tool_count": len(steps),
                "domain": analysis.intent_domain.value,
                "complexity": analysis.complexity.value,
            },
        )

    @classmethod
    def _domain_to_tools(cls, domain: IntentDomain) -> List[str]:
        """Maps intent domains to mandatory tool names."""
        mapping: Dict[IntentDomain, List[str]] = {
            IntentDomain.GOVERNMENT_SCHEME: ["rag_search"],
            IntentDomain.FINANCIAL_CALCULATION: ["calculator"],
            IntentDomain.FILE_ANALYSIS: ["file_reader"],
            IntentDomain.WEB_LOOKUP: ["web_search"],
            IntentDomain.BUSINESS_STARTUP: ["rag_search"],
        }
        return mapping.get(domain, [])

    @classmethod
    def _infer_args(cls, tool_name: str, analysis: PromptAnalysis) -> Dict[str, Any]:
        """Infer sensible default arguments for a tool based on the analysis."""
        prompt = analysis.original_prompt
        if tool_name == "calculator":
            # Try to extract a math expression from the prompt
            expr = prompt
            for prefix in ["calculate", "what is", "compute", "evaluate"]:
                if prompt.lower().startswith(prefix):
                    expr = prompt[len(prefix):].strip(" ?:=")
                    break
            return {"expression": expr}
        elif tool_name == "web_search":
            return {"query": prompt, "max_results": 5}
        elif tool_name == "rag_search":
            return {"query": prompt, "limit": 4}
        elif tool_name == "file_reader":
            return {"file_name": "document.txt"}
        return {}
