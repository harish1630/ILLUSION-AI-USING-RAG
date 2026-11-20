"""Automated tests for Illusion AI Hybrid Tool System."""

import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.tools.registry import tool_registry
from app.tools.calculator.tool import CalculatorTool, SafeCalculator
from app.tools.file_reader.tool import FileReaderTool
from app.tools.web_search.tool import WebSearchTool
from app.tools.rag_search.tool import RAGSearchTool
from app.tools.router import ToolRouter, ToolSelectionMode


@pytest.fixture
def client():
    return TestClient(app)


# 1. Tool Registration Tests
def test_tool_registration():
    names = tool_registry.list_available_names()
    assert "calculator" in names
    assert "file_reader" in names
    assert "web_search" in names
    assert "rag_search" in names

    calc = tool_registry.get("calculator")
    assert calc is not None
    assert calc.definition.name == "calculator"
    assert calc.definition.category == "math"


# 2. Calculator Tool AST & Security Tests
@pytest.mark.asyncio
async def test_calculator_ast_valid():
    calc = CalculatorTool()
    # Basic math
    res1 = await calc.execute(expression="2500000 * 0.25")
    assert res1.success is True
    assert res1.data["result"] == 625000.0

    # Formulas with sqrt and powers
    res2 = await calc.execute(expression="sqrt(144) + (10 ** 2)")
    assert res2.success is True
    assert res2.data["result"] == 112.0


@pytest.mark.asyncio
async def test_calculator_ast_security_blocking():
    calc = CalculatorTool()
    # Code execution, imports, and eval must be completely blocked
    res1 = await calc.execute(expression="__import__('os').system('ls')")
    assert res1.success is False
    assert any(term in res1.error for term in ["Security error", "Disallowed", "Unknown", "Only direct math function calls are permitted"])

    res2 = await calc.execute(expression="eval('1 + 1')")
    assert res2.success is False

    res3 = await calc.execute(expression="10 / 0")
    assert res3.success is False
    assert "Division by zero" in res3.error


# 3. Web Search Tool Execution Tests
@pytest.mark.asyncio
async def test_web_search_execution():
    tool = WebSearchTool()
    res = await tool.execute(query="Tamil Nadu NEEDS subsidy scheme")
    assert res.success is True
    assert "results" in res.data
    assert len(res.data["results"]) > 0


# 4. RAG Search Retrieval Tests
@pytest.mark.asyncio
async def test_rag_search_execution():
    tool = RAGSearchTool()
    res = await tool.execute(query="NEEDS 25% capital subsidy Tamil Nadu", limit=2)
    assert res.success is True
    assert "chunks" in res.data
    assert len(res.data["chunks"]) > 0
    # Verified scheme presence
    chunk_titles = [c.get("title", "") for c in res.data["chunks"]]
    assert any("NEEDS" in t for t in chunk_titles)


# 5. File Reader Tool Tests (PDF, DOCX, TXT)
@pytest.mark.asyncio
async def test_file_reader_txt():
    reader = FileReaderTool()
    content = b"Illusion AI Project: Verification document for first-time startups."
    res = await reader.execute(file_bytes=content, file_name="notes.txt")
    assert res.success is True
    assert "Illusion AI Project" in res.data["content"]
    assert res.data["format"] == "txt"


@pytest.mark.asyncio
async def test_file_reader_pdf():
    import fitz

    # Create dummy in-memory PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Tamil Nadu MSME Guidelines for Entrepreneurs")
    pdf_bytes = doc.write()
    doc.close()

    reader = FileReaderTool()
    res = await reader.execute(file_bytes=pdf_bytes, file_name="guidelines.pdf")
    assert res.success is True
    assert "Tamil Nadu MSME Guidelines" in res.data["content"]
    assert res.data["format"] == "pdf"


@pytest.mark.asyncio
async def test_file_reader_docx():
    import docx

    # Create dummy in-memory DOCX
    doc = docx.Document()
    doc.add_heading("Sample Business Plan", level=1)
    doc.add_paragraph("Estimated investment: Rs 15 Lakhs.")
    docx_buf = io.BytesIO()
    doc.save(docx_buf)
    docx_bytes = docx_buf.getvalue()

    reader = FileReaderTool()
    res = await reader.execute(file_bytes=docx_bytes, file_name="plan.docx")
    assert res.success is True
    assert "Sample Business Plan" in res.data["content"]
    assert "Estimated investment: Rs 15 Lakhs." in res.data["content"]
    assert res.data["format"] == "docx"


# 6. Automatic, Manual, and Hybrid Tool Selection Tests
@pytest.mark.asyncio
async def test_tool_routing_manual():
    planned = await ToolRouter.route(
        prompt="Tell me about Chennai",
        mode=ToolSelectionMode.MANUAL,
        manual_tools=["calculator", "web_search"],
    )
    names = [p.tool_name for p in planned]
    assert "calculator" in names
    assert "web_search" in names
    assert "rag_search" not in names


@pytest.mark.asyncio
async def test_tool_routing_auto_heuristics():
    # Calculation query
    planned_calc = await ToolRouter.route(
        prompt="Calculate 5000000 * 0.25 for subsidy",
        mode=ToolSelectionMode.AUTO,
    )
    calc_names = [p.tool_name for p in planned_calc]
    assert "calculator" in calc_names

    # Scheme policy query
    planned_rag = await ToolRouter.route(
        prompt="What is the eligibility for NEEDS scheme subsidy in Tamil Nadu?",
        mode=ToolSelectionMode.AUTO,
    )
    rag_names = [p.tool_name for p in planned_rag]
    assert "rag_search" in rag_names


@pytest.mark.asyncio
async def test_tool_routing_hybrid():
    # In hybrid mode, manual selection is guaranteed and AI/heuristic can augment
    planned = await ToolRouter.route(
        prompt="What is 100000 * 0.25 and what are latest updates?",
        mode=ToolSelectionMode.HYBRID,
        manual_tools=["rag_search"],
    )
    names = [p.tool_name for p in planned]
    assert "rag_search" in names
    assert ("calculator" in names or "web_search" in names)


# 7. Tools and Chat API Endpoints Tests
def test_api_tools_list_endpoint(client):
    response = client.get("/api/tools/")
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    tool_names = [t["name"] for t in tools]
    assert "calculator" in tool_names
    assert "file_reader" in tool_names
    assert "web_search" in tool_names
    assert "rag_search" in tool_names


def test_api_tools_upload_endpoint(client):
    file_content = b"Sample text for illusion AI upload test."
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    response = client.post("/api/tools/upload", files=files)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["file_name"] == "test.txt"
    assert "Sample text for illusion AI" in res_data["data"]["content"]


def test_api_chat_endpoint_with_tools(client):
    payload = {
        "question": "Calculate 25% of 10000000 for NEEDS scheme subsidy",
        "language": "en",
        "tool_mode": "manual",
        "selected_tools": ["calculator"],
        "tool_args": {"calculator": {"expression": "10000000 * 0.25"}},
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    chat_res = response.json()
    assert "answer" in chat_res
    assert len(chat_res["executed_tools"]) > 0
    assert chat_res["executed_tools"][0]["tool_name"] == "calculator"
    assert chat_res["executed_tools"][0]["success"] is True
    assert chat_res["executed_tools"][0]["data"]["result"] == 2500000.0


def test_api_chat_endpoint_bilingual_tamil(client):
    payload = {
        "question": "தமிழ்நாட்டில் NEEDS மானியம் எவ்வளவு?",
        "language": "ta",
        "tool_mode": "auto",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    chat_res = response.json()
    assert chat_res["language"] == "ta"
    assert "disclaimer" in chat_res
