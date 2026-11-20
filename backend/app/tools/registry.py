"""Central Tool Registry for registering, managing, and inspecting available tools."""

from typing import Dict, List, Optional
from app.core.logging import logger
from app.tools.base import BaseTool, ToolDefinition
from app.tools.calculator.tool import CalculatorTool
from app.tools.file_reader.tool import FileReaderTool
from app.tools.web_search.tool import WebSearchTool
from app.tools.rag_search.tool import RAGSearchTool


class ToolRegistry:
    """Registry managing instances of all tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Initializes and registers standard tools."""
        self.register(CalculatorTool())
        self.register(FileReaderTool())
        self.register(WebSearchTool())
        self.register(RAGSearchTool())

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        name = tool.definition.name
        self._tools[name] = tool
        logger.info(f"Registered tool: '{name}' (Category: {tool.definition.category})")

    def unregister(self, name: str) -> bool:
        """Unregister a tool by name."""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: '{name}'")
            return True
        return False

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """List metadata definitions for all registered tools."""
        return [tool.definition for tool in self._tools.values()]

    def list_available_names(self) -> List[str]:
        """List names of all currently registered tools."""
        return list(self._tools.keys())

    def get_definitions_for_llm(self) -> List[Dict]:
        """Formats tool definitions for LLM tool selection prompts."""
        llm_defs = []
        for tool in self._tools.values():
            defn = tool.definition
            params_dict = {
                p.name: {"type": p.type, "description": p.description, "required": p.required}
                for p in defn.parameters
            }
            llm_defs.append({
                "name": defn.name,
                "description": defn.description,
                "parameters": params_dict,
            })
        return llm_defs


# Global registry singleton
tool_registry = ToolRegistry()
