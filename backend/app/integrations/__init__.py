"""Integrations package for Illusion AI Plugin Marketplace."""

from app.integrations.gmail import GmailPlugin
from app.integrations.github import GitHubPlugin

__all__ = ["GmailPlugin", "GitHubPlugin"]
