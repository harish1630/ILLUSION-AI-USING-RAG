"""Google Calendar Integration Plugin for Illusion AI."""

import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlencode
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.plugins.base import BasePlugin
from app.plugins.schemas import PluginToolDefinition, PermissionLevel

GOOGLE_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class GoogleCalendarPlugin(BasePlugin):
    """Google Calendar marketplace plugin for listing, creating, and scheduling events."""

    def __init__(self):
        super().__init__(
            plugin_id="google_calendar",
            name="google_calendar",
            display_name="Google Calendar",
            description="Manage schedules, inspect upcoming meetings, check availability, and schedule events with AI.",
            category="productivity",
            icon="Calendar",
            auth_type="oauth2",
            scopes=CALENDAR_SCOPES,
            features=[
                "List upcoming calendar events",
                "Check free/busy time availability",
                "Schedule new events with explicit confirmation",
                "Sync meeting links & agendas",
            ],
        )

    def get_tools(self) -> List[PluginToolDefinition]:
        return [
            PluginToolDefinition(
                tool_name="calendar_list_events",
                qualified_name="google_calendar:calendar_list_events",
                description="List upcoming calendar events from user's primary calendar within a time range",
                input_schema={
                    "type": "object",
                    "properties": {
                        "time_min": {"type": "string", "description": "ISO formatted start time (default now)", "default": ""},
                        "time_max": {"type": "string", "description": "ISO formatted end time", "default": ""},
                        "max_results": {"type": "integer", "description": "Max events to retrieve (1-20)", "default": 10},
                    },
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="calendar_check_availability",
                qualified_name="google_calendar:calendar_check_availability",
                description="Check if user has free slots on a specific date or time range",
                input_schema={
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format (default today)"},
                    },
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="calendar_create_event",
                qualified_name="google_calendar:calendar_create_event",
                description="Schedule a new calendar event. SENSITIVE: Requires explicit human approval before creation.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Title/summary of the meeting or event"},
                        "start_time": {"type": "string", "description": "ISO formatted event start time"},
                        "end_time": {"type": "string", "description": "ISO formatted event end time"},
                        "description": {"type": "string", "description": "Optional event details or meeting agenda"},
                    },
                    "required": ["summary", "start_time", "end_time"],
                },
                is_sensitive=True,
                default_permission=PermissionLevel.APPROVAL_REQUIRED,
            ),
        ]

    def get_auth_url(self, user_id: str, redirect_uri: str) -> Tuple[str, str]:
        client_id = settings.GOOGLE_CLIENT_ID or "google_mock_client_id"
        state = f"calendar_{secrets.token_urlsafe(24)}"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        return url, state

    async def exchange_code(self, code: str, redirect_uri: str, state: Optional[str] = None) -> Dict[str, Any]:
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET

        if not client_id or not client_secret or client_id.startswith("google_mock") or code.startswith("mock_"):
            logger.info("Using mock Google Calendar token exchange for test/development")
            return {
                "access_token": f"mock_calendar_access_{secrets.token_hex(16)}",
                "refresh_token": f"mock_calendar_refresh_{secrets.token_hex(16)}",
                "expires_at": datetime.now(timezone.utc).isoformat(),
                "account_id": "google_user_cal_10928374",
                "account_email": "founder@illusion.ai",
                "account_username": "founder",
                "avatar_url": "https://lh3.googleusercontent.com/a/default-user",
                "scopes": self.scopes,
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if token_resp.status_code != 200:
                raise ValueError(f"Google Calendar token exchange failed: {token_resp.text}")

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            userinfo_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile = userinfo_resp.json() if userinfo_resp.status_code == 200 else {}

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": datetime.now(timezone.utc).isoformat(),
                "account_id": profile.get("id"),
                "account_email": profile.get("email"),
                "account_username": (profile.get("email") or "").split("@")[0] or profile.get("name"),
                "avatar_url": profile.get("picture"),
                "scopes": self.scopes,
            }

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        credentials: Dict[str, Any],
    ) -> Any:
        access_token = credentials.get("access_token")
        if not access_token:
            raise ValueError("Google Calendar access token missing or invalid")

        if access_token.startswith("mock_"):
            return self._execute_mock(tool_name, arguments)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            if tool_name == "calendar_list_events":
                max_results = min(int(arguments.get("max_results", 10)), 20)
                time_min = arguments.get("time_min") or datetime.now(timezone.utc).isoformat()
                params = {
                    "maxResults": max_results,
                    "timeMin": time_min,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                }
                if arguments.get("time_max"):
                    params["timeMax"] = arguments["time_max"]

                resp = await client.get(
                    f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events",
                    headers=headers,
                    params=params,
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"Calendar list events failed ({resp.status_code}): {resp.text}")
                data = resp.json()
                events = [
                    {
                        "id": item.get("id"),
                        "summary": item.get("summary", "Untitled Event"),
                        "start": item.get("start", {}).get("dateTime") or item.get("start", {}).get("date"),
                        "end": item.get("end", {}).get("dateTime") or item.get("end", {}).get("date"),
                        "status": item.get("status"),
                        "html_link": item.get("htmlLink"),
                    }
                    for item in data.get("items", [])
                ]
                return {"events": events, "count": len(events)}

            elif tool_name == "calendar_check_availability":
                target_date = arguments.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
                t_start = f"{target_date}T00:00:00Z"
                t_end = f"{target_date}T23:59:59Z"
                resp = await client.post(
                    f"{GOOGLE_CALENDAR_API_BASE}/freeBusy",
                    headers=headers,
                    json={
                        "timeMin": t_start,
                        "timeMax": t_end,
                        "items": [{"id": "primary"}],
                    },
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"Calendar free/busy query failed: {resp.text}")
                data = resp.json()
                busy_slots = data.get("calendars", {}).get("primary", {}).get("busy", [])
                return {
                    "date": target_date,
                    "is_free": len(busy_slots) == 0,
                    "busy_slots": busy_slots,
                }

            elif tool_name == "calendar_create_event":
                summary = arguments.get("summary")
                start_time = arguments.get("start_time")
                end_time = arguments.get("end_time")
                desc = arguments.get("description", "")

                body = {
                    "summary": summary,
                    "description": desc,
                    "start": {"dateTime": start_time},
                    "end": {"dateTime": end_time},
                }

                resp = await client.post(
                    f"{GOOGLE_CALENDAR_API_BASE}/calendars/primary/events",
                    headers=headers,
                    json=body,
                )
                if resp.status_code not in (200, 201):
                    raise RuntimeError(f"Calendar event creation failed: {resp.text}")
                data = resp.json()
                return {
                    "status": "created",
                    "event_id": data.get("id"),
                    "summary": summary,
                    "html_link": data.get("htmlLink"),
                    "start": start_time,
                    "end": end_time,
                }
            else:
                raise ValueError(f"Unknown Google Calendar tool: '{tool_name}'")

    def _execute_mock(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        now = datetime.now(timezone.utc)
        if tool_name == "calendar_list_events":
            return {
                "count": 2,
                "events": [
                    {
                        "id": "cal_evt_001",
                        "summary": "Tamil Nadu MSME DIC Verification Hearing",
                        "start": (now + timedelta(days=1, hours=2)).isoformat(),
                        "end": (now + timedelta(days=1, hours=3)).isoformat(),
                        "status": "confirmed",
                        "html_link": "https://calendar.google.com/calendar/event?eid=mock1",
                    },
                    {
                        "id": "cal_evt_002",
                        "summary": "TANSEED Mentorship & Pitch Practice Session",
                        "start": (now + timedelta(days=3, hours=4)).isoformat(),
                        "end": (now + timedelta(days=3, hours=5)).isoformat(),
                        "status": "confirmed",
                        "html_link": "https://calendar.google.com/calendar/event?eid=mock2",
                    },
                ],
            }
        elif tool_name == "calendar_check_availability":
            date_str = arguments.get("date") or now.strftime("%Y-%m-%d")
            return {
                "date": date_str,
                "is_free": True,
                "busy_slots": [
                    {
                        "start": f"{date_str}T10:00:00Z",
                        "end": f"{date_str}T11:00:00Z",
                    }
                ],
            }
        elif tool_name == "calendar_create_event":
            return {
                "status": "created",
                "event_id": f"evt_{uuid.uuid4().hex[:8]}",
                "summary": arguments.get("summary", "New Meeting"),
                "start": arguments.get("start_time"),
                "end": arguments.get("end_time"),
                "html_link": "https://calendar.google.com/calendar/event?eid=mock_new",
                "message": "Calendar event scheduled successfully.",
            }
        raise ValueError(f"Unknown Google Calendar tool: '{tool_name}'")

    async def revoke(self, credentials: Dict[str, Any]) -> bool:
        token = credentials.get("access_token")
        if not token or token.startswith("mock_"):
            return True
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            return True
        except Exception as e:
            logger.warning(f"Failed to revoke Google Calendar token with provider: {e}")
            return False
