"""Anthropic plugin for Prompt Manager."""

from collections.abc import Mapping
from typing import Any

from prompt_manager.core.models import Prompt
from prompt_manager.core.template import TemplateEngine
from prompt_manager.exceptions import PluginError
from prompt_manager.integrations.anthropic import AnthropicIntegration
from prompt_manager.plugins.base import BasePlugin


class AnthropicPlugin(BasePlugin):
    """Plugin for Anthropic SDK integration.

    Provides integration with Anthropic's Messages API, converting
    Prompt Manager prompts to Anthropic's format.

    Example:
        >>> plugin = AnthropicPlugin()
        >>> await plugin.initialize({})
        >>> result = await plugin.render_for_framework(prompt, variables)
        >>> # result: {"system": "...", "messages": [...]}
    """

    def __init__(self) -> None:
        """Initialize the Anthropic plugin."""
        super().__init__(name="anthropic", version="1.0.0")
        self._integration: AnthropicIntegration | None = None

    def _initialize_impl(self, config: Mapping[str, Any]) -> None:
        """Initialize Anthropic integration.

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
            self._integration = AnthropicIntegration(
                template_engine=template_engine,
                strict_validation=strict_validation,
            )

        except Exception as e:
            msg = f"Failed to initialize Anthropic integration: {e}"
            raise PluginError(msg) from e

    def render_for_framework(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> Any:
        """Render prompt in Anthropic Messages API format.

        Args:
            prompt: The prompt to render (must be CHAT format)
            variables: Variables for template substitution

        Returns:
            Dictionary with "messages" array and optional "system" field

        Raises:
            PluginError: If plugin not initialized
            IncompatibleFormatError: If prompt is not CHAT format
            ConversionError: If conversion fails

        Example:
            >>> result = await plugin.render_for_framework(
            ...     chat_prompt,
            ...     {"topic": "AI"}
            ... )
            >>> # result: {"system": "...", "messages": [...]}
        """
        self._ensure_initialized()

        if self._integration is None:
            msg = "Integration not initialized"
            raise PluginError(msg)

        # Delegate to integration
        return self._integration.convert(prompt, variables)

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if prompt is compatible with Anthropic.

        Args:
            prompt: The prompt to validate

        Returns:
            True if prompt is CHAT format, False otherwise

        Raises:
            PluginError: If plugin not initialized

        Example:
            >>> is_compatible = await plugin.validate_compatibility(chat_prompt)
            >>> # is_compatible: True
        """
        self._ensure_initialized()

        if self._integration is None:
            msg = "Integration not initialized"
            raise PluginError(msg)

        # Delegate to integration
        return self._integration.validate_compatibility(prompt)
