"""Base plugin implementation for LLM framework integrations."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

import structlog

from prompt_manager.core.models import Prompt
from prompt_manager.exceptions import PluginError

logger = structlog.get_logger(__name__)


class BasePlugin(ABC):
    """
    Base class for LLM framework plugins.

    Plugins enable rendering prompts in framework-specific formats
    for OpenAI, Anthropic, LangChain, LiteLLM, etc.
    """

    def __init__(self, name: str, version: str) -> None:
        """
        Initialize base plugin.

        Args:
            name: Plugin name (e.g., "openai", "anthropic")
            version: Plugin version
        """
        self.name = name
        self.version = version
        self._config: dict[str, Any] = {}
        self._initialized = False
        self._logger = logger.bind(plugin=name)

    def initialize(self, config: Mapping[str, Any]) -> None:
        """
        Initialize the plugin with configuration.

        Args:
            config: Plugin configuration

        Raises:
            PluginError: If initialization fails
        """
        self._logger.info("initializing_plugin", config=dict(config))

        try:
            self._config = dict(config)
            self._initialize_impl(config)
            self._initialized = True

            self._logger.info("plugin_initialized")

        except Exception as e:
            msg = f"Failed to initialize plugin {self.name}: {e}"
            raise PluginError(msg) from e

    @abstractmethod
    def _initialize_impl(self, config: Mapping[str, Any]) -> None:
        """
        Plugin-specific initialization logic.

        Args:
            config: Plugin configuration
        """
        ...

    @abstractmethod
    def render_for_framework(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> Any:
        """
        Render prompt in framework-specific format.

        Args:
            prompt: Prompt to render
            variables: Variables for rendering

        Returns:
            Framework-specific prompt format

        Raises:
            PluginError: If rendering fails
        """
        ...

    @abstractmethod
    def validate_compatibility(self, prompt: Prompt) -> bool:
        """
        Check if prompt is compatible with framework.

        Args:
            prompt: Prompt to check

        Returns:
            True if compatible

        Raises:
            PluginError: If validation fails
        """
        ...

    def shutdown(self) -> None:
        """Clean up plugin resources."""
        self._logger.info("shutting_down_plugin")
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Ensure plugin is initialized before use."""
        if not self._initialized:
            msg = f"Plugin {self.name} not initialized"
            raise PluginError(msg)

    def get_config(self) -> dict[str, Any]:
        """Get plugin configuration."""
        return self._config.copy()

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.name!r}, version={self.version!r})"
