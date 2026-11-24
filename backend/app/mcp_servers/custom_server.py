"""Custom MCP Server for Illusion AI: illusion_custom.

Provides initial diagnostic and utility tools:
- get_project_info
- list_project_modules
- calculate (safe AST math parser, never unrestricted eval)
- get_system_status (health metrics without credentials)
"""

import ast
import operator
import sys
import os
from typing import Dict, Any, List
from mcp.server import MCPServer

# Initialize server
server = MCPServer("illusion_custom")


# Supported safe operators for AST calculator
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval_ast(node: ast.AST) -> float:
    """Safely evaluate an arithmetic AST expression."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.BinOp):
        left = safe_eval_ast(node.left)
        right = safe_eval_ast(node.right)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                raise ZeroDivisionError("Division by zero is not permitted.")
            if op_type == ast.Pow and abs(right) > 100:
                raise ValueError("Exponent too large (max 100).")
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
    elif isinstance(node, ast.UnaryOp):
        operand = safe_eval_ast(node.operand)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    else:
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")


@server.tool()
def get_project_info() -> Dict[str, Any]:
    """Return Illusion AI project information, architecture, and capabilities."""
    return {
        "project_name": "Illusion AI",
        "description": "Production AI Assistant with RAG, LangChain, Multi-Model Routing, MCP, and GitHub Integration",
        "version": "2.0.0",
        "architecture": {
            "backend": "FastAPI + LangChain + LangGraph",
            "frontend": "Next.js + React + Tailwind CSS",
            "database": "Supabase PostgreSQL + pgvector",
            "protocols": ["MCP (Model Context Protocol)", "REST", "SSE", "OAuth 2.0"],
        },
        "capabilities": [
            "Hybrid Intelligent Tool Routing",
            "RAG Vector Search & Embeddings",
            "Dynamic MCP Tool Discovery & Execution",
            "GitHub Repository Code Analysis & OAuth",
            "Human-in-the-Loop Approval Workflows",
            "Bilingual English / Tamil Natural Language Processing",
        ],
        "status": "operational",
    }


@server.tool()
def list_project_modules() -> Dict[str, Any]:
    """Return available backend and frontend modules in Illusion AI."""
    return {
        "backend_modules": {
            "api_routes": [
                "/api/chat",
                "/api/auth/register",
                "/api/auth/login",
                "/api/auth/google",
                "/api/github/url",
                "/api/github/callback",
                "/api/github/repos",
                "/api/mcp/servers",
                "/api/mcp/tools",
                "/api/mcp/permissions",
                "/api/mcp/approvals",
                "/api/mcp/logs",
            ],
            "ai_router": [
                "DecisionEngine",
                "IntentClassifier",
                "ToolRegistry",
                "ConversationManager",
            ],
            "mcp_engine": [
                "MCPClientManager",
                "DynamicToolDiscovery",
                "PermissionManager",
                "ApprovalQueue",
                "SandboxedExecutor",
            ],
            "services": [
                "RAGPipeline",
                "TokenManager",
                "GitHubService",
                "WebSearchService",
            ],
        },
        "frontend_modules": {
            "pages": [
                "/",
                "/chat",
                "/mcp",
                "/github",
                "/marketplace",
                "/docs",
                "/settings",
            ],
            "components": [
                "Navbar",
                "MarketplaceDashboard",
                "ApprovalCard",
                "ToolResultViewer",
                "MCPDashboard",
            ],
        },
    }


@server.tool()
def calculate(expression: str) -> Dict[str, Any]:
    """Perform safe mathematical calculations without eval().

    Args:
        expression: Mathematical expression string, e.g., '125 * 4 + (50 / 2) - 3^2'
    """
    clean_expr = expression.strip().replace("^", "**")
    try:
        parsed = ast.parse(clean_expr, mode="eval")
        result = safe_eval_ast(parsed.body)
        return {
            "expression": expression,
            "result": result,
            "status": "success",
        }
    except ZeroDivisionError as e:
        return {"expression": expression, "error": str(e), "status": "error"}
    except Exception as e:
        return {
            "expression": expression,
            "error": f"Invalid or unsafe expression: {str(e)}",
            "status": "error",
        }


@server.tool()
def get_system_status() -> Dict[str, Any]:
    """Return application health and configured service status. Never exposes secrets or tokens."""
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_supabase = bool(os.getenv("SUPABASE_URL"))
    has_github = bool(os.getenv("GITHUB_CLIENT_ID"))

    return {
        "status": "healthy",
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "services": {
            "supabase_configured": has_supabase,
            "groq_configured": has_groq,
            "gemini_configured": has_gemini,
            "github_oauth_configured": has_github,
            "mcp_runtime": "active",
        },
        "security": {
            "secrets_exposed": False,
            "auth_encryption": "Fernet AES-CBC enabled",
            "mcp_default_policy": "DENY",
        },
    }


if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run_stdio_async())
