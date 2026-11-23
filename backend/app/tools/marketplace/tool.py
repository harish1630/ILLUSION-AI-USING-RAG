"""Marketplace Tools exposed to Illusion AI Router and LangGraph Agents."""

from typing import Dict, Any, Optional, List
from app.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from app.plugins import plugin_manager, ExecutionStatus


class GmailSearchEmailsTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="gmail_search_emails",
            display_name="Gmail Inbox Search",
            description="Search connected Gmail account for messages matching query terms, sender, or subject.",
            category="marketplace_email",
            requires_auth=True,
            parameters=[
                ToolParameter(name="query", type="string", description="Search query syntax e.g. 'from:investor' or 'funding'"),
                ToolParameter(name="max_results", type="integer", description="Max messages to return (default 5)", required=False, default=5),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        user_id = kwargs.pop("user_id", "guest_user")
        res = await plugin_manager.execute_tool(
            user_id=user_id,
            plugin_id="gmail",
            tool_name="gmail_search_emails",
            arguments=kwargs,
        )
        if res.status == ExecutionStatus.SUCCESS:
            return ToolResult(tool_name="gmail_search_emails", success=True, data=res.result)
        return ToolResult(tool_name="gmail_search_emails", success=False, error=res.error)


class GmailReadEmailTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="gmail_read_email",
            display_name="Read Gmail Message",
            description="Read the complete body and details of a specific Gmail message by its message_id.",
            category="marketplace_email",
            requires_auth=True,
            parameters=[
                ToolParameter(name="message_id", type="string", description="ID of the Gmail message"),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        user_id = kwargs.pop("user_id", "guest_user")
        res = await plugin_manager.execute_tool(
            user_id=user_id,
            plugin_id="gmail",
            tool_name="gmail_read_email",
            arguments=kwargs,
        )
        if res.status == ExecutionStatus.SUCCESS:
            return ToolResult(tool_name="gmail_read_email", success=True, data=res.result)
        return ToolResult(tool_name="gmail_read_email", success=False, error=res.error)


class GmailCreateDraftTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="gmail_create_draft",
            display_name="Create Gmail Draft",
            description="Compose a new draft message in the connected Gmail account without sending it.",
            category="marketplace_email",
            requires_auth=True,
            parameters=[
                ToolParameter(name="to", type="string", description="Recipient email address"),
                ToolParameter(name="subject", type="string", description="Email subject"),
                ToolParameter(name="body", type="string", description="Body text of the email"),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        user_id = kwargs.pop("user_id", "guest_user")
        res = await plugin_manager.execute_tool(
            user_id=user_id,
            plugin_id="gmail",
            tool_name="gmail_create_draft",
            arguments=kwargs,
        )
        if res.status == ExecutionStatus.SUCCESS:
            return ToolResult(tool_name="gmail_create_draft", success=True, data=res.result)
        return ToolResult(tool_name="gmail_create_draft", success=False, error=res.error)


class GmailSendEmailTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="gmail_send_email",
            display_name="Send Gmail Message",
            description="Send an email to a recipient. Requires explicit user confirmation / permission.",
            category="marketplace_email",
            requires_auth=True,
            parameters=[
                ToolParameter(name="to", type="string", description="Recipient email address"),
                ToolParameter(name="subject", type="string", description="Email subject"),
                ToolParameter(name="body", type="string", description="Body text of the email"),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        user_id = kwargs.pop("user_id", "guest_user")
        approval_token = kwargs.pop("approval_token", None)
        res = await plugin_manager.execute_tool(
            user_id=user_id,
            plugin_id="gmail",
            tool_name="gmail_send_email",
            arguments=kwargs,
            approval_token=approval_token,
        )
        if res.status == ExecutionStatus.SUCCESS:
            return ToolResult(tool_name="gmail_send_email", success=True, data=res.result)
        elif res.status == ExecutionStatus.APPROVAL_REQUIRED:
            return ToolResult(
                tool_name="gmail_send_email",
                success=False,
                error="Action requires explicit user confirmation.",
                metadata={"approval_id": res.approval_id, "requires_approval": True},
            )
        return ToolResult(tool_name="gmail_send_email", success=False, error=res.error)


class GitHubListIssuesTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_list_issues",
            display_name="GitHub List Issues",
            description="List issue tickets from a GitHub repository.",
            category="marketplace_developer",
            requires_auth=True,
            parameters=[
                ToolParameter(name="repo_name", type="string", description="Repository name e.g. 'owner/repo'"),
                ToolParameter(name="state", type="string", description="Issue state: 'open', 'closed', 'all'", required=False, default="open"),
                ToolParameter(name="limit", type="integer", description="Max issues to return", required=False, default=10),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        user_id = kwargs.pop("user_id", "guest_user")
        res = await plugin_manager.execute_tool(
            user_id=user_id,
            plugin_id="github",
            tool_name="github_list_issues",
            arguments=kwargs,
        )
        if res.status == ExecutionStatus.SUCCESS:
            return ToolResult(tool_name="github_list_issues", success=True, data=res.result)
        return ToolResult(tool_name="github_list_issues", success=False, error=res.error)


class GitHubCreateIssueTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="github_create_issue",
            display_name="GitHub Create Issue",
            description="Create a new issue ticket in a GitHub repository. Requires confirmation.",
            category="marketplace_developer",
            requires_auth=True,
            parameters=[
                ToolParameter(name="repo_name", type="string", description="Repository name e.g. 'owner/repo'"),
                ToolParameter(name="title", type="string", description="Title of the issue"),
                ToolParameter(name="body", type="string", description="Description / body markdown of the issue"),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        user_id = kwargs.pop("user_id", "guest_user")
        approval_token = kwargs.pop("approval_token", None)
        res = await plugin_manager.execute_tool(
            user_id=user_id,
            plugin_id="github",
            tool_name="github_create_issue",
            arguments=kwargs,
            approval_token=approval_token,
        )
        if res.status == ExecutionStatus.SUCCESS:
            return ToolResult(tool_name="github_create_issue", success=True, data=res.result)
        elif res.status == ExecutionStatus.APPROVAL_REQUIRED:
            return ToolResult(
                tool_name="github_create_issue",
                success=False,
                error="Creating an issue requires explicit user confirmation.",
                metadata={"approval_id": res.approval_id, "requires_approval": True},
            )
        return ToolResult(tool_name="github_create_issue", success=False, error=res.error)


class CalendarListEventsTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calendar_list_events",
            display_name="Google Calendar List Events",
            description="List upcoming calendar events from the user's primary Google Calendar.",
            category="marketplace_calendar",
            requires_auth=True,
            parameters=[
                ToolParameter(name="time_min", type="string", description="ISO start time (default now)", required=False, default=""),
                ToolParameter(name="time_max", type="string", description="ISO end time", required=False, default=""),
                ToolParameter(name="max_results", type="integer", description="Max events to return (default 10)", required=False, default=10),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        user_id = kwargs.pop("user_id", "guest_user")
        res = await plugin_manager.execute_tool(
            user_id=user_id,
            plugin_id="google_calendar",
            tool_name="calendar_list_events",
            arguments=kwargs,
        )
        if res.status == ExecutionStatus.SUCCESS:
            return ToolResult(tool_name="calendar_list_events", success=True, data=res.result)
        return ToolResult(tool_name="calendar_list_events", success=False, error=res.error)


class CalendarCheckAvailabilityTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calendar_check_availability",
            display_name="Google Calendar Check Availability",
            description="Check free/busy availability on a given date in the user's Google Calendar.",
            category="marketplace_calendar",
            requires_auth=True,
            parameters=[
                ToolParameter(name="date", type="string", description="Date in YYYY-MM-DD format (default today)", required=False, default=""),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        user_id = kwargs.pop("user_id", "guest_user")
        res = await plugin_manager.execute_tool(
            user_id=user_id,
            plugin_id="google_calendar",
            tool_name="calendar_check_availability",
            arguments=kwargs,
        )
        if res.status == ExecutionStatus.SUCCESS:
            return ToolResult(tool_name="calendar_check_availability", success=True, data=res.result)
        return ToolResult(tool_name="calendar_check_availability", success=False, error=res.error)


class CalendarCreateEventTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="calendar_create_event",
            display_name="Google Calendar Create Event",
            description="Schedule a new meeting/event in Google Calendar. SENSITIVE: Requires human confirmation.",
            category="marketplace_calendar",
            requires_auth=True,
            parameters=[
                ToolParameter(name="summary", type="string", description="Event title or subject"),
                ToolParameter(name="start_time", type="string", description="ISO format start time e.g. 2026-11-24T10:00:00Z"),
                ToolParameter(name="end_time", type="string", description="ISO format end time e.g. 2026-11-24T11:00:00Z"),
                ToolParameter(name="description", type="string", description="Optional event description or agenda", required=False, default=""),
            ],
        )

    async def execute(self, **kwargs) -> ToolResult:
        user_id = kwargs.pop("user_id", "guest_user")
        approval_token = kwargs.pop("approval_token", None)
        res = await plugin_manager.execute_tool(
            user_id=user_id,
            plugin_id="google_calendar",
            tool_name="calendar_create_event",
            arguments=kwargs,
            approval_token=approval_token,
        )
        if res.status == ExecutionStatus.SUCCESS:
            return ToolResult(tool_name="calendar_create_event", success=True, data=res.result)
        elif res.status == ExecutionStatus.APPROVAL_REQUIRED:
            return ToolResult(
                tool_name="calendar_create_event",
                success=False,
                error="Scheduling a calendar event requires explicit user confirmation.",
                metadata={"approval_id": res.approval_id, "requires_approval": True},
            )
        return ToolResult(tool_name="calendar_create_event", success=False, error=res.error)
