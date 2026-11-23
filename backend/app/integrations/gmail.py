"""Google Gmail Integration Plugin for Illusion AI."""

import base64
import json
import uuid
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlencode
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.plugins.base import BasePlugin
from app.plugins.schemas import PluginToolDefinition, PermissionLevel

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class GmailPlugin(BasePlugin):
    """Gmail marketplace plugin for reading, searching, drafting, and sending emails."""

    def __init__(self):
        super().__init__(
            plugin_id="gmail",
            name="gmail",
            display_name="Google Gmail",
            description="Search emails, read communications, compose drafts, and securely send emails with AI assistance.",
            category="email",
            icon="Mail",
            auth_type="oauth2",
            scopes=GMAIL_SCOPES,
            features=[
                "Search inbox with search queries",
                "Read messages & threads",
                "Compose draft replies",
                "Send emails with explicit confirmation",
            ],
        )

    def get_tools(self) -> List[PluginToolDefinition]:
        return [
            PluginToolDefinition(
                tool_name="gmail_search_emails",
                qualified_name="gmail:gmail_search_emails",
                description="Search user's Gmail inbox for messages matching query (e.g. 'from:investor subject:funding')",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query syntax matching Gmail filters"},
                        "max_results": {"type": "integer", "description": "Max emails to retrieve (1-20)", "default": 5},
                    },
                    "required": ["query"],
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="gmail_read_email",
                qualified_name="gmail:gmail_read_email",
                description="Read full details and content of a specific email message by its message_id",
                input_schema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "Gmail message ID"},
                    },
                    "required": ["message_id"],
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="gmail_create_draft",
                qualified_name="gmail:gmail_create_draft",
                description="Create a draft email in user's Gmail inbox without sending it",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject line"},
                        "body": {"type": "string", "description": "Email message body text"},
                    },
                    "required": ["to", "subject", "body"],
                },
                is_sensitive=False,
                default_permission=PermissionLevel.ALLOW,
            ),
            PluginToolDefinition(
                tool_name="gmail_send_email",
                qualified_name="gmail:gmail_send_email",
                description="Send an email to a recipient. SENSITIVE: Requires explicit human approval before execution.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject line"},
                        "body": {"type": "string", "description": "Email message body text"},
                    },
                    "required": ["to", "subject", "body"],
                },
                is_sensitive=True,
                default_permission=PermissionLevel.APPROVAL_REQUIRED,
            ),
        ]

    def get_auth_url(self, user_id: str, redirect_uri: str) -> Tuple[str, str]:
        client_id = settings.GOOGLE_CLIENT_ID
        state = f"gmail_{secrets.token_urlsafe(24)}"

        if not client_id or client_id.startswith("google_mock") or client_id == "your_google_client_id_here":
            dev_url = f"{redirect_uri}?code=mock_gmail_code_{secrets.token_hex(8)}&state={state}&user_id={user_id}"
            return dev_url, state

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

        # If running in test or without configured secrets, provide mock credential structure
        if not client_id or not client_secret or client_id.startswith("google_mock") or code.startswith("mock_"):
            logger.info("Using mock Gmail token exchange for test/development")
            return {
                "access_token": f"mock_gmail_access_{secrets.token_hex(16)}",
                "refresh_token": f"mock_gmail_refresh_{secrets.token_hex(16)}",
                "expires_at": datetime.now(timezone.utc).isoformat(),
                "account_id": "google_user_10928374",
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
                raise ValueError(f"Google token exchange failed: {token_resp.text}")

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            # Fetch userinfo
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
            raise ValueError("Gmail access token missing or invalid")

        # Mock responses if using mock credentials
        if access_token.startswith("mock_"):
            return self._execute_mock(tool_name, arguments)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            if tool_name == "gmail_search_emails":
                query = arguments.get("query", "")
                max_results = min(int(arguments.get("max_results", 5)), 20)
                resp = await client.get(
                    f"{GMAIL_API_BASE}/messages",
                    headers=headers,
                    params={"q": query, "maxResults": max_results},
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"Gmail search failed ({resp.status_code}): {resp.text}")
                data = resp.json()
                messages = data.get("messages", [])
                
                # Fetch snippets
                results = []
                for m in messages[:max_results]:
                    m_resp = await client.get(
                        f"{GMAIL_API_BASE}/messages/{m['id']}",
                        headers=headers,
                        params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
                    )
                    if m_resp.status_code == 200:
                        m_data = m_resp.json()
                        headers_map = {h["name"]: h["value"] for h in m_data.get("payload", {}).get("headers", [])}
                        results.append({
                            "id": m["id"],
                            "thread_id": m.get("threadId"),
                            "snippet": m_data.get("snippet", ""),
                            "subject": headers_map.get("Subject", "No Subject"),
                            "from": headers_map.get("From", "Unknown"),
                            "date": headers_map.get("Date", ""),
                        })
                return {
                    "query": query,
                    "count": len(results),
                    "emails": results,
                }

            elif tool_name == "gmail_read_email":
                msg_id = arguments.get("message_id")
                resp = await client.get(
                    f"{GMAIL_API_BASE}/messages/{msg_id}",
                    headers=headers,
                    params={"format": "full"},
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"Failed to read email {msg_id}: {resp.text}")
                data = resp.json()
                headers_map = {h["name"]: h["value"] for h in data.get("payload", {}).get("headers", [])}
                
                # Extract text body if present
                snippet = data.get("snippet", "")
                return {
                    "id": msg_id,
                    "subject": headers_map.get("Subject", "No Subject"),
                    "from": headers_map.get("From", "Unknown"),
                    "to": headers_map.get("To", "Unknown"),
                    "date": headers_map.get("Date", ""),
                    "snippet": snippet,
                    "labels": data.get("labelIds", []),
                }

            elif tool_name == "gmail_create_draft":
                to_addr = arguments.get("to")
                subject = arguments.get("subject", "")
                body = arguments.get("body", "")

                message_text = f"To: {to_addr}\r\nSubject: {subject}\r\n\r\n{body}"
                encoded_message = base64.urlsafe_b64encode(message_text.encode("utf-8")).decode("utf-8")

                resp = await client.post(
                    f"{GMAIL_API_BASE}/drafts",
                    headers=headers,
                    json={"message": {"raw": encoded_message}},
                )
                if resp.status_code not in (200, 201):
                    raise RuntimeError(f"Failed to create draft: {resp.text}")
                draft = resp.json()
                return {
                    "status": "success",
                    "draft_id": draft.get("id"),
                    "message_id": draft.get("message", {}).get("id"),
                    "to": to_addr,
                    "subject": subject,
                }

            elif tool_name == "gmail_send_email":
                to_addr = arguments.get("to")
                subject = arguments.get("subject", "")
                body = arguments.get("body", "")

                message_text = f"To: {to_addr}\r\nSubject: {subject}\r\n\r\n{body}"
                encoded_message = base64.urlsafe_b64encode(message_text.encode("utf-8")).decode("utf-8")

                resp = await client.post(
                    f"{GMAIL_API_BASE}/messages/send",
                    headers=headers,
                    json={"raw": encoded_message},
                )
                if resp.status_code not in (200, 201):
                    raise RuntimeError(f"Failed to send email: {resp.text}")
                sent = resp.json()
                return {
                    "status": "sent",
                    "message_id": sent.get("id"),
                    "thread_id": sent.get("threadId"),
                    "to": to_addr,
                    "subject": subject,
                }

            else:
                raise ValueError(f"Unknown Gmail tool: '{tool_name}'")

    def _execute_mock(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Deterministic mock results for testing without external network calls."""
        if tool_name == "gmail_search_emails":
            q = arguments.get("query", "")
            return {
                "query": q,
                "count": 2,
                "emails": [
                    {
                        "id": "mock_msg_001",
                        "subject": "TN MSME Subsidy Application Approval Notice",
                        "from": "noreply@msmeonline.tn.gov.in",
                        "date": "Mon, 23 Nov 2026 09:15:00 +0530",
                        "snippet": "Your UYEGP subsidy claim of Rs 2,50,000 has been reviewed and verified...",
                    },
                    {
                        "id": "mock_msg_002",
                        "subject": "Startup India Seed Fund Follow-up",
                        "from": "team@startupindia.gov.in",
                        "date": "Sun, 22 Nov 2026 14:30:00 +0530",
                        "snippet": "Please submit your audited financial projections for TANSEED Phase 2...",
                    },
                ],
            }
        elif tool_name == "gmail_read_email":
            msg_id = arguments.get("message_id", "mock_msg_001")
            return {
                "id": msg_id,
                "subject": "TN MSME Subsidy Application Approval Notice",
                "from": "noreply@msmeonline.tn.gov.in",
                "to": "founder@illusion.ai",
                "date": "Mon, 23 Nov 2026 09:15:00 +0530",
                "snippet": "Your UYEGP subsidy claim of Rs 2,50,000 has been reviewed and verified...",
                "body": "Dear Entrepreneur,\n\nWe are pleased to inform you that your subsidy claim under the Unemployed Youth Employment Generation Programme (UYEGP) has been provisionally sanctioned by the District Industries Centre (DIC). Please carry your original documents for physical verification.\n\nRegards,\nDIC Team",
                "labels": ["INBOX", "IMPORTANT"],
            }
        elif tool_name == "gmail_create_draft":
            return {
                "status": "success",
                "draft_id": f"draft_{uuid.uuid4().hex[:8]}",
                "to": arguments.get("to"),
                "subject": arguments.get("subject"),
                "message": "Draft created successfully in your Gmail inbox.",
            }
        elif tool_name == "gmail_send_email":
            return {
                "status": "sent",
                "message_id": f"sent_{uuid.uuid4().hex[:8]}",
                "to": arguments.get("to"),
                "subject": arguments.get("subject"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"Email successfully sent to {arguments.get('to')}.",
            }
        raise ValueError(f"Unknown Gmail tool: '{tool_name}'")

    async def revoke(self, credentials: Dict[str, Any]) -> bool:
        token = credentials.get("access_token")
        if not token:
            return True
        if token.startswith("mock_"):
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
            logger.warning(f"Failed to revoke Google token with provider: {e}")
            return False
