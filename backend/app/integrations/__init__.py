"""Integrations package for Illusion AI Plugin Marketplace."""

from app.integrations.gmail import GmailPlugin
from app.integrations.github import GitHubPlugin
from app.integrations.google_calendar import GoogleCalendarPlugin

__all__ = ["GmailPlugin", "GitHubPlugin", "GoogleCalendarPlugin"]
