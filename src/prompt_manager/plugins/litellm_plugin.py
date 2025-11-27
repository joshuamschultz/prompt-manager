"""LiteLLM plugin for Prompt Manager."""

from collections.abc import Mapping
from typing import Any

from prompt_manager.core.models import Prompt
from prompt_manager.core.template import TemplateEngine
from prompt_manager.exceptions import PluginError
from prompt_manager.integrations.litellm import LiteLLMIntegration
from prompt_manager.plugins.base import BasePlugin


class LiteLLMPlugin(BasePlugin):
    """Plugin for LiteLLM integration.

    Provides integration with LiteLLM, which uses OpenAI-compatible format
    across multiple LLM providers.

    Example:
        >>> plugin = LiteLLMPlugin()
        >>> await plugin.initialize({})
        >>> result = await plugin.render_for_framework(prompt, variables)
        >>> # result: OpenAI-compatible format (string or message list)
    """

    def __init__(self) -> None:
        """Initialize the LiteLLM plugin."""
        super().__init__(name="litellm", version="1.0.0")
        self._integration: LiteLLMIntegration | None = None

    def _initialize_impl(self, config: Mapping[str, Any]) -> None:
        """Initialize LiteLLM integration.

        Args:
            config: Plugin configuration. Supported keys:
                - strict_validation (bool): Enable strict validation mode

        Raises:
            PluginError: If initialization fails
        """
        try:
            # Create template engine
            template_engine = TemplateEngine()

            # Get strict validation setting (default True)
            strict_validation = config.get("strict_validation", True)

            # Create integration
            self._integration = LiteLLMIntegration(
                template_engine=template_engine,
                strict_validation=strict_validation,
            )

        except Exception as e:
            msg = f"Failed to initialize LiteLLM integration: {e}"
            raise PluginError(msg) from e

    def render_for_framework(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> Any:
        """Render prompt in LiteLLM (OpenAI-compatible) format.

        Args:
            prompt: The prompt to render
            variables: Variables for template substitution

        Returns:
            For TEXT format: Rendered string
            For CHAT format: List of OpenAI-compatible message dictionaries

        Raises:
            PluginError: If plugin not initialized
            ConversionError: If conversion fails

        Example:
            >>> result = await plugin.render_for_framework(
            ...     prompt,
            ...     {"name": "Alice"}
            ... )
            >>> # result: str or list[dict]
        """
        self._ensure_initialized()

        if self._integration is None:
            msg = "Integration not initialized"
            raise PluginError(msg)

        # Delegate to integration
        return self._integration.convert(prompt, variables)

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if prompt is compatible with LiteLLM.

        Args:
            prompt: The prompt to validate

        Returns:
            True (LiteLLM supports all formats)

        Raises:
            PluginError: If plugin not initialized

        Example:
            >>> is_compatible = await plugin.validate_compatibility(prompt)
            >>> # is_compatible: True
        """
        self._ensure_initialized()

        if self._integration is None:
            msg = "Integration not initialized"
            raise PluginError(msg)

        # Delegate to integration
        return self._integration.validate_compatibility(prompt)
