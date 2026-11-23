"""LangChain Tool Adapter wrapping Illusion AI tools as standard LangChain BaseTools."""

from typing import List, Dict, Any, Optional, Type
import json
import asyncio
from pydantic import BaseModel, create_model, Field
from langchain_core.tools import BaseTool as LangChainBaseTool, StructuredTool

from app.core.logging import logger
from app.tools.registry import tool_registry
from app.tools.base import BaseTool as IllusionBaseTool, ToolParameter
from app.plugins import plugin_manager


def _create_pydantic_args_model(tool_name: str, parameters: List[ToolParameter]) -> Type[BaseModel]:
    """Dynamically generates a Pydantic schema model from a tool's parameters."""
    field_definitions: Dict[str, Any] = {}
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "object": dict,
        "array": list,
    }

    for p in parameters:
        py_type = type_mapping.get(p.type, Any)
        if not p.required:
            py_type = Optional[py_type]
            default_val = p.default
        else:
            default_val = ...

        field_definitions[p.name] = (py_type, Field(default=default_val, description=p.description))

    # Add optional user_id and approval_token fields
    field_definitions["user_id"] = (Optional[str], Field(default="guest_user", description="Authenticated user ID"))
    field_definitions["approval_token"] = (Optional[str], Field(default=None, description="Human approval confirmation token"))

    return create_model(f"{tool_name.title().replace('_', '')}Input", **field_definitions)


class IllusionLangChainTool(LangChainBaseTool):
    """Wraps an Illusion AI BaseTool as a LangChain BaseTool."""

    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None
    _inner_tool: Optional[IllusionBaseTool] = None

    def __init__(self, inner_tool: IllusionBaseTool, **kwargs):
        tool_def = inner_tool.definition
        args_model = _create_pydantic_args_model(tool_def.name, tool_def.parameters)
        super().__init__(
            name=tool_def.name,
            description=tool_def.description,
            args_schema=args_model,
            **kwargs,
        )
        self._inner_tool = inner_tool

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """Synchronous run fallback."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._arun(*args, **kwargs))

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        """Asynchronous execution calling the inner Illusion tool."""
        if not self._inner_tool:
            return json.dumps({"error": f"Tool '{self.name}' not configured"})

        try:
            result = await self._inner_tool.execute(**kwargs)
            if result.success:
                return json.dumps({"status": "success", "data": result.data})
            return json.dumps({"status": "error", "error": result.error, "metadata": result.metadata})
        except Exception as e:
            logger.error(f"Error executing LangChain tool {self.name}: {e}")
            return json.dumps({"status": "error", "error": str(e)})


class LangChainToolRegistry:
    """Provides LangChain-compatible tool instances for all registered tools."""

    @classmethod
    def get_all_langchain_tools(cls) -> List[LangChainBaseTool]:
        """Convert all registered tools into LangChain BaseTools."""
        lc_tools = []
        for name, tool in tool_registry.get_all().items():
            try:
                lc_tools.append(IllusionLangChainTool(inner_tool=tool))
            except Exception as e:
                logger.warning(f"Could not convert tool '{name}' to LangChain tool: {e}")
        return lc_tools

    @classmethod
    def get_tool(cls, name: str) -> Optional[LangChainBaseTool]:
        """Retrieve a specific LangChain tool by name."""
        inner = tool_registry.get(name)
        if inner:
            return IllusionLangChainTool(inner_tool=inner)
        return None


# Global helper instance
langchain_tools_registry = LangChainToolRegistry()
