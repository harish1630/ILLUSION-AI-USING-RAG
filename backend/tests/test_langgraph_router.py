"""Comprehensive Test Suite for LangGraph 6-Branch Intelligent Router."""

import pytest
import asyncio
from app.router.langgraph_router import langgraph_router
from app.plugins import plugin_manager
from app.ai.langchain_provider import conversation_memory


@pytest.mark.asyncio
async def test_router_chat_branch():
    """Test standard conversational prompts route to the chat router with memory."""
    prompt = "Hello! Can you help me understand how you can guide my business?"
    res = await langgraph_router.run(
        prompt=prompt,
        user_id="test_user_1",
        session_id="session_chat_test",
        language="en",
    )

    assert res["selected_router"] == "chat"
    assert len(res["answer"]) > 10
    assert res["requires_auth"] is False
    # Memory should have registered this interaction
    msgs = conversation_memory.get_messages("session_chat_test")
    assert len(msgs) >= 2


@pytest.mark.asyncio
async def test_router_rag_branch():
    """Test government scheme queries route to the RAG knowledge router."""
    prompt = "What is the subsidy percentage under the NEEDS scheme for first-generation entrepreneurs in Tamil Nadu?"
    res = await langgraph_router.run(
        prompt=prompt,
        user_id="test_user_2",
        session_id="session_rag_test",
        language="en",
    )

    assert res["selected_router"] == "rag"
    assert len(res["answer"]) > 10
    # Should execute rag_search tool
    executed = [t["name"] for t in res.get("executed_tools", [])]
    assert "rag_search" in executed


@pytest.mark.asyncio
async def test_router_tool_branch():
    """Test mathematical calculations route to the internal tool router."""
    prompt = "Calculate 25% of 1000000"
    res = await langgraph_router.run(
        prompt=prompt,
        user_id="test_user_3",
        session_id="session_tool_test",
        language="en",
    )

    assert res["selected_router"] == "tool"
    executed = [t["name"] for t in res.get("executed_tools", [])]
    assert "calculator" in executed


@pytest.mark.asyncio
async def test_router_oauth_unconnected_gate():
    """Test OAuth queries for unconnected users trigger the authorization requirement gate."""
    user_id = "unconnected_user_99"
    # Ensure user has no google_calendar connection
    await plugin_manager.disconnect_user_plugin(user_id, "google_calendar")

    prompt = "Show my calendar events for tomorrow"
    res = await langgraph_router.run(
        prompt=prompt,
        user_id=user_id,
        session_id="session_oauth_unconnected",
        language="en",
    )

    assert res["selected_router"] == "oauth"
    assert res["requires_auth"] is True
    assert res["missing_auth_provider"] == "google_calendar"
    assert "Marketplace" in res["answer"]


@pytest.mark.asyncio
async def test_router_oauth_connected_google_calendar():
    """Test OAuth queries for connected users execute calendar tools."""
    user_id = "connected_cal_user_1"
    # Connect mock Google Calendar
    plugin_manager.connect_user_plugin(
        user_id=user_id,
        plugin_id="google_calendar",
        raw_credentials={
            "access_token": "mock_calendar_token_12345",
            "account_id": "google_user_cal_123",
            "account_email": "founder@illusion.ai",
        },
    )

    prompt = "Check my calendar schedule and upcoming meetings"
    res = await langgraph_router.run(
        prompt=prompt,
        user_id=user_id,
        session_id="session_cal_exec",
        language="en",
    )

    assert res["selected_router"] == "oauth"
    assert res["requires_auth"] is False
    executed = [t["name"] for t in res.get("executed_tools", [])]
    assert "calendar_list_events" in executed
    assert len(res["answer"]) > 10


@pytest.mark.asyncio
async def test_router_multistep_workflow():
    """Test complex multi-capability queries trigger the multi-step orchestration branch."""
    user_id = "multistep_user_1"
    # Connect mock Gmail
    plugin_manager.connect_user_plugin(
        user_id=user_id,
        plugin_id="gmail",
        raw_credentials={
            "access_token": "mock_gmail_token_999",
            "account_id": "google_user_gmail_999",
            "account_email": "founder@illusion.ai",
        },
    )

    # Combines RAG scheme + Calculator + Gmail draft
    prompt = "Find UYEGP subsidy scheme details, calculate 25% of 500000 loan, and draft an email to the DIC officer"
    res = await langgraph_router.run(
        prompt=prompt,
        user_id=user_id,
        session_id="session_multi_test",
        language="en",
    )

    assert res["selected_router"] == "multistep"
    assert len(res["workflow_steps"]) >= 2
    executed = [t["name"] for t in res.get("executed_tools", [])]
    assert "rag_search" in executed or "calculator" in executed or "gmail_create_draft" in executed
