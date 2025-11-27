"""LangChain plugin for Prompt Manager."""

from collections.abc import Mapping
from typing import Any

from prompt_manager.core.models import Prompt
from prompt_manager.core.template import TemplateEngine
from prompt_manager.exceptions import IntegrationNotAvailableError, PluginError
from prompt_manager.plugins.base import BasePlugin


class LangChainPlugin(BasePlugin):
    """Plugin for LangChain integration.

    Provides integration with LangChain's prompt templates, converting
    Prompt Manager prompts to LangChain format.

    Note:
        Requires langchain-core to be installed. Install with:
        pip install agentic-prompt-manager[langchain]

    Example:
        >>> plugin = LangChainPlugin()
        >>> await plugin.initialize({})
        >>> lc_template = await plugin.render_for_framework(prompt, variables)
        >>> # lc_template: PromptTemplate or ChatPromptTemplate
    """

    def __init__(self) -> None:
        """Initialize the LangChain plugin."""
        super().__init__(name="langchain", version="1.0.0")
        self._integration: Any = None

    def _initialize_impl(self, config: Mapping[str, Any]) -> None:
        """Initialize LangChain integration.

        Args:
            config: Plugin configuration. Supported keys:
                - strict_validation (bool): Enable strict validation mode

        Raises:
            IntegrationNotAvailableError: If langchain-core not installed
            PluginError: If initialization fails
        """
        # Import here to avoid requiring langchain for plugin discovery
        try:
            from prompt_manager.integrations.langchain import LangChainIntegration

            # Create template engine
            template_engine = TemplateEngine()

            # Get strict validation setting (default True)
            strict_validation = config.get("strict_validation", True)

            # Create integration
            self._integration = LangChainIntegration(
                template_engine=template_engine,
                strict_validation=strict_validation,
            )

        except IntegrationNotAvailableError:
            # Re-raise IntegrationNotAvailableError as-is
            raise
        except Exception as e:
            msg = f"Failed to initialize LangChain integration: {e}"
            raise PluginError(msg) from e

    def render_for_framework(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> Any:
        """Render prompt in LangChain template format.

        Args:
            prompt: The prompt to render
            variables: Variables for template substitution

        Returns:
            For TEXT format: PromptTemplate
            For CHAT format: ChatPromptTemplate

        Raises:
            PluginError: If plugin not initialized
            ConversionError: If conversion fails

        Example:
            >>> lc_template = await plugin.render_for_framework(
            ...     prompt,
            ...     {"name": "Alice"}
            ... )
            >>> # lc_template: PromptTemplate or ChatPromptTemplate
        """
        self._ensure_initialized()

        if self._integration is None:
            msg = "Integration not initialized"
            raise PluginError(msg)

        # Delegate to integration
        return self._integration.convert(prompt, variables)

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if prompt is compatible with LangChain.

        Args:
            prompt: The prompt to validate

        Returns:
            True if prompt is TEXT or CHAT format

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
        return self._integration.validate_compatibility(prompt)  # type: ignore[no-any-return]
