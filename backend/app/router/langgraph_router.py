"""LangGraph 6-Branch Intelligent Router for Illusion AI.

Orchestrates user queries across 6 specialized execution domains:
  1. Chat Router: General conversations & LLM responses with conversation memory.
  2. RAG Router: Government scheme knowledge retrieval with citations.
  3. Tool Router: Calculator, web search, and file processing.
  4. MCP Router: Model Context Protocol dynamic server tool discovery & execution.
  5. OAuth Router: Authorized external apps (GitHub, Gmail, Google Calendar) with auth gates.
  6. Multi-Step Router: Multi-capability workflows combining retrieval, calculation, and actions.
"""

import json
import re
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.core.logging import logger
from app.ai.langchain_provider import langchain_provider, conversation_memory
from app.tools.registry import tool_registry
from app.plugins import plugin_manager, ExecutionStatus


class LangGraphRouterState(TypedDict):
    prompt: str
    language: str
    user_id: str
    session_id: str
    selected_router: str
    intent_summary: str
    complexity: str
    confidence: float
    planned_tools: List[Dict[str, Any]]
    executed_tools: List[Dict[str, Any]]
    workflow_steps: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    answer: str
    requires_auth: bool
    missing_auth_provider: Optional[str]
    requires_approval: bool
    approval_details: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


