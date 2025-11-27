"""LangChain integration for Prompt Manager.

This module provides integration with LangChain's prompt templates, converting
Prompt Manager prompts to LangChain's template format.
"""

import re
from typing import Any, Mapping

from prompt_manager.core.models import Prompt, PromptFormat, Role
from prompt_manager.exceptions import IntegrationNotAvailableError, ConversionError
from prompt_manager.integrations.base import BaseIntegration

# Try to import LangChain dependencies
try:
    from langchain_core.prompts import (
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        PromptTemplate,
        SystemMessagePromptTemplate,
    )

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Define placeholder types for type checking
    ChatPromptTemplate = Any  # type: ignore[misc, assignment]
    PromptTemplate = Any  # type: ignore[misc, assignment]
    HumanMessagePromptTemplate = Any  # type: ignore[misc, assignment]
    SystemMessagePromptTemplate = Any  # type: ignore[misc, assignment]


class LangChainIntegration(BaseIntegration[Any]):
    """Integration for converting prompts to LangChain template format.

    Converts Prompt Manager prompts to LangChain's PromptTemplate or
    ChatPromptTemplate format. Requires langchain-core to be installed.

    Key Conversions:
        - Handlebars {{variable}} → f-string {variable}
        - TEXT format → PromptTemplate
        - CHAT format → ChatPromptTemplate
        - Role.SYSTEM → SystemMessagePromptTemplate
        - Role.USER → HumanMessagePromptTemplate

    Example:
        >>> from prompt_manager.core.template import TemplateEngine
        >>> engine = TemplateEngine()
        >>> integration = LangChainIntegration(engine)
        >>>
        >>> # TEXT format
        >>> text_prompt = Prompt(id="simple", format=PromptFormat.TEXT, ...)
        >>> lc_template = integration.convert(text_prompt, {})
        >>> # Returns: PromptTemplate(input_variables=[...], template="...")
        >>>
        >>> # CHAT format
        >>> chat_prompt = Prompt(id="chat", format=PromptFormat.CHAT, ...)
        >>> lc_chat = integration.convert(chat_prompt, {})
        >>> # Returns: ChatPromptTemplate(...)

    Reference:
        https://python.langchain.com/docs/modules/model_io/prompts/
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with dependency check.

        Raises:
            IntegrationNotAvailableError: If langchain-core is not installed
        """
        if not LANGCHAIN_AVAILABLE:
            raise IntegrationNotAvailableError(
                integration_name="langchain",
                extra="langchain",
            )
        super().__init__(*args, **kwargs)

    def convert(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> PromptTemplate | ChatPromptTemplate:
        """Convert a prompt to LangChain template format.

        Args:
            prompt: The prompt to convert
            variables: Variables for template substitution (not used for conversion,
                      but kept for interface compatibility)

        Returns:
            For TEXT format: PromptTemplate
            For CHAT format: ChatPromptTemplate

        Raises:
            ConversionError: If conversion fails
            IntegrationNotAvailableError: If langchain-core not installed

        Example:
            >>> lc_template = integration.convert(prompt, {})
            >>> # Use with LangChain: result = lc_template.format(**variables)
        """
        if prompt.format == PromptFormat.CHAT:
            return self._convert_chat(prompt)
        else:
            return self._convert_text(prompt)

    def _convert_chat(self, prompt: Prompt) -> ChatPromptTemplate:
        """Convert CHAT format to ChatPromptTemplate.

        Args:
            prompt: The CHAT format prompt

        Returns:
            LangChain ChatPromptTemplate

        Raises:
            ConversionError: If chat_template is missing
        """
        if not prompt.chat_template:
            raise ConversionError(
                "CHAT format requires chat_template",
                prompt_id=prompt.id,
                framework="langchain",
            )

        message_templates = []

        try:
            for msg in prompt.chat_template.messages:
                # Convert Handlebars to f-string format
                content = self._handlebars_to_fstring(msg.content)

                # Map role to appropriate LangChain template
                template: Any
                if msg.role == Role.SYSTEM:
                    template = SystemMessagePromptTemplate.from_template(content)
                elif msg.role == Role.USER:
                    template = HumanMessagePromptTemplate.from_template(content)
                else:
                    # For ASSISTANT, FUNCTION, TOOL roles, use HumanMessage
                    # LangChain doesn't have direct equivalents for all roles
                    template = HumanMessagePromptTemplate.from_template(content)

                message_templates.append(template)

            return ChatPromptTemplate.from_messages(message_templates)

        except Exception as e:
            raise ConversionError(
                f"Failed to create ChatPromptTemplate: {e}",
                prompt_id=prompt.id,
                framework="langchain",
                cause=e,
            ) from e

    def _convert_text(self, prompt: Prompt) -> PromptTemplate:
        """Convert TEXT format to PromptTemplate.

        Args:
            prompt: The TEXT format prompt

        Returns:
            LangChain PromptTemplate

        Raises:
            ConversionError: If template is missing
        """
        if not prompt.template:
            raise ConversionError(
                "TEXT format requires template",
                prompt_id=prompt.id,
                framework="langchain",
            )

        try:
            # Convert Handlebars to f-string
            content = self._handlebars_to_fstring(prompt.template.content)

            # Create PromptTemplate
            return PromptTemplate.from_template(
                content,
                partial_variables=prompt.template.partials or {},
            )

        except Exception as e:
            raise ConversionError(
                f"Failed to create PromptTemplate: {e}",
                prompt_id=prompt.id,
                framework="langchain",
                cause=e,
            ) from e

    def _handlebars_to_fstring(self, template: str) -> str:
        """Convert Handlebars {{variable}} syntax to f-string {variable}.

        This is a simple conversion for basic variable substitution.
        Complex Handlebars features (helpers, conditionals, loops) are not supported.

        Args:
            template: Template string with Handlebars syntax

        Returns:
            Template string with f-string syntax

        Example:
            >>> integration._handlebars_to_fstring("Hello {{name}}!")
            "Hello {name}!"
            >>>
            >>> integration._handlebars_to_fstring("{{greeting}} {{name}}")
            "{greeting} {name}"

        Note:
            Only supports simple variable replacement. Does not handle:
            - Handlebars helpers: {{#if}}, {{#each}}, etc.
            - Nested properties: {{user.name}}
            - Partials: {{> partial}}
        """
        # Replace {{variable}} with {variable}
        # Use word boundaries to match only variable names
        return re.sub(r'\{\{(\w+)\}\}', r'{\1}', template)

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if prompt is compatible with LangChain.

        LangChain supports both TEXT and CHAT formats.

        Args:
            prompt: The prompt to validate

        Returns:
            True if prompt is TEXT or CHAT format

        Example:
            >>> integration.validate_compatibility(text_prompt)
            True
            >>> integration.validate_compatibility(chat_prompt)
            True
        """
        return prompt.format in (PromptFormat.TEXT, PromptFormat.CHAT)
