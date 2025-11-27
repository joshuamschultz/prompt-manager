"""OpenAI plugin for Prompt Manager.

Provides plugin interface for OpenAI SDK integration, enabling
prompt rendering in OpenAI-compatible format.
"""

from collections.abc import Mapping
from typing import Any

from prompt_manager.core.models import Prompt
from prompt_manager.core.template import TemplateEngine
from prompt_manager.exceptions import PluginError
from prompt_manager.integrations.openai import OpenAIIntegration
from prompt_manager.integrations.types import OpenAIMessage
from prompt_manager.plugins.base import BasePlugin


class OpenAIPlugin(BasePlugin):
    """Plugin for OpenAI SDK integration.

    Converts Prompt Manager prompts to OpenAI message format using the
    OpenAIIntegration class.

    Example:
        >>> plugin = OpenAIPlugin()
        >>> await plugin.initialize({})
        >>> result = await plugin.render_for_framework(prompt, variables)
        >>> # result: list[OpenAIMessage] | str

    Reference:
        https://platform.openai.com/docs/api-reference/chat/create
    """

    def __init__(self) -> None:
        """Initialize OpenAI plugin."""
        super().__init__(name="openai", version="1.0.0")
        self._integration: OpenAIIntegration | None = None

    def _initialize_impl(self, config: Mapping[str, Any]) -> None:
        """Initialize OpenAI integration.

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
            self._integration = OpenAIIntegration(
                template_engine=template_engine,
                strict_validation=strict_validation,
            )

            self._logger.info(
                "openai_integration_initialized",
                strict_validation=strict_validation,
            )

        except Exception as e:
            msg = f"Failed to initialize OpenAI integration: {e}"
            raise PluginError(msg) from e

    def render_for_framework(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> list[OpenAIMessage] | str:
        """Render prompt in OpenAI format.

        Args:
            prompt: Prompt to render
            variables: Variables for template substitution

        Returns:
            - For CHAT format: List of OpenAI message dictionaries
            - For TEXT format: Rendered string

        Raises:
            PluginError: If plugin not initialized
            ConversionError: If conversion fails

        Example:
            >>> messages = await plugin.render_for_framework(
            ...     chat_prompt,
            ...     {"user": "Alice"}
            ... )
            >>> # messages: [{"role": "system", "content": "..."}, ...]
        """
        self._ensure_initialized()

        if self._integration is None:
            msg = "Integration not initialized"
            raise PluginError(msg)

        # Delegate to integration
        return self._integration.convert(prompt, variables)

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if prompt is compatible with OpenAI.

        OpenAI supports all prompt formats (TEXT and CHAT).

        Args:
            prompt: Prompt to validate

        Returns:
            True (OpenAI supports all formats)

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