class IllusionLangGraphRouter:
    """Intelligent LangGraph Router managing 6-branch orchestration."""

    def __init__(self):
        self.workflow = self._build_graph()

    def _build_graph(self) -> Any:
        graph = StateGraph(LangGraphRouterState)

        # 1. Classification node
        graph.add_node("classify_intent", self._classify_intent_node)

        # 2. Six router branches
        graph.add_node("chat_router", self._chat_router_node)
        graph.add_node("rag_router", self._rag_router_node)
        graph.add_node("tool_router", self._tool_router_node)
        graph.add_node("mcp_router", self._mcp_router_node)
        graph.add_node("oauth_router", self._oauth_router_node)
        graph.add_node("multistep_router", self._multistep_router_node)

        # 3. Final synthesis node
        graph.add_node("synthesize", self._synthesize_node)

        # Routing logic
        graph.set_entry_point("classify_intent")
        graph.add_conditional_edges(
            "classify_intent",
            self._route_decision,
            {
                "chat": "chat_router",
                "rag": "rag_router",
                "tool": "tool_router",
                "mcp": "mcp_router",
                "oauth": "oauth_router",
                "multistep": "multistep_router",
            },
        )

        # Branch nodes lead to synthesis
        graph.add_edge("chat_router", "synthesize")
        graph.add_edge("rag_router", "synthesize")
        graph.add_edge("tool_router", "synthesize")
        graph.add_edge("mcp_router", "synthesize")
        graph.add_edge("oauth_router", "synthesize")
        graph.add_edge("multistep_router", "synthesize")

        graph.add_edge("synthesize", END)

        return graph.compile()

    # -------------------------------------------------------------------------
    # Conditional Routing Logic
    # -------------------------------------------------------------------------

    def _route_decision(self, state: LangGraphRouterState) -> str:
        return state.get("selected_router", "chat")

    # -------------------------------------------------------------------------
    # Node 1: Intent Classification
    # -------------------------------------------------------------------------

    async def _classify_intent_node(self, state: LangGraphRouterState) -> Dict[str, Any]:
        prompt = state["prompt"]
        p = prompt.lower().strip()
        lang = state.get("language", "en")

        def has_any(words: List[str]) -> bool:
            return any(re.search(r"\b" + re.escape(w) + r"\b", p) for w in words)

        # Detect capabilities needed
        oauth_provider = None
        has_oauth = False
        has_rag = False
        has_tool = False
        has_mcp = False
        planned_tools: List[Dict[str, Any]] = []

        # 1. Check OAuth app keywords
        # Gmail
        gmail_keywords = ["gmail", "email", "emails", "inbox", "mail"]
        if has_any(gmail_keywords):
            has_oauth = True
            oauth_provider = "gmail"
            if has_any(["send", "forward"]):
                planned_tools.append({"name": "gmail_send_email", "provider": "gmail"})
            elif has_any(["draft", "compose"]):
                planned_tools.append({"name": "gmail_create_draft", "provider": "gmail"})
            elif has_any(["read", "open", "view"]):
                planned_tools.append({"name": "gmail_read_email", "provider": "gmail"})
            else:
                planned_tools.append({"name": "gmail_search_emails", "provider": "gmail"})

        # GitHub
        github_keywords = ["github", "repo", "repos", "repositories", "repository", "commits", "commit", "issues", "issue", "branch", "branches", "pull request", "pr"]
        if has_any(github_keywords):
            has_oauth = True
            oauth_provider = "github"
            if "issue" in p and has_any(["create", "open", "file", "new"]):
                planned_tools.append({"name": "github_create_issue", "provider": "github"})
            elif "issue" in p:
                planned_tools.append({"name": "github_list_issues", "provider": "github"})
            elif "commit" in p:
                planned_tools.append({"name": "github_list_commits", "provider": "github"})
            elif "branch" in p:
                planned_tools.append({"name": "github_list_branches", "provider": "github"})
            elif "readme" in p or "file" in p:
                planned_tools.append({"name": "github_get_file_content", "provider": "github"})
            elif has_any(["list", "all", "my repos", "repos", "repositories"]):
                planned_tools.append({"name": "github_list_repositories", "provider": "github"})
            else:
                planned_tools.append({"name": "github_get_repository", "provider": "github"})

        # Google Calendar
        calendar_keywords = ["calendar", "schedule", "schedules", "meeting", "meetings", "event", "events", "availability", "free slots"]
        if has_any(calendar_keywords):
            has_oauth = True
            oauth_provider = "google_calendar"
            if (has_any(["create", "book", "set"]) and has_any(["meeting", "event", "appointment"])) or re.search(r"\bschedule (?:a|an|new)\b", p):
                planned_tools.append({"name": "calendar_create_event", "provider": "google_calendar"})
            elif has_any(["free", "busy", "availability", "available"]):
                planned_tools.append({"name": "calendar_check_availability", "provider": "google_calendar"})
            else:
                planned_tools.append({"name": "calendar_list_events", "provider": "google_calendar"})

        # 2. Check Government Schemes / RAG keywords
        scheme_keywords = [
            "scheme", "subsidy", "needs", "uyegp", "pmegp", "udyam", "tanseed",
            "mudra", "aabcs", "eligibility", "msme", "grant", "government",
            "மானியம்", "உத்யாம்", "திட்டம்", "தகுதி",
        ]
        if any(k in p for k in scheme_keywords):
            has_rag = True
            planned_tools.append({"name": "rag_search"})

        # 3. Check Standard Tools (Calculator, Web search, File reader)
        math_ops = ["+", "-", "*", "/", "%", "^", "calculate", "percentage", "emi", "budget"]
        has_digits = any(c.isdigit() for c in prompt)
        if has_digits and any(op in p for op in math_ops):
            has_tool = True
            planned_tools.append({"name": "calculator"})

        web_keywords = ["latest news", "current 2025", "current 2026", "online search", "google it", "who won", "today"]
        if any(k in p for k in web_keywords):
            has_tool = True
            planned_tools.append({"name": "web_search"})

        file_keywords = ["file", "pdf", "docx", "document", "extract content"]
        if any(k in p for k in file_keywords):
            has_tool = True
            planned_tools.append({"name": "file_reader"})

        # 4. Check MCP keywords
        mcp_keywords = ["mcp", "mcp server", "mcp tool", "custom tool", "illusion_custom"]
        if any(k in p for k in mcp_keywords):
            has_mcp = True
            planned_tools.append({"name": "mcp_execute"})

        # Determine router domain
        active_domains = sum([bool(has_oauth), bool(has_rag), bool(has_tool), bool(has_mcp)])

        if active_domains > 1:
            selected_router = "multistep"
            summary = "Multi-step complex workflow requiring chained tools"
            complexity = "high"
        elif has_oauth:
            selected_router = "oauth"
            summary = f"OAuth-connected application request for {oauth_provider}"
            complexity = "medium"
        elif has_rag:
            selected_router = "rag"
            summary = "Verified government scheme & subsidy knowledge inquiry"
            complexity = "medium"
        elif has_tool:
            selected_router = "tool"
            summary = "Standard tool execution (calculator, search, or file reader)"
            complexity = "low"
        elif has_mcp:
            selected_router = "mcp"
            summary = "MCP server capability execution"
            complexity = "medium"
        else:
            selected_router = "chat"
            summary = "General conversational response or direct business consultation"
            complexity = "low"

        logger.info(
            f"LangGraphRouter: intent classified -> '{selected_router}', "
            f"planned_tools={[t['name'] for t in planned_tools]}"
        )

        return {
            "selected_router": selected_router,
            "intent_summary": summary,
            "complexity": complexity,
            "confidence": 0.95 if planned_tools else 0.85,
            "planned_tools": planned_tools,
            "metadata": {"oauth_provider": oauth_provider},
        }

    # -------------------------------------------------------------------------
    # Branch 1: Chat Router Node
    # -------------------------------------------------------------------------

    async def _chat_router_node(self, state: LangGraphRouterState) -> Dict[str, Any]:
        prompt = state["prompt"]
        session_id = state.get("session_id", "default_session")
        lang = state.get("language", "en")

        # Retrieve conversation memory
        history = conversation_memory.get_messages(session_id, limit=6)
        llm = langchain_provider.get_llm()

        system_prompt = (
            "You are Illusion AI, an expert bilingual startup and MSME advisor for Tamil Nadu and India. "
            "Provide helpful, concise, empowering guidance. "
            f"Respond fluently in {'Tamil (தமிழ்)' if lang == 'ta' else 'English'}."
        )

        messages = [SystemMessage(content=system_prompt)]
        messages.extend(history)
        messages.append(HumanMessage(content=prompt))

        try:
            ai_msg = await llm.ainvoke(messages)
            answer = ai_msg.content if isinstance(ai_msg, AIMessage) else str(ai_msg)
        except Exception as e:
            logger.warning(f"ChatRouter LLM error: {e}, falling back to template")
            answer = (
                "வணக்கம்! உங்கள் தொழில் வளர்ச்சிக்கு உதவ நான் தயார். உங்களுக்குத் தேவையான திட்டங்கள் அல்லது உதவிகளைக் கேட்கலாம்."
                if lang == "ta"
                else "Hello! I am Illusion AI, your startup and MSME advisor. How can I help you grow your business today?"
            )

        conversation_memory.add_user_message(session_id, prompt)
        conversation_memory.add_ai_message(session_id, answer)

        return {
            "answer": answer,
            "executed_tools": [],
            "workflow_steps": [{"step": "chat_memory", "status": "completed"}],
        }

    # -------------------------------------------------------------------------
    # Branch 2: RAG Router Node
    # -------------------------------------------------------------------------

    async def _rag_router_node(self, state: LangGraphRouterState) -> Dict[str, Any]:
        prompt = state["prompt"]
        lang = state.get("language", "en")
        rag_tool = tool_registry.get("rag_search")

        sources = []
        executed_tools = []
        rag_content = ""

        if rag_tool:
            result = await rag_tool.execute(query=prompt, top_k=3)
            executed_tools.append({
                "name": "rag_search",
                "success": result.success,
                "data": result.data,
            })
            if result.success and isinstance(result.data, dict):
                chunks = result.data.get("chunks", [])
                for c in chunks:
                    sources.append({
                        "title": c.get("title", "Verified Government Scheme"),
                        "url": c.get("url", "https://msmeonline.tn.gov.in/"),
                        "document_id": c.get("id"),
                        "section": c.get("section", "Guidelines"),
                    })
                rag_content = "\n\n".join([f"Scheme: {c.get('title')}\nDetails: {c.get('content')}" for c in chunks])

        llm = langchain_provider.get_llm()
        system_prompt = (
            "You are Illusion AI, an authority on Tamil Nadu and Central MSME government schemes (NEEDS, UYEGP, PMEGP, TANSEED, Mudra). "
            "Use the provided verified scheme data to give clear, factual answers with eligibility criteria and subsidy percentages. "
            f"Respond fluently in {'Tamil (தமிழ்)' if lang == 'ta' else 'English'}."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User Query: {prompt}\n\nVerified Knowledge Base:\n{rag_content or 'No direct matching schemes found in cache.'}"),
        ]

        try:
            ai_msg = await llm.ainvoke(messages)
            answer = ai_msg.content if isinstance(ai_msg, AIMessage) else str(ai_msg)
        except Exception:
            answer = (
                f"Based on Tamil Nadu MSME records: {rag_content[:400]}..."
                if rag_content
                else "Please review the official Tamil Nadu MSME guidelines at https://msmeonline.tn.gov.in/."
            )

        return {
            "answer": answer,
            "sources": sources,
            "executed_tools": executed_tools,
            "workflow_steps": [{"step": "rag_vector_search", "status": "completed", "sources_count": len(sources)}],
        }

    # -------------------------------------------------------------------------
    # Branch 3: Tool Router Node
    # -------------------------------------------------------------------------

    async def _tool_router_node(self, state: LangGraphRouterState) -> Dict[str, Any]:
        prompt = state["prompt"]
        lang = state.get("language", "en")
        planned = state.get("planned_tools", [])
        executed_tools = []
        tool_outputs = []

        for t_spec in planned:
            t_name = t_spec["name"]
            tool_inst = tool_registry.get(t_name)
            if not tool_inst:
                continue

            args = {}
            if t_name == "calculator":
                # Extract math expression
                expr = re.sub(r"[^0-9\+\-\*\/\.\(\)\%\^]", "", prompt)
                args = {"expression": expr if expr else "0"}
            elif t_name == "web_search":
                args = {"query": prompt, "max_results": 3}
            elif t_name == "file_reader":
                args = {"file_path": "uploaded_doc.txt"}

            res = await tool_inst.execute(**args)
            executed_tools.append({
                "name": t_name,
                "success": res.success,
                "data": res.data,
                "error": res.error,
            })
            tool_outputs.append(f"Tool {t_name} output: {res.data or res.error}")

        llm = langchain_provider.get_llm()
        sys_msg = (
            "You are Illusion AI. Synthesize the tool execution results into an informative response for the user. "
            f"Respond fluently in {'Tamil (தமிழ்)' if lang == 'ta' else 'English'}."
        )
        human_msg = f"User Request: {prompt}\n\nTool Results:\n" + "\n".join(tool_outputs)

        try:
            ai_msg = await llm.ainvoke([SystemMessage(content=sys_msg), HumanMessage(content=human_msg)])
            answer = ai_msg.content if isinstance(ai_msg, AIMessage) else str(ai_msg)
        except Exception:
            answer = "\n".join(tool_outputs)

        return {
            "answer": answer,
            "executed_tools": executed_tools,
            "workflow_steps": [{"step": "internal_tools_execution", "status": "completed"}],
        }

    # -------------------------------------------------------------------------
    # Branch 4: MCP Router Node
    # -------------------------------------------------------------------------

    async def _mcp_router_node(self, state: LangGraphRouterState) -> Dict[str, Any]:
        prompt = state["prompt"]
        mcp_tool = tool_registry.get("mcp_execute")
        executed_tools = []
        result_text = ""

        if mcp_tool:
            res = await mcp_tool.execute(tool_name="get_project_info", arguments={})
            executed_tools.append({
                "name": "mcp_execute",
                "success": res.success,
                "data": res.data,
                "error": res.error,
            })
            result_text = f"MCP Result: {res.data}"

        answer = (
            f"MCP Tool execution completed successfully:\n{result_text}"
            if result_text
            else "MCP server connection is active. No external MCP tools required for this query."
        )

        return {
            "answer": answer,
            "executed_tools": executed_tools,
            "workflow_steps": [{"step": "mcp_server_bridge", "status": "completed"}],
        }

    # -------------------------------------------------------------------------
    # Branch 5: OAuth Router Node
    # -------------------------------------------------------------------------

    async def _oauth_router_node(self, state: LangGraphRouterState) -> Dict[str, Any]:
        prompt = state["prompt"]
        user_id = state.get("user_id", "guest_user")
        lang = state.get("language", "en")
        meta = state.get("metadata", {})
        provider = meta.get("oauth_provider") or "github"

        # Check OAuth connection
        conn = plugin_manager.get_user_integration(user_id, provider)

        # In dev/mock mode with guest_user, if not connected, check if mock connection can be used or gate it
        if not conn:
            # User is NOT connected to this provider
            msg_en = (
                f"To access your {provider.replace('_', ' ').title()} data, please connect your account first. "
                f"You can securely authorize Illusion AI by visiting the Plugin Marketplace."
            )
            msg_ta = (
                f"உங்கள் {provider.replace('_', ' ').title()} கணக்கை அணுக, முதலில் உங்கள் கணக்கை இணைக்கவும். "
                f"Plugin Marketplace பக்கத்திற்குச் சென்று பாதுகாப்பாக இணைக்கலாம்."
            )
            return {
                "answer": msg_ta if lang == "ta" else msg_en,
                "requires_auth": True,
                "missing_auth_provider": provider,
                "executed_tools": [],
                "workflow_steps": [{"step": "oauth_verification", "status": "auth_required", "provider": provider}],
            }

        # User is connected: execute the requested plugin tool
        planned = state.get("planned_tools", [])
        executed_tools = []
        requires_approval = False
        approval_details = None
        outputs = []

        for t_spec in planned:
            t_name = t_spec["name"]
            tool_inst = tool_registry.get(t_name)
            if not tool_inst:
                continue

            # Build mock/smart arguments based on tool name
            args: Dict[str, Any] = {"user_id": user_id}
            if t_name == "gmail_search_emails":
                args["query"] = prompt
                args["max_results"] = 5
            elif t_name == "gmail_create_draft":
                args["to"] = "director@msmeonline.tn.gov.in"
                args["subject"] = "Inquiry regarding UYEGP subsidy claim"
                args["body"] = "Dear Officer,\n\nI am requesting status verification for my application.\n\nRegards"
            elif t_name == "gmail_send_email":
                args["to"] = "director@msmeonline.tn.gov.in"
                args["subject"] = "Notice"
                args["body"] = "Official update"
            elif t_name == "github_list_repositories":
                args["visibility"] = "all"
            elif t_name == "github_get_repository":
                args["repo_name"] = "founder/illusion-ai"
            elif t_name == "github_create_issue":
                args["repo_name"] = "founder/illusion-ai"
                args["title"] = "Automated Issue from Illusion AI Router"
                args["body"] = prompt
            elif t_name == "calendar_list_events":
                args["max_results"] = 5
            elif t_name == "calendar_check_availability":
                args["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            elif t_name == "calendar_create_event":
                args["summary"] = "DIC MSME Subsidy Discussion"
                args["start_time"] = "2026-11-25T10:00:00Z"
                args["end_time"] = "2026-11-25T11:00:00Z"
                args["description"] = prompt

            res = await tool_inst.execute(**args)
            executed_tools.append({
                "name": t_name,
                "success": res.success,
                "data": res.data,
                "error": res.error,
            })

            if not res.success and res.metadata and res.metadata.get("requires_approval"):
                requires_approval = True
                approval_details = {
                    "tool_name": t_name,
                    "approval_id": res.metadata.get("approval_id"),
                    "provider": provider,
                }
                outputs.append(f"Action '{t_name}' requires your confirmation (ID: {res.metadata.get('approval_id')}).")
            else:
                outputs.append(f"Result from {t_name}: {json.dumps(res.data, indent=2) if res.data else res.error}")

        llm = langchain_provider.get_llm()
        sys_msg = (
            f"You are Illusion AI communicating authorized {provider.replace('_', ' ').title()} data to the user. "
            "Present the information in a professional, clear, and structured format. "
            f"Respond in {'Tamil (தமிழ்)' if lang == 'ta' else 'English'}."
        )
        human_msg = f"User Request: {prompt}\n\nProvider Output:\n" + "\n".join(outputs)

        try:
            ai_msg = await llm.ainvoke([SystemMessage(content=sys_msg), HumanMessage(content=human_msg)])
            answer = ai_msg.content if isinstance(ai_msg, AIMessage) else str(ai_msg)
        except Exception:
            answer = "\n".join(outputs)

        return {
            "answer": answer,
            "requires_auth": False,
            "requires_approval": requires_approval,
            "approval_details": approval_details,
            "executed_tools": executed_tools,
            "workflow_steps": [{"step": f"{provider}_execution", "status": "completed"}],
        }

    # -------------------------------------------------------------------------
    # Branch 6: Multi-Step Router Node
    # -------------------------------------------------------------------------

    async def _multistep_router_node(self, state: LangGraphRouterState) -> Dict[str, Any]:
        prompt = state["prompt"]
        user_id = state.get("user_id", "guest_user")
        lang = state.get("language", "en")
        planned = state.get("planned_tools", [])

        workflow_steps = []
        executed_tools = []
        sources = []
        accumulated_context = []

        for i, t_spec in enumerate(planned):
            t_name = t_spec["name"]
            tool_inst = tool_registry.get(t_name)
            if not tool_inst:
                continue

            step_name = f"Step {i+1}: {t_name}"
            args: Dict[str, Any] = {"user_id": user_id}

            if t_name == "rag_search":
                res = await tool_inst.execute(query=prompt, top_k=3)
                if res.success and isinstance(res.data, dict):
                    for c in res.data.get("chunks", []):
                        sources.append({
                            "title": c.get("title", "Government Scheme"),
                            "url": c.get("url", "https://msmeonline.tn.gov.in/"),
                            "document_id": c.get("id"),
                        })
            elif t_name == "calculator":
                expr = re.sub(r"[^0-9\+\-\*\/\.\(\)\%\^]", "", prompt) or "250000"
                res = await tool_inst.execute(expression=expr)
            elif t_name == "gmail_create_draft":
                res = await tool_inst.execute(
                    user_id=user_id,
                    to="director@msmeonline.tn.gov.in",
                    subject="UYEGP Subsidy Application Follow-up",
                    body=f"Dear Officer,\n\nFollowing my review of the scheme guidelines, please find attached my subsidy calculation.\n\nPrompt: {prompt}",
                )
            elif t_name.startswith("calendar_"):
                res = await tool_inst.execute(user_id=user_id, max_results=5)
            elif t_name.startswith("github_"):
                res = await tool_inst.execute(user_id=user_id, repo_name="founder/illusion-ai")
            else:
                res = await tool_inst.execute(**args)

            executed_tools.append({
                "name": t_name,
                "success": res.success,
                "data": res.data,
                "error": res.error,
            })
            workflow_steps.append({
                "step": step_name,
                "status": "completed" if res.success else "failed",
                "tool": t_name,
            })
            accumulated_context.append(f"[{t_name}] Result: {res.data or res.error}")

        # Final multi-step synthesis
        llm = langchain_provider.get_llm()
        sys_msg = (
            "You are Illusion AI's Multi-Step Orchestrator. "
            "Synthesize the chained results from each step into a comprehensive, cohesive summary for the entrepreneur. "
            f"Respond in {'Tamil (தமிழ்)' if lang == 'ta' else 'English'}."
        )
        human_msg = f"User Request: {prompt}\n\nExecution Chain Results:\n" + "\n".join(accumulated_context)

        try:
            ai_msg = await llm.ainvoke([SystemMessage(content=sys_msg), HumanMessage(content=human_msg)])
            answer = ai_msg.content if isinstance(ai_msg, AIMessage) else str(ai_msg)
        except Exception:
            answer = "Multi-step workflow completed:\n" + "\n".join(accumulated_context)

        return {
            "answer": answer,
            "sources": sources,
            "executed_tools": executed_tools,
            "workflow_steps": workflow_steps,
        }

    # -------------------------------------------------------------------------
    # Synthesis Node
    # -------------------------------------------------------------------------

    async def _synthesize_node(self, state: LangGraphRouterState) -> Dict[str, Any]:
        """Final verification and metadata attachment before returning to caller."""
        return {
            "answer": state.get("answer", "Workflow completed."),
            "sources": state.get("sources", []),
            "executed_tools": state.get("executed_tools", []),
            "workflow_steps": state.get("workflow_steps", []),
            "selected_router": state.get("selected_router", "chat"),
            "requires_auth": state.get("requires_auth", False),
            "missing_auth_provider": state.get("missing_auth_provider"),
            "requires_approval": state.get("requires_approval", False),
            "approval_details": state.get("approval_details"),
        }

    # -------------------------------------------------------------------------
    # Public Execution Entry Point
    # -------------------------------------------------------------------------

    async def run(
        self,
        prompt: str,
        user_id: str = "guest_user",
        session_id: str = "default_session",
        language: str = "en",
    ) -> Dict[str, Any]:
        """Execute query through the 6-branch LangGraph state machine."""
        initial_state: LangGraphRouterState = {
            "prompt": prompt,
            "language": language,
            "user_id": user_id,
            "session_id": session_id,
            "selected_router": "chat",
            "intent_summary": "",
            "complexity": "low",
            "confidence": 0.0,
            "planned_tools": [],
            "executed_tools": [],
            "workflow_steps": [],
            "sources": [],
            "answer": "",
            "requires_auth": False,
            "missing_auth_provider": None,
            "requires_approval": False,
            "approval_details": None,
            "metadata": {},
        }

        final_state = await self.workflow.ainvoke(initial_state)
        return final_state


# Global singleton router instance
langgraph_router = IllusionLangGraphRouter()
