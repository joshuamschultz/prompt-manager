"""OpenAI SDK integration for Prompt Manager.

This module provides integration with the OpenAI Python SDK, converting
Prompt Manager prompts to OpenAI's message format.
"""

from typing import Any, Mapping

from prompt_manager.core.models import Prompt, PromptFormat, Role
from prompt_manager.exceptions import ConversionError, IntegrationError
from prompt_manager.integrations.base import BaseIntegration
from prompt_manager.integrations.types import OpenAIMessage


class OpenAIIntegration(BaseIntegration[list[OpenAIMessage] | str]):
    """Integration for converting prompts to OpenAI SDK format.

    Converts Prompt Manager prompts to the format expected by OpenAI's
    Chat Completions API. Supports both TEXT and CHAT formats.

    Output Formats:
        - TEXT prompts: Returns rendered string
        - CHAT prompts: Returns list of OpenAI message dictionaries

    Example:
        >>> from prompt_manager.core.template import TemplateEngine
        >>> engine = TemplateEngine()
        >>> integration = OpenAIIntegration(engine)
        >>>
        >>> # TEXT format
        >>> prompt = Prompt(id="simple", format=PromptFormat.TEXT, ...)
        >>> result = integration.convert(prompt, {"name": "Alice"})
        >>> # result: "Hello Alice!"
        >>>
        >>> # CHAT format
        >>> chat_prompt = Prompt(id="chat", format=PromptFormat.CHAT, ...)
        >>> messages = integration.convert(chat_prompt, {})
        >>> # messages: [{"role": "system", "content": "..."}, ...]

    Reference:
        https://platform.openai.com/docs/api-reference/chat/create
    """

    def convert(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> list[OpenAIMessage] | str:
        """Convert a prompt to OpenAI format.

        Args:
            prompt: The prompt to convert
            variables: Variables for template substitution

        Returns:
            For TEXT format: Rendered string
            For CHAT format: List of OpenAI message dictionaries

        Raises:
            ConversionError: If conversion fails
            IntegrationError: If prompt format is not supported

        Example:
            >>> result = integration.convert(prompt, {"user": "Alice"})
        """
        if prompt.format == PromptFormat.CHAT:
            return self._convert_chat(prompt, variables)
        elif prompt.format == PromptFormat.TEXT:
            return self._convert_text(prompt, variables)
        else:
            raise ConversionError(
                f"Unsupported prompt format: {prompt.format}",
                prompt_id=prompt.id,
                framework="openai",
            )

    def _convert_chat(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> list[OpenAIMessage]:
        """Convert CHAT format prompt to OpenAI messages.

        Args:
            prompt: The CHAT format prompt
            variables: Variables for template substitution

        Returns:
            List of OpenAI message dictionaries

        Raises:
            ConversionError: If chat_template is missing or rendering fails
        """
        if not prompt.chat_template:
            raise ConversionError(
                "CHAT format requires chat_template",
                prompt_id=prompt.id,
                framework="openai",
            )

        messages: list[OpenAIMessage] = []

        try:
            for message in prompt.chat_template.messages:
                # Render message content
                rendered_content = self._template_engine.render(
                    message.content,
                    variables,
                )

                # Build OpenAI message
                openai_message: OpenAIMessage = {
                    "role": self._map_role(message.role),
                    "content": str(rendered_content),
                }

                # Add optional name field
                if message.name:
                    openai_message["name"] = message.name

                messages.append(openai_message)

        except Exception as e:
            raise ConversionError(
                f"Failed to render chat template: {e}",
                prompt_id=prompt.id,
                framework="openai",
                cause=e,
            ) from e

        return messages

    def _convert_text(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> str:
        """Convert TEXT format prompt to string.

        Args:
            prompt: The TEXT format prompt
            variables: Variables for template substitution

        Returns:
            Rendered string content

        Raises:
            ConversionError: If template is missing or rendering fails
        """
        if not prompt.template:
            raise ConversionError(
                "TEXT format requires template",
                prompt_id=prompt.id,
                framework="openai",
            )

        try:
            rendered = self._template_engine.render(
                prompt.template.content,
                variables,
            )
            return str(rendered)

        except Exception as e:
            raise ConversionError(
                f"Failed to render text template: {e}",
                prompt_id=prompt.id,
                framework="openai",
                cause=e,
            ) from e

    def _map_role(self, role: Role) -> str:
        """Map Prompt Manager role to OpenAI role string.

        Args:
            role: The Prompt Manager role enum value

        Returns:
            OpenAI role string

        Role Mapping:
            - Role.SYSTEM → "system"
            - Role.USER → "user"
            - Role.ASSISTANT → "assistant"
            - Role.FUNCTION → "function"
            - Role.TOOL → "tool"

        Example:
            >>> integration._map_role(Role.USER)
            "user"
        """
        role_mapping = {
            Role.SYSTEM: "system",
            Role.USER: "user",
            Role.ASSISTANT: "assistant",
            Role.FUNCTION: "function",
            Role.TOOL: "tool",
        }
        return role_mapping[role]

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if prompt is compatible with OpenAI.

        OpenAI supports all prompt formats (TEXT and CHAT).

        Args:
            prompt: The prompt to validate

        Returns:
            True (OpenAI supports all formats)

        Example:
            >>> integration.validate_compatibility(any_prompt)
            True
        """
        # OpenAI supports all formats
        return True
