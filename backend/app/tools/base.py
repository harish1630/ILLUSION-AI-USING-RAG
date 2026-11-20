"""Base interfaces, schemas, and abstract classes for Illusion AI Tool System."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Specification of a parameter needed by a tool."""
    name: str
    type: str = "string"  # string, number, integer, boolean, object, array
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """Metadata schema defining a registered tool."""
    name: str = Field(..., description="Unique tool name identifier")
    display_name: str = Field(..., description="User-friendly display name")
    description: str = Field(..., description="Clear description of the tool purpose for LLM and UI")
    parameters: List[ToolParameter] = Field(default_factory=list, description="List of expected parameters")
    category: str = Field(default="general", description="Category: search, retrieval, document, math, etc.")
    requires_auth: bool = Field(default=False, description="Whether tool execution requires elevated authentication")
    is_available: bool = Field(default=True, description="Whether tool dependencies/keys are currently available")


class ToolResult(BaseModel):
    """Standard execution result returned by all tools."""
    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_llm_context(self) -> str:
        """Formats the result into safe, prompt-injection-resistant context for the LLM."""
        if not self.success:
            return f"[{self.tool_name} returned error]: {self.error}"
        
        # Prevent prompt injection by clearly sandboxing tool output in tags
        output_str = str(self.data) if self.data is not None else ""
        # Truncate overly verbose output to protect LLM context window
        if len(output_str) > 6000:
            output_str = output_str[:6000] + "... [Tool output truncated for length]"
            
        return f"--- START {self.tool_name.upper()} DATA ---\n{output_str}\n--- END {self.tool_name.upper()} DATA ---"


class BaseTool(ABC):
    """Abstract base class that all Illusion AI tools must implement."""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return tool metadata, schema, and capabilities."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with provided arguments safely."""
        pass

    def check_availability(self) -> bool:
        """Check if necessary environment variables, SDKs, or services are available."""
        return True
