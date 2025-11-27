"""Base integration class for framework adapters.

This module provides the abstract base class that all framework integrations
must implement. It defines the protocol for converting Prompt Manager prompts
into framework-specific formats.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Mapping, TypeVar

from prompt_manager.core.models import Prompt
from prompt_manager.core.protocols import TemplateEngineProtocol

# Type variable for the framework-specific output format
T = TypeVar("T")


class BaseIntegration(ABC, Generic[T]):
    """Abstract base class for framework integrations.

    Integrations convert Prompt Manager prompts into framework-specific formats.
    Each integration is generic over the output type T, which is the native
    format expected by the target framework.

    Type Parameters:
        T: The framework-specific format type. Examples:
           - list[dict[str, Any]] for OpenAI messages
           - dict[str, Any] for Anthropic requests
           - PromptTemplate for LangChain templates

    Attributes:
        template_engine: Template engine for variable substitution
        strict_validation: Whether to enforce strict format compatibility checks

    Example:
        >>> class OpenAIIntegration(BaseIntegration[list[dict[str, Any]]]):
        ...     def convert(self, prompt, variables):
        ...         # Convert to OpenAI message format
        ...         return [{"role": "user", "content": rendered}]
        ...
        ...     def validate_compatibility(self, prompt):
        ...         return True  # OpenAI supports all formats

    Notes:
        - Conversion should be idempotent (same inputs = same outputs)
        - Validation should be fast (it may be called frequently)
    """

    def __init__(
        self,
        template_engine: TemplateEngineProtocol,
        strict_validation: bool = True,
    ) -> None:
        """Initialize the integration.

        Args:
            template_engine: Template engine for rendering prompt content.
                Used to substitute variables in prompt templates before
                converting to framework format.
            strict_validation: Whether to enforce strict compatibility checks.
                When True, raises IncompatibleFormatError if prompt format
                is not supported. When False, attempts best-effort conversion.
                Defaults to True for safety.

        Example:
            >>> from prompt_manager.core.template import HandlebarsEngine
            >>> engine = HandlebarsEngine()
            >>> integration = OpenAIIntegration(
            ...     template_engine=engine,
            ...     strict_validation=True
            ... )
        """
        self._template_engine = template_engine
        self._strict_validation = strict_validation

    @abstractmethod
    def convert(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> T:
        """Convert a prompt to framework-specific format.

        This method performs the core conversion logic, transforming a
        Prompt Manager prompt into the native format expected by the
        target framework.

        Args:
            prompt: The prompt to convert. Contains template, format,
                metadata, and other configuration.
            variables: Variables to substitute in the template. Must contain
                all required variables defined in the prompt template.

        Returns:
            The framework-specific format. Type depends on the integration:
            - OpenAI: list[dict[str, Any]] (message array)
            - Anthropic: dict[str, Any] (request payload)
            - LangChain: PromptTemplate or ChatPromptTemplate

        Raises:
            ConversionError: If conversion fails due to invalid prompt structure
                or variable substitution errors.
            IncompatibleFormatError: If strict_validation=True and the prompt
                format is not supported by the framework.
            IntegrationError: For other integration-specific errors.

        Example:
            >>> prompt = Prompt(
            ...     id="greeting",
            ...     format=PromptFormat.TEXT,
            ...     template=PromptTemplate(content="Hello {{name}}!")
            ... )
            >>> result = integration.convert(
            ...     prompt,
            ...     {"name": "Alice"}
            ... )
            >>> # For OpenAI: result = "Hello Alice!"
            >>> # For LangChain: result = PromptTemplate(...)

        Notes:
            - Must handle variable substitution using template_engine
            - Should validate prompt format if strict_validation=True
            - Should preserve metadata when framework supports it
            - Must be idempotent and thread-safe
        """
        raise NotImplementedError

    @abstractmethod
    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if a prompt is compatible with this integration.

        This method performs a fast check to determine if the prompt format
        and structure can be converted to the target framework format.

        Args:
            prompt: The prompt to validate

        Returns:
            True if the prompt can be converted to the framework format,
            False otherwise.

        Example:
            >>> prompt = Prompt(format=PromptFormat.TEXT, ...)
            >>> openai_integration.validate_compatibility(prompt)
            True
            >>> anthropic_integration.validate_compatibility(prompt)
            False  # Anthropic requires CHAT format

        Notes:
            - This should be a fast check (no network calls)
            - Used for routing prompts to appropriate integrations
            - Should not raise exceptions (return False instead)
            - May check: format type, template structure, metadata requirements
        """
        raise NotImplementedError

    @property
    def template_engine(self) -> TemplateEngineProtocol:
        """Get the template engine used for rendering.

        Returns:
            The template engine instance for variable substitution
        """
        return self._template_engine

    @property
    def strict_validation(self) -> bool:
        """Get the strict validation mode.

        Returns:
            True if strict validation is enabled, False otherwise
        """
        return self._strict_validation
