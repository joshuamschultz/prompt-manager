"""Anthropic SDK integration for Prompt Manager.

This module provides integration with the Anthropic Python SDK, converting
Prompt Manager prompts to Anthropic's Messages API format.
"""

from typing import Any, Mapping

from prompt_manager.core.models import Prompt, PromptFormat, Role
from prompt_manager.exceptions import ConversionError, IncompatibleFormatError
from prompt_manager.integrations.base import BaseIntegration
from prompt_manager.integrations.types import AnthropicMessage, AnthropicRequest


class AnthropicIntegration(BaseIntegration[AnthropicRequest]):
    """Integration for converting prompts to Anthropic Messages API format.

    Converts Prompt Manager CHAT prompts to the format expected by Anthropic's
    Messages API. Only supports CHAT format (not TEXT).

    Key Differences from OpenAI:
        - System messages are separate (not in messages array)
        - Only supports "user" and "assistant" roles
        - Messages must alternate between user and assistant
        - First message must be from user

    Output Format:
        Returns dict with:
        - "messages": List of user/assistant messages
        - "system": System message content (optional)

    Example:
        >>> from prompt_manager.core.template import TemplateEngine
        >>> engine = TemplateEngine()
        >>> integration = AnthropicIntegration(engine)
        >>>
        >>> chat_prompt = Prompt(id="chat", format=PromptFormat.CHAT, ...)
        >>> result = integration.convert(chat_prompt, {})
        >>> # result: {
        >>> #   "system": "You are helpful.",
        >>> #   "messages": [{"role": "user", "content": "..."}]
        >>> # }

    Reference:
        https://docs.anthropic.com/claude/reference/messages_post
    """

    def convert(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> AnthropicRequest:
        """Convert a prompt to Anthropic Messages API format.

        Args:
            prompt: The prompt to convert (must be CHAT format)
            variables: Variables for template substitution

        Returns:
            Dictionary with "messages" array and optional "system" field

        Raises:
            IncompatibleFormatError: If prompt is not CHAT format
            ConversionError: If conversion fails or validation fails

        Example:
            >>> result = integration.convert(prompt, {"user": "Alice"})
            >>> # {"system": "...", "messages": [...]}
        """
        if prompt.format != PromptFormat.CHAT:
            raise IncompatibleFormatError(
                prompt_format=str(prompt.format),
                framework="anthropic",
                supported_formats=["CHAT"],
            )

        if not prompt.chat_template:
            raise ConversionError(
                "CHAT format requires chat_template",
                prompt_id=prompt.id,
                framework="anthropic",
            )

        messages: list[AnthropicMessage] = []
        system_message: str | None = None

        try:
            for message in prompt.chat_template.messages:
                # Render message content
                rendered_content = self._template_engine.render(
                    message.content,
                    variables,
                )

                # Handle system messages separately
                if message.role == Role.SYSTEM:
                    if system_message is not None:
                        raise ConversionError(
                            "Anthropic only supports one system message",
                            prompt_id=prompt.id,
                            framework="anthropic",
                        )
                    system_message = str(rendered_content)
                    continue

                # Build Anthropic message
                anthropic_message: AnthropicMessage = {
                    "role": self._map_role(message.role),
                    "content": str(rendered_content),
                }

                messages.append(anthropic_message)

        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(
                f"Failed to render chat template: {e}",
                prompt_id=prompt.id,
                framework="anthropic",
                cause=e,
            ) from e

        # Validate message alternation (Anthropic requirement)
        self._validate_alternation(messages)

        # Build result
        result: AnthropicRequest = {"messages": messages}
        if system_message:
            result["system"] = system_message

        return result

    def _map_role(self, role: Role) -> str:
        """Map Prompt Manager role to Anthropic role string.

        Anthropic only supports "user" and "assistant" roles.
        FUNCTION and TOOL roles are mapped to "user" since they represent
        tool responses that should be treated as user input.

        Args:
            role: The Prompt Manager role enum value

        Returns:
            Anthropic role string ("user" or "assistant")

        Raises:
            ConversionError: If role cannot be mapped (e.g., SYSTEM)

        Role Mapping:
            - Role.USER → "user"
            - Role.FUNCTION → "user" (tool responses)
            - Role.TOOL → "user" (tool responses)
            - Role.ASSISTANT → "assistant"
            - Role.SYSTEM → Error (must be handled separately)

        Example:
            >>> integration._map_role(Role.USER)
            "user"
            >>> integration._map_role(Role.FUNCTION)
            "user"  # Tool responses treated as user input
        """
        if role in (Role.USER, Role.FUNCTION, Role.TOOL):
            return "user"
        elif role == Role.ASSISTANT:
            return "assistant"
        else:
            raise ConversionError(
                f"Unsupported role for Anthropic: {role}. "
                "System messages must be handled separately.",
                framework="anthropic",
            )

    def _validate_alternation(
        self,
        messages: list[AnthropicMessage],
    ) -> None:
        """Validate that messages alternate between user and assistant.

        Anthropic's API requires:
        1. First message must be from user
        2. Messages must strictly alternate between user and assistant

        Args:
            messages: List of Anthropic messages to validate

        Raises:
            ConversionError: If validation fails

        Example:
            >>> # Valid
            >>> messages = [
            ...     {"role": "user", "content": "Hi"},
            ...     {"role": "assistant", "content": "Hello"},
            ...     {"role": "user", "content": "How are you?"}
            ... ]
            >>> integration._validate_alternation(messages)  # OK
            >>>
            >>> # Invalid - consecutive user messages
            >>> bad_messages = [
            ...     {"role": "user", "content": "Hi"},
            ...     {"role": "user", "content": "Hello?"}  # Error!
            ... ]
            >>> integration._validate_alternation(bad_messages)  # Raises
        """
        if not messages:
            return

        # First message must be user
        if messages[0]["role"] != "user":
            raise ConversionError(
                "First message must be from user in Anthropic format. "
                "Anthropic requires conversations to start with a user message.",
                framework="anthropic",
            )

        # Check alternation
        for i in range(1, len(messages)):
            current_role = messages[i]["role"]
            previous_role = messages[i - 1]["role"]

            if current_role == previous_role:
                raise ConversionError(
                    f"Messages must alternate between user and assistant roles. "
                    f"Found consecutive '{current_role}' messages at position {i}.",
                    framework="anthropic",
                )

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """Check if prompt is compatible with Anthropic.

        Anthropic only supports CHAT format prompts.

        Args:
            prompt: The prompt to validate

        Returns:
            True if prompt is CHAT format, False otherwise

        Example:
            >>> chat_prompt = Prompt(format=PromptFormat.CHAT, ...)
            >>> integration.validate_compatibility(chat_prompt)
            True
            >>>
            >>> text_prompt = Prompt(format=PromptFormat.TEXT, ...)
            >>> integration.validate_compatibility(text_prompt)
            False
        """
        return prompt.format == PromptFormat.CHAT
