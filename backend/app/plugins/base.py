"""Abstract Base Class for Marketplace Plugins in Illusion AI."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from app.plugins.schemas import PluginToolDefinition, PermissionLevel


class BasePlugin(ABC):
    """Abstract interface for all Illusion AI marketplace integrations."""

    def __init__(
        self,
        plugin_id: str,
        name: str,
        display_name: str,
        description: str,
        category: str,
        icon: str,
        auth_type: str = "oauth2",
        scopes: Optional[List[str]] = None,
        features: Optional[List[str]] = None,
    ):
        self.plugin_id = plugin_id
        self.name = name
        self.display_name = display_name
        self.description = description
        self.category = category
        self.icon = icon
        self.auth_type = auth_type
        self.scopes = scopes or []
        self.features = features or []

    @abstractmethod
    def get_tools(self) -> List[PluginToolDefinition]:
        """Return list of tools exposed by this plugin."""
        pass

    @abstractmethod
    def get_auth_url(self, user_id: str, redirect_uri: str) -> Tuple[str, str]:
        """Generate OAuth authorization URL and state token.
        
        Returns:
            Tuple[str, str]: (authorization_url, state)
        """
        pass

    @abstractmethod
    async def exchange_code(self, code: str, redirect_uri: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Exchange authorization code for credentials and account profile.
        
        Returns:
            Dict containing:
            - access_token: str
            - refresh_token: Optional[str]
            - expires_at: Optional[str]
            - account_id: Optional[str]
            - account_email: Optional[str]
            - account_username: Optional[str]
            - avatar_url: Optional[str]
            - scopes: List[str]
        """
        pass

    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        credentials: Dict[str, Any],
    ) -> Any:
        """Execute a tool exposed by this plugin using decrypted credentials."""
        pass

    @abstractmethod
    async def revoke(self, credentials: Dict[str, Any]) -> bool:
        """Revoke token or disconnect connection with remote provider."""
        pass
