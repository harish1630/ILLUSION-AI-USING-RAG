"""Hybrid Tool Selection and Routing: Automatic, Manual, and Hybrid Modes."""

import json
import re
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from app.core.logging import logger
from app.tools.registry import tool_registry
from app.ai.provider_manager import provider_manager


class ToolSelectionMode(str, Enum):
    AUTO = "auto"        # AI selects tools automatically based on prompt
    MANUAL = "manual"    # User explicitly selects tools
    HYBRID = "hybrid"    # User specifies tools, AI can add complementary tools


class PlannedToolCall(BaseModel):
    """Represents a planned tool call with arguments."""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None


class ToolRouter:
    """
    Orchestrates selection of tools across Automatic, Manual, and Hybrid modes.
    Uses Groq LLM (with heuristic fallbacks) to select tools and map parameters safely.
    """

    TOOL_SELECTION_SYSTEM_PROMPT = """You are the Tool Routing Dispatcher for ILLUSION AI.
Your role is to analyze a user request and determine which available tools should be invoked, along with their parameters.

Routing Guidelines:
- For email requests (searching inbox, reading emails, creating drafts, sending messages), select the corresponding gmail_* tool (e.g. gmail_search_emails, gmail_create_draft, gmail_send_email).
- For creating issues, filing bugs, or reporting tickets, select github_create_issue.
- For listing or viewing issue tickets, select github_list_issues.
- For listing repositories, code search, reading files, commits, branches, select github_list_repositories, github_get_file_content, github_get_repository, etc.
- For subsidies, policies, and schemes in Tamil Nadu & Central India, select rag_search.
- For real-time web info, live portal updates, or external websites, select web_search.
- For arithmetic, interest rates, investment ratios, and caps, select calculator.

Available tools:
{tool_specs}

Respond ONLY with a JSON object in this format:
{
  "selected_tools": [
    {
      "tool_name": "tool_name_here",
      "arguments": {"param1": "value1"},
      "reason": "Brief explanation why this tool is needed"
    }
  ]
}

If no tools are needed, return: {"selected_tools": []}.
Do not include markdown code block formatting around your JSON if possible.
"""

    @classmethod
    async def route(
        cls,
        prompt: str,
        mode: ToolSelectionMode = ToolSelectionMode.AUTO,
        manual_tools: Optional[List[str]] = None,
        manual_tool_args: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[PlannedToolCall]:
        """
        Routes and determines the complete list of tools to invoke based on mode.
        """
        manual_tools = manual_tools or []
        manual_tool_args = manual_tool_args or {}
        planned: List[PlannedToolCall] = []
        selected_names: Set[str] = set()

        # 1. Manual Mode: Execute only user-specified tools
        if mode == ToolSelectionMode.MANUAL:
            for t_name in manual_tools:
                tool = tool_registry.get(t_name)
                if tool:
                    args = manual_tool_args.get(t_name) or cls._infer_fallback_args(t_name, prompt)
                    planned.append(PlannedToolCall(tool_name=t_name, arguments=args, reason="Manual user selection"))
                    selected_names.add(t_name)
            return planned

        # 2. Hybrid Mode: Include user-specified tools first, then ask AI for additional tools
        if mode == ToolSelectionMode.HYBRID:
            for t_name in manual_tools:
                tool = tool_registry.get(t_name)
                if tool:
                    args = manual_tool_args.get(t_name) or cls._infer_fallback_args(t_name, prompt)
                    planned.append(PlannedToolCall(tool_name=t_name, arguments=args, reason="Manual user selection"))
                    selected_names.add(t_name)

        # 3. Automatic & Hybrid Mode: AI determines tools needed
        ai_planned = await cls._ai_select_tools(prompt)
        for item in ai_planned:
            if item.tool_name not in selected_names and tool_registry.get(item.tool_name):
                planned.append(item)
                selected_names.add(item.tool_name)

        # Heuristic check: augment if AI was offline or missed specific high-intent actions
        heuristic_planned = cls._heuristic_select_tools(prompt)
        for item in heuristic_planned:
            if item.tool_name not in selected_names:
                if not ai_planned or any(k in item.tool_name for k in ["create_issue", "send_email", "create_draft"]):
                    planned.append(item)
                    selected_names.add(item.tool_name)

        return planned

    @classmethod
    async def _ai_select_tools(cls, prompt: str) -> List[PlannedToolCall]:
        """Uses LLM to select appropriate tools and arguments."""
        llm_defs = tool_registry.get_definitions_for_llm()
        spec_text = json.dumps(llm_defs, indent=2)
        system_prompt = cls.TOOL_SELECTION_SYSTEM_PROMPT.replace("{tool_specs}", spec_text)

        try:
            raw_response = await provider_manager.generate_response(system_prompt, prompt)
            if not raw_response:
                return []

            # Extract json if wrapped in ```json ... ```
            cleaned = raw_response.strip()
            if "```" in cleaned:
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()

            parsed = json.loads(cleaned)
            selected = parsed.get("selected_tools", [])
            calls = []
            for item in selected:
                name = item.get("tool_name")
                if name and tool_registry.get(name):
                    calls.append(PlannedToolCall(
                        tool_name=name,
                        arguments=item.get("arguments", {}),
                        reason=item.get("reason", "Selected by AI model"),
                    ))
            return calls
        except Exception as e:
            logger.warning(f"AI tool routing failed or returned invalid JSON: {e}")
            return []

    @classmethod
    def _heuristic_select_tools(cls, prompt: str) -> List[PlannedToolCall]:
        """Deterministic heuristic fallback when LLM selection is offline or inconclusive."""
        p_lower = prompt.lower()
        selected = []

        # Check for calculator triggers: mathematical expressions or arithmetic words
        math_symbols = ["+", "-", "*", "/", "%", "^", "calculate", "subsidy for", "percentage", "emi", "budget of"]
        has_numbers = any(char.isdigit() for char in prompt)
        if has_numbers and any(sym in p_lower for sym in math_symbols):
            # Extract expression if basic
            expr = prompt
            for prefix in ["calculate", "what is", "compute", "evaluate"]:
                if p_lower.startswith(prefix):
                    expr = prompt[len(prefix):].strip(" ?:=")
            selected.append(PlannedToolCall(
                tool_name="calculator",
                arguments={"expression": expr},
                reason="Heuristic detected arithmetic/calculation",
            ))

        # Check for Web Search triggers: current/online queries, latest news, recent updates
        if any(term in p_lower for term in ["latest", "news", "recent", "current", "website", "online", "update", "2026", "2025"]):
            selected.append(PlannedToolCall(
                tool_name="web_search",
                arguments={"query": prompt, "max_results": 4},
                reason="Heuristic detected real-time or recent information request",
            ))

        # Check for RAG triggers: schemes, subsidies, eligibility, Tamil Nadu policies
        if any(term in p_lower for term in ["scheme", "subsidy", "needs", "uyegp", "pmegp", "udyam", "tanseed", "eligibility", "tamil nadu", "rules"]):
            selected.append(PlannedToolCall(
                tool_name="rag_search",
                arguments={"query": prompt, "limit": 4},
                reason="Heuristic detected government scheme/policy inquiry",
            ))

        # Check for Gmail triggers: search, read, send, draft
        if any(term in p_lower for term in ["search email", "find email", "check email", "check my inbox", "gmail search", "emails from", "unread email"]):
            selected.append(PlannedToolCall(
                tool_name="gmail_search_emails",
                arguments={"query": prompt, "max_results": 5},
                reason="Heuristic detected Gmail inbox search request",
            ))
        elif any(term in p_lower for term in ["send email", "send an email", "email to"]):
            selected.append(PlannedToolCall(
                tool_name="gmail_send_email",
                arguments={"to": "recipient@example.com", "subject": "Notification from Illusion AI", "body": prompt},
                reason="Heuristic detected Gmail message send intent",
            ))
        elif any(term in p_lower for term in ["draft email", "create a draft", "save email draft"]):
            selected.append(PlannedToolCall(
                tool_name="gmail_create_draft",
                arguments={"to": "recipient@example.com", "subject": "Draft", "body": prompt},
                reason="Heuristic detected Gmail draft creation intent",
            ))

        # Check for GitHub Issues triggers
        if any(term in p_lower for term in ["create issue", "file bug", "open issue", "report issue", "file an issue"]):
            selected.append(PlannedToolCall(
                tool_name="github_create_issue",
                arguments={"repo_name": "owner/repo", "title": prompt[:60], "body": prompt},
                reason="Heuristic detected GitHub issue creation intent",
            ))
        elif any(term in p_lower for term in ["list issue", "show issue", "view issue", "github issue"]):
            selected.append(PlannedToolCall(
                tool_name="github_list_issues",
                arguments={"repo_name": "owner/repo", "state": "open"},
                reason="Heuristic detected GitHub issue listing intent",
            ))
        elif any(term in p_lower for term in ["github repo", "my repositories", "list repos", "github profile"]):
            selected.append(PlannedToolCall(
                tool_name="github_list_repositories",
                arguments={"visibility": "all"},
                reason="Heuristic detected GitHub repository query",
            ))

        return selected

    @classmethod
    def _infer_fallback_args(cls, tool_name: str, prompt: str) -> Dict[str, Any]:
        """Provides default arguments for manual tools if user didn't specify them."""
        if tool_name == "calculator":
            return {"expression": prompt}
        elif tool_name == "web_search":
            return {"query": prompt, "max_results": 4}
        elif tool_name == "rag_search":
            return {"query": prompt, "limit": 4}
        elif tool_name == "file_reader":
            return {"file_name": "document.txt"}
        elif tool_name == "gmail_search_emails":
            return {"query": prompt, "max_results": 5}
        elif tool_name == "gmail_send_email":
            return {"to": "recipient@example.com", "subject": "Notice", "body": prompt}
        elif tool_name == "gmail_create_draft":
            return {"to": "recipient@example.com", "subject": "Draft", "body": prompt}
        elif tool_name == "github_list_issues":
            return {"repo_name": "owner/repo", "state": "open"}
        elif tool_name == "github_create_issue":
            return {"repo_name": "owner/repo", "title": prompt[:60], "body": prompt}
        return {}
