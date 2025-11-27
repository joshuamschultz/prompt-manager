"""LiteLLM integration for Prompt Manager.

This module provides integration with LiteLLM, which uses OpenAI-compatible
format across multiple LLM providers.
"""

from typing import Any, Mapping

from prompt_manager.core.models import Prompt
from prompt_manager.integrations.base import BaseIntegration
from prompt_manager.integrations.openai import OpenAIIntegration
from prompt_manager.integrations.types import OpenAIMessage


class LiteLLMIntegration(BaseIntegration[list[OpenAIMessage] | str]):
    """Integration for LiteLLM using OpenAI-compatible format.

    LiteLLM provides a unified interface to multiple LLM providers using
    OpenAI's message format as the standard. This integration delegates
    to OpenAIIntegration since the formats are identical.

    Supported Providers (via LiteLLM):
        - OpenAI (GPT-3.5, GPT-4)
        - Anthropic (Claude via OpenAI format)
        - Google (PaLM, Gemini)
        - Cohere
        - Hugging Face
        - And many more...

    Example:
        >>> from prompt_manager.core.template import TemplateEngine
        >>> engine = TemplateEngine()
        >>> integration = LiteLLMIntegration(engine)
        >>>
        >>> # Works with any prompt format
        >>> result = integration.convert(prompt, {"name": "Alice"})
        >>> # Can be used with any LiteLLM-supported provider

    Reference:
        https://docs.litellm.ai/docs/
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with OpenAI integration for delegation.

        Args:
            *args: Positional arguments passed to BaseIntegration
            **kwargs: Keyword arguments passed to BaseIntegration
        """
        super().__init__(*args, **kwargs)
        # Create OpenAI integration for delegation
        self._openai_integration = OpenAIIntegration(
            template_engine=self._template_engine,
            strict_validation=self._strict_validation,
        )

    def convert(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> list[OpenAIMessage] | str:
        """Convert a prompt to LiteLLM format (OpenAI-compatible).

        Delegates to OpenAIIntegration since LiteLLM uses the same format.

        Args:
            prompt: The prompt to convert
            variables: Variables for template substitution

        Returns:
            For TEXT format: Rendered string
            For CHAT format: List of OpenAI-compatible message dictionaries

        Raises:
            ConversionError: If conversion fails
            IntegrationError: If prompt format is not supported

        Example:
            >>> result = integration.convert(prompt, {"user": "Alice"})
        """
        # Delegate to OpenAI integration
        return self._openai_integration.convert(prompt, variables)

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if prompt is compatible with LiteLLM.

        LiteLLM supports all formats (delegates to OpenAI).

        Args:
            prompt: The prompt to validate

        Returns:
            True (LiteLLM supports all formats via OpenAI compatibility)

        Example:
            >>> integration.validate_compatibility(any_prompt)
            True
        """
        # LiteLLM supports all formats via OpenAI compatibility
        return self._openai_integration.validate_compatibility(prompt)
