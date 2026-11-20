"""Comprehensive tests for the Intelligent Hybrid Router system."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.router.schemas import (
    PromptAnalysis,
    RoutingDecision,
    ExecutionPlan,
    ExecutionStep,
    ExecutionResult,
    ExecutionMode,
    IntentDomain,
    ComplexityLevel,
    RiskLevel,
    ToolSelectionMode,
)
from app.router.intent_classifier import IntentClassifier
from app.router.decision_engine import DecisionEngine
from app.router.execution_engine import ExecutionEngine
from app.router.response_synthesizer import ResponseSynthesizer
from app.router.mcp_manager import mcp_manager


@pytest.fixture
def client():
    return TestClient(app)


# ===================================================================
# 1. Schema Validation Tests
# ===================================================================

def test_prompt_analysis_schema_defaults():
    """PromptAnalysis should have sensible defaults."""
    pa = PromptAnalysis(original_prompt="hello")
    assert pa.language == "en"
    assert pa.intent_domain == IntentDomain.UNKNOWN
    assert pa.complexity == ComplexityLevel.LOW
    assert pa.risk_level == RiskLevel.SAFE
    assert pa.requires_rag is False
    assert pa.requires_web is False
    assert pa.confidence == 0.5


def test_execution_plan_schema():
    """ExecutionPlan should correctly hold analysis and steps."""
    analysis = PromptAnalysis(original_prompt="test", intent_domain=IntentDomain.GREETING)
    step = RoutingDecision(tool_name="calculator", arguments={"expression": "1+1"}, reason="test")
    plan = ExecutionPlan(analysis=analysis, execution_mode=ExecutionMode.SINGLE_TOOL, steps=[step])
    assert len(plan.steps) == 1
    assert plan.steps[0].tool_name == "calculator"
    assert plan.requires_approval is False


# ===================================================================
# 2. Intent Classifier Tests (Heuristic Fallback)
# ===================================================================

@pytest.mark.asyncio
async def test_classifier_greeting():
    """Greetings should produce GREETING domain with TRIVIAL complexity."""
    result = await IntentClassifier.analyse("hello, how are you?")
    assert result.intent_domain == IntentDomain.GREETING
    assert result.complexity == ComplexityLevel.TRIVIAL
    assert len(result.suggested_tools) == 0


@pytest.mark.asyncio
async def test_classifier_scheme_query():
    """Scheme queries should flag requires_rag and suggest rag_search."""
    result = await IntentClassifier.analyse("What is NEEDS scheme subsidy in Tamil Nadu?")
    assert result.requires_rag is True
    assert "rag_search" in result.suggested_tools
    assert result.intent_domain == IntentDomain.GOVERNMENT_SCHEME


@pytest.mark.asyncio
async def test_classifier_calculation_query():
    """Math queries should flag requires_calculation and suggest calculator."""
    result = await IntentClassifier.analyse("Calculate 2500000 * 0.25 for subsidy amount")
    assert result.requires_calculation is True
    assert "calculator" in result.suggested_tools


@pytest.mark.asyncio
async def test_classifier_web_query():
    """Current/latest queries should flag requires_web."""
    result = await IntentClassifier.analyse("What are the latest MSME updates in 2026?")
    assert result.requires_web is True
    assert "web_search" in result.suggested_tools


@pytest.mark.asyncio
async def test_classifier_tamil_detection():
    """Tamil text should be detected correctly."""
    result = await IntentClassifier.analyse("தமிழ்நாட்டில் NEEDS மானியம் எவ்வளவு?")
    assert result.language == "ta"


@pytest.mark.asyncio
async def test_classifier_multi_tool_complexity():
    """Queries needing multiple tools should have MEDIUM+ complexity."""
    result = await IntentClassifier.analyse(
        "Calculate 5000000 * 0.25 and find the latest NEEDS scheme eligibility rules"
    )
    assert len(result.suggested_tools) >= 2
    assert result.complexity.value in ["medium", "high"]


# ===================================================================
# 3. Decision Engine Tests
# ===================================================================

def test_decision_engine_manual_mode():
    """Manual mode should include ONLY user-specified tools."""
    analysis = PromptAnalysis(original_prompt="anything", requires_rag=True)
    plan = DecisionEngine.plan(
        analysis=analysis,
        mode=ToolSelectionMode.MANUAL,
        manual_tools=["calculator"],
    )
    tool_names = [s.tool_name for s in plan.steps]
    assert "calculator" in tool_names
    assert "rag_search" not in tool_names


def test_decision_engine_auto_mode_scheme():
    """Auto mode with scheme domain should auto-select rag_search."""
    analysis = PromptAnalysis(
        original_prompt="Tell me about NEEDS",
        intent_domain=IntentDomain.GOVERNMENT_SCHEME,
        requires_rag=True,
        suggested_tools=["rag_search"],
    )
    plan = DecisionEngine.plan(analysis=analysis, mode=ToolSelectionMode.AUTO)
    tool_names = [s.tool_name for s in plan.steps]
    assert "rag_search" in tool_names


def test_decision_engine_hybrid_mode():
    """Hybrid mode should include manual tools + auto-detected tools."""
    analysis = PromptAnalysis(
        original_prompt="NEEDS subsidy details and calculate 50000 * 0.25",
        intent_domain=IntentDomain.GOVERNMENT_SCHEME,
        requires_rag=True,
        requires_calculation=True,
        suggested_tools=["rag_search", "calculator"],
    )
    plan = DecisionEngine.plan(
        analysis=analysis,
        mode=ToolSelectionMode.HYBRID,
        manual_tools=["web_search"],
    )
    tool_names = [s.tool_name for s in plan.steps]
    assert "web_search" in tool_names  # manual
    assert "rag_search" in tool_names  # auto from domain
    assert "calculator" in tool_names  # auto from flag


def test_decision_engine_no_tools_greeting():
    """Greeting analysis should produce DIRECT_LLM with zero steps."""
    analysis = PromptAnalysis(
        original_prompt="Hi there!",
        intent_domain=IntentDomain.GREETING,
        complexity=ComplexityLevel.TRIVIAL,
    )
    plan = DecisionEngine.plan(analysis=analysis, mode=ToolSelectionMode.AUTO)
    assert plan.execution_mode == ExecutionMode.DIRECT_LLM
    assert len(plan.steps) == 0


def test_decision_engine_parallel_mode():
    """Multiple independent tools should produce PARALLEL execution mode."""
    analysis = PromptAnalysis(
        original_prompt="Search web and RAG for NEEDS scheme",
        requires_rag=True,
        requires_web=True,
        suggested_tools=["rag_search", "web_search"],
    )
    plan = DecisionEngine.plan(analysis=analysis, mode=ToolSelectionMode.AUTO)
    assert plan.execution_mode == ExecutionMode.PARALLEL
    assert len(plan.steps) >= 2


def test_decision_engine_max_steps_cap():
    """Plan should respect ROUTER_MAX_STEPS cap."""
    analysis = PromptAnalysis(
        original_prompt="test",
        requires_rag=True, requires_web=True,
        requires_calculation=True, requires_file=True,
        suggested_tools=["rag_search", "web_search", "calculator", "file_reader"],
    )
    plan = DecisionEngine.plan(analysis=analysis, mode=ToolSelectionMode.AUTO)
    from app.core.config import settings
    assert len(plan.steps) <= settings.ROUTER_MAX_STEPS


# ===================================================================
# 4. Execution Engine Tests
# ===================================================================

@pytest.mark.asyncio
async def test_execution_engine_calculator():
    """Execution engine should successfully execute calculator."""
    analysis = PromptAnalysis(original_prompt="calc test")
    step = RoutingDecision(tool_name="calculator", arguments={"expression": "100 * 25"})
    plan = ExecutionPlan(analysis=analysis, execution_mode=ExecutionMode.SINGLE_TOOL, steps=[step])
    result = await ExecutionEngine.execute(plan)
    assert len(result.steps) == 1
    assert result.steps[0].success is True
    assert result.steps[0].result_data["result"] == 2500.0
    assert result.total_duration_ms > 0


@pytest.mark.asyncio
async def test_execution_engine_parallel():
    """Parallel execution should run multiple tools and return results for each."""
    analysis = PromptAnalysis(original_prompt="parallel test")
    steps = [
        RoutingDecision(tool_name="calculator", arguments={"expression": "2 + 2"}),
        RoutingDecision(tool_name="rag_search", arguments={"query": "NEEDS scheme", "limit": 2}),
    ]
    plan = ExecutionPlan(analysis=analysis, execution_mode=ExecutionMode.PARALLEL, steps=steps)
    result = await ExecutionEngine.execute(plan)
    assert len(result.steps) == 2
    calc_step = next(s for s in result.steps if s.tool_name == "calculator")
    rag_step = next(s for s in result.steps if s.tool_name == "rag_search")
    assert calc_step.success is True
    assert rag_step.success is True


@pytest.mark.asyncio
async def test_execution_engine_nonexistent_tool():
    """Non-existent tool should return failure without crashing."""
    analysis = PromptAnalysis(original_prompt="bad tool test")
    step = RoutingDecision(tool_name="nonexistent_tool", arguments={})
    plan = ExecutionPlan(analysis=analysis, execution_mode=ExecutionMode.SINGLE_TOOL, steps=[step])
    result = await ExecutionEngine.execute(plan)
    assert len(result.steps) == 1
    assert result.steps[0].success is False
    assert "not registered" in result.steps[0].error


@pytest.mark.asyncio
async def test_execution_engine_empty_plan():
    """Empty plan should return immediately with success."""
    analysis = PromptAnalysis(original_prompt="empty")
    plan = ExecutionPlan(analysis=analysis, execution_mode=ExecutionMode.DIRECT_LLM, steps=[])
    result = await ExecutionEngine.execute(plan)
    assert result.all_succeeded is True
    assert len(result.steps) == 0


@pytest.mark.asyncio
async def test_execution_steps_to_tool_results():
    """steps_to_tool_results should convert correctly for backward compat."""
    steps = [
        ExecutionStep(tool_name="calculator", success=True, result_data={"result": 42}, duration_ms=5.0),
        ExecutionStep(tool_name="web_search", success=False, error="timeout", duration_ms=15000.0),
    ]
    tool_results = ExecutionEngine.steps_to_tool_results(steps)
    assert len(tool_results) == 2
    assert tool_results[0].tool_name == "calculator"
    assert tool_results[0].success is True
    assert tool_results[0].data["result"] == 42
    assert tool_results[1].success is False


# ===================================================================
# 5. Response Synthesizer Tests
# ===================================================================

@pytest.mark.asyncio
async def test_synthesizer_fallback_with_results():
    """When LLM is unavailable, synthesizer should build fallback from tool data."""
    analysis = PromptAnalysis(original_prompt="test", language="en")
    steps = [
        ExecutionStep(tool_name="calculator", success=True, result_data={"result": 625000}),
    ]
    # ResponseSynthesizer will try LLM then fallback
    answer = await ResponseSynthesizer.synthesise(analysis, steps)
    assert answer is not None
    assert len(answer) > 0


@pytest.mark.asyncio
async def test_synthesizer_empty_steps():
    """With no steps, synthesizer should still produce a response."""
    analysis = PromptAnalysis(original_prompt="hello", language="en")
    answer = await ResponseSynthesizer.synthesise(analysis, [])
    assert answer is not None
    assert len(answer) > 0


# ===================================================================
# 6. MCP Manager Tests
# ===================================================================

def test_mcp_manager_disabled():
    """MCP manager should report disabled and zero tools in Phase 1."""
    # MCP_DISCOVERY_ENABLED defaults to False
    assert mcp_manager.tool_count == 0
    assert mcp_manager.list_tools() == []


@pytest.mark.asyncio
async def test_mcp_invoke_returns_none():
    """MCP invoke should return None in Phase 1 stub."""
    result = await mcp_manager.invoke("some_tool", {"arg": "val"})
    assert result is None


# ===================================================================
# 7. Router API Endpoint Tests
# ===================================================================

def test_router_analyze_endpoint(client):
    """POST /api/router/analyze should return analysis and plan."""
    payload = {"prompt": "What is NEEDS scheme subsidy?", "language": "en", "tool_mode": "auto"}
    resp = client.post("/api/router/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis" in data
    assert "plan" in data
    assert data["analysis"]["original_prompt"] == "What is NEEDS scheme subsidy?"


def test_router_execute_endpoint(client):
    """POST /api/router/execute should return full answer with metadata."""
    payload = {
        "prompt": "Calculate 2500000 * 0.25",
        "language": "en",
        "tool_mode": "manual",
        "selected_tools": ["calculator"],
        "tool_args": {"calculator": {"expression": "2500000 * 0.25"}},
    }
    resp = client.post("/api/router/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert data["tool_count"] >= 1
    assert data["executed_tools"][0]["tool_name"] == "calculator"
    assert data["executed_tools"][0]["success"] is True
    assert data["executed_tools"][0]["result_data"]["result"] == 625000.0


def test_router_status_endpoint(client):
    """GET /api/router/status should return operational status."""
    resp = client.get("/api/router/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"
    assert "registered_tools" in data
    assert "calculator" in data["registered_tools"]


def test_router_execute_greeting(client):
    """Greeting prompts should return a direct LLM answer with zero tools."""
    payload = {"prompt": "Hello!", "language": "en", "tool_mode": "auto"}
    resp = client.post("/api/router/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["execution_mode"] == "direct_llm"
    assert data["tool_count"] == 0


def test_router_analyze_tamil(client):
    """Tamil prompts should be classified with language=ta."""
    payload = {"prompt": "தமிழ்நாட்டில் NEEDS மானியம் எவ்வளவு?", "tool_mode": "auto"}
    resp = client.post("/api/router/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["analysis"]["language"] == "ta"


# ===================================================================
# 8. Backward Compatibility: Existing Chat Endpoint Still Works
# ===================================================================

def test_existing_chat_endpoint_still_works(client):
    """The existing /api/chat endpoint should still function correctly."""
    payload = {
        "question": "Calculate 10000 * 0.25",
        "language": "en",
        "tool_mode": "manual",
        "selected_tools": ["calculator"],
        "tool_args": {"calculator": {"expression": "10000 * 0.25"}},
    }
    resp = client.post("/api/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["executed_tools"]) > 0
    assert data["executed_tools"][0]["tool_name"] == "calculator"
    assert data["executed_tools"][0]["success"] is True
