"""Pydantic structured schemas for intelligent prompt routing and execution planning."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IntentDomain(str, Enum):
    """High-level domain the user prompt belongs to."""
    GOVERNMENT_SCHEME = "government_scheme"
    BUSINESS_STARTUP = "business_startup"
    LEGAL_REGULATORY = "legal_regulatory"
    FINANCIAL_CALCULATION = "financial_calculation"
    GENERAL_KNOWLEDGE = "general_knowledge"
    FILE_ANALYSIS = "file_analysis"
    WEB_LOOKUP = "web_lookup"
    GREETING = "greeting"
    UNKNOWN = "unknown"


class ComplexityLevel(str, Enum):
    """Estimated complexity of the user request."""
    TRIVIAL = "trivial"        # Simple greeting, one-liner
    LOW = "low"                # Single tool or direct LLM
    MEDIUM = "medium"          # 1-2 tools with synthesis
    HIGH = "high"              # Multi-tool, multi-step
    CRITICAL = "critical"      # Sensitive / irreversible actions


class RiskLevel(str, Enum):
    """Risk classification for the requested action."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"              # Needs user confirmation before executing


class ExecutionMode(str, Enum):
    """How the planned tools should be executed."""
    DIRECT_LLM = "direct_llm"       # No tools needed – pure LLM response
    SINGLE_TOOL = "single_tool"     # One tool then synthesise
    PARALLEL = "parallel"           # Multiple independent tools at once
    SEQUENTIAL = "sequential"       # Tools depend on each other's outputs
    MIXED = "mixed"                 # Some parallel, some sequential


class ToolSelectionMode(str, Enum):
    """User-facing mode for how tools are chosen."""
    AUTO = "auto"
    MANUAL = "manual"
    HYBRID = "hybrid"


# ---------------------------------------------------------------------------
# Prompt Analysis (output of Intent Classifier)
# ---------------------------------------------------------------------------

class PromptAnalysis(BaseModel):
    """Structured analysis of a user prompt produced by the Intent Classifier."""
    original_prompt: str = Field(..., description="The raw user prompt")
    language: str = Field(default="en", description="Detected language code (en / ta)")
    intent_domain: IntentDomain = Field(default=IntentDomain.UNKNOWN)
    intent_summary: str = Field(default="", description="One-line summary of what the user wants")
    complexity: ComplexityLevel = Field(default=ComplexityLevel.LOW)
    risk_level: RiskLevel = Field(default=RiskLevel.SAFE)
    requires_rag: bool = Field(default=False, description="Whether private/verified knowledge is needed")
    requires_web: bool = Field(default=False, description="Whether fresh external data is needed")
    requires_calculation: bool = Field(default=False, description="Whether math evaluation is needed")
    requires_file: bool = Field(default=False, description="Whether file reading/analysis is needed")
    requires_mcp: bool = Field(default=False, description="Whether MCP external integration is needed")
    requires_memory: bool = Field(default=False, description="Whether conversation history is needed")
    suggested_tools: List[str] = Field(default_factory=list, description="Tool names the classifier recommends")
    keywords: List[str] = Field(default_factory=list, description="Key terms extracted from the prompt")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Classifier confidence 0-1")


# ---------------------------------------------------------------------------
# Routing Decision (output of Decision Engine)
# ---------------------------------------------------------------------------

class RoutingDecision(BaseModel):
    """Final decision on which tools to invoke and how."""
    tool_name: str = Field(..., description="Registered tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="", description="Why this tool was selected")
    priority: int = Field(default=0, description="Execution priority (lower = first)")
    depends_on: List[str] = Field(default_factory=list, description="Tool names this depends on")


class ExecutionPlan(BaseModel):
    """Complete execution plan produced by the Decision Engine."""
    analysis: PromptAnalysis
    execution_mode: ExecutionMode = Field(default=ExecutionMode.DIRECT_LLM)
    steps: List[RoutingDecision] = Field(default_factory=list)
    requires_approval: bool = Field(default=False, description="True if risk_level is HIGH")
    fallback_strategy: str = Field(default="direct_llm", description="What to do if all tools fail")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Execution Step & Result (used by Execution Engine)
# ---------------------------------------------------------------------------

class ExecutionStep(BaseModel):
    """Runtime record of a single tool execution within a plan."""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    success: bool = False
    result_data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


class ExecutionResult(BaseModel):
    """Aggregate result from the Execution Engine."""
    plan: ExecutionPlan
    steps: List[ExecutionStep] = Field(default_factory=list)
    all_succeeded: bool = False
    total_duration_ms: float = 0.0


# ---------------------------------------------------------------------------
# Router API Request / Response schemas
# ---------------------------------------------------------------------------

class RouterAnalyzeRequest(BaseModel):
    """Request body for POST /api/router/analyze."""
    prompt: str = Field(..., min_length=1, description="User prompt to analyse")
    language: Optional[str] = Field(default="en")
    tool_mode: Optional[str] = Field(default="auto", description="auto / manual / hybrid")
    selected_tools: Optional[List[str]] = Field(default=None)
    tool_args: Optional[Dict[str, Dict[str, Any]]] = Field(default=None)
    conversation_id: Optional[str] = None


class RouterAnalyzeResponse(BaseModel):
    """Response body for POST /api/router/analyze."""
    analysis: PromptAnalysis
    plan: ExecutionPlan


class RouterExecuteRequest(BaseModel):
    """Request body for POST /api/router/execute."""
    prompt: str = Field(..., min_length=1)
    language: Optional[str] = Field(default="en")
    tool_mode: Optional[str] = Field(default="auto")
    selected_tools: Optional[List[str]] = Field(default=None)
    tool_args: Optional[Dict[str, Dict[str, Any]]] = Field(default=None)
    conversation_id: Optional[str] = None


class RouterExecuteResponse(BaseModel):
    """Response body for POST /api/router/execute."""
    answer: str
    language: str
    analysis: PromptAnalysis
    execution_mode: str
    executed_tools: List[ExecutionStep] = Field(default_factory=list)
    tool_count: int = 0
    total_duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
