"""Unit tests for Anthropic integration."""

import pytest
from unittest.mock import AsyncMock, Mock

from prompt_manager.core.models import (
    ChatPromptTemplate,
    Message,
    Prompt,
    PromptFormat,
    PromptStatus,
    PromptTemplate,
    Role,
)
from prompt_manager.core.template import TemplateEngine
from prompt_manager.exceptions import ConversionError, IncompatibleFormatError
from prompt_manager.integrations.anthropic import AnthropicIntegration


class TestAnthropicIntegration:
    """Test suite for AnthropicIntegration class."""

    @pytest.fixture
    def template_engine(self) -> TemplateEngine:
        """Create a TemplateEngine instance."""
        return TemplateEngine()

    @pytest.fixture
    def integration(self, template_engine: TemplateEngine) -> AnthropicIntegration:
        """Create an AnthropicIntegration instance."""
        return AnthropicIntegration(template_engine)

    @pytest.fixture
    def chat_prompt(self) -> Prompt:
        """Create a CHAT format prompt with system message."""
        return Prompt(
            id="chat_prompt",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.SYSTEM, content="You are a helpful assistant."),
                    Message(role=Role.USER, content="Tell me about {{topic}}."),
                ],
                variables=["topic"],
            ),
        )

    # Test: Format validation
    def test_convert_text_format_raises_incompatible_format_error(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test that TEXT format raises IncompatibleFormatError."""
        # Arrange
        text_prompt = Prompt(
            id="text_prompt",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Hello {{name}}!"),
        )

        # Act & Assert
        with pytest.raises(
            IncompatibleFormatError, match="incompatible with framework 'anthropic'"
        ):
            integration.convert(text_prompt, {})

    def test_convert_chat_prompt_to_anthropic_format(
        self, integration: AnthropicIntegration, chat_prompt: Prompt
    ) -> None:
        """Test converting CHAT prompt to Anthropic format."""
        # Arrange
        variables = {"topic": "AI"}

        # Act
        result = integration.convert(chat_prompt, variables)

        # Assert
        assert isinstance(result, dict)
        assert "messages" in result
        assert "system" in result
        assert result["system"] == "You are a helpful assistant."
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "Tell me about AI."

    def test_convert_chat_prompt_without_system_message(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test CHAT prompt without system message."""
        # Arrange
        prompt = Prompt(
            id="no_system",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="Hello"),
                    Message(role=Role.ASSISTANT, content="Hi there!"),
                ],
            ),
        )

        # Act
        result = integration.convert(prompt, {})

        # Assert
        assert "messages" in result
        assert "system" not in result or result.get("system") is None
        assert len(result["messages"]) == 2
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"

    def test_convert_chat_prompt_with_multiple_exchanges(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test CHAT prompt with multiple user-assistant exchanges."""
        # Arrange
        prompt = Prompt(
            id="multi_exchange",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.SYSTEM, content="System message"),
                    Message(role=Role.USER, content="First question"),
                    Message(role=Role.ASSISTANT, content="First answer"),
                    Message(role=Role.USER, content="Second question"),
                ],
            ),
        )

        # Act
        result = integration.convert(prompt, {})

        # Assert
        assert result["system"] == "System message"
        assert len(result["messages"]) == 3
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"
        assert result["messages"][2]["role"] == "user"

    def test_convert_missing_chat_template_raises_error(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test error when CHAT prompt has no chat_template."""
        # Arrange
        prompt = Prompt(
            id="no_chat_template",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[Message(role=Role.USER, content="Test")]
            ),
        )
        prompt.__dict__["chat_template"] = None

        # Act & Assert
        with pytest.raises(ConversionError, match="CHAT format requires chat_template"):
            integration.convert(prompt, {})

    # Test: Role mapping
    def test_map_role_user(self, integration: AnthropicIntegration) -> None:
        """Test mapping USER role to Anthropic format."""
        # Act
        result = integration._map_role(Role.USER)

        # Assert
        assert result == "user"

    def test_map_role_function(self, integration: AnthropicIntegration) -> None:
        """Test mapping FUNCTION role to user (tool response)."""
        # Act
        result = integration._map_role(Role.FUNCTION)

        # Assert
        assert result == "user"

    def test_map_role_tool(self, integration: AnthropicIntegration) -> None:
        """Test mapping TOOL role to user (tool response)."""
        # Act
        result = integration._map_role(Role.TOOL)

        # Assert
        assert result == "user"

    def test_map_role_assistant(self, integration: AnthropicIntegration) -> None:
        """Test mapping ASSISTANT role to Anthropic format."""
        # Act
        result = integration._map_role(Role.ASSISTANT)

        # Assert
        assert result == "assistant"

    def test_map_role_system_raises_error(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test that SYSTEM role cannot be mapped directly."""
        # Act & Assert
        with pytest.raises(ConversionError, match="Unsupported role for Anthropic"):
            integration._map_role(Role.SYSTEM)

    # Test: Message alternation validation
    def test_validate_alternation_valid_sequence(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test valid user-assistant alternation."""
        # Arrange
        prompt = Prompt(
            id="valid_alternation",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="Hi"),
                    Message(role=Role.ASSISTANT, content="Hello"),
                    Message(role=Role.USER, content="How are you?"),
                ],
            ),
        )

        # Act & Assert - Should not raise
        result = integration.convert(prompt, {})
        assert len(result["messages"]) == 3

    def test_validate_alternation_first_message_not_user(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test error when first message is not from user."""
        # Arrange
        prompt = Prompt(
            id="assistant_first",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.ASSISTANT, content="Hello"),
                    Message(role=Role.USER, content="Hi"),
                ],
            ),
        )

        # Act & Assert
        with pytest.raises(ConversionError, match="First message must be from user"):
            integration.convert(prompt, {})

    def test_validate_alternation_consecutive_user_messages(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test error when consecutive user messages appear."""
        # Arrange
        prompt = Prompt(
            id="consecutive_user",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="First"),
                    Message(role=Role.USER, content="Second"),
                ],
            ),
        )

        # Act & Assert
        with pytest.raises(ConversionError, match="Messages must alternate"):
            integration.convert(prompt, {})

    def test_validate_alternation_consecutive_assistant_messages(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test error when consecutive assistant messages appear."""
        # Arrange
        prompt = Prompt(
            id="consecutive_assistant",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="Question"),
                    Message(role=Role.ASSISTANT, content="Answer 1"),
                    Message(role=Role.ASSISTANT, content="Answer 2"),
                ],
            ),
        )

        # Act & Assert
        with pytest.raises(ConversionError, match="Messages must alternate"):
            integration.convert(prompt, {})

    def test_validate_alternation_with_tool_roles(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test alternation with FUNCTION/TOOL roles mapped to user."""
        # Arrange
        prompt = Prompt(
            id="tool_roles",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="Call function"),
                    Message(role=Role.ASSISTANT, content="Calling..."),
                    Message(role=Role.FUNCTION, content="Function result"),
                ],
            ),
        )

        # Act
        result = integration.convert(prompt, {})

        # Assert
        assert len(result["messages"]) == 3
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"
        assert result["messages"][2]["role"] == "user"  # FUNCTION mapped to user

    # Test: System message handling
    def test_single_system_message_extracted(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test single system message is extracted correctly."""
        # Arrange
        prompt = Prompt(
            id="system_test",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.SYSTEM, content="Be helpful"),
                    Message(role=Role.USER, content="Hello"),
                ],
            ),
        )

        # Act
        result = integration.convert(prompt, {})

        # Assert
        assert result["system"] == "Be helpful"
        assert len(result["messages"]) == 1

    def test_multiple_system_messages_raises_error(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test error when multiple system messages present."""
        # Arrange
        prompt = Prompt(
            id="multi_system",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.SYSTEM, content="System 1"),
                    Message(role=Role.SYSTEM, content="System 2"),
                    Message(role=Role.USER, content="Hello"),
                ],
            ),
        )

        # Act & Assert
        with pytest.raises(
            ConversionError, match="only supports one system message"
        ):
            integration.convert(prompt, {})

    # Test: Variable substitution
    def test_variable_substitution_in_system_message(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test variable substitution in system message."""
        # Arrange
        prompt = Prompt(
            id="var_system",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.SYSTEM, content="You are a {{role}} assistant."),
                    Message(role=Role.USER, content="Hello"),
                ],
                variables=["role"],
            ),
        )
        variables = {"role": "helpful"}

        # Act
        result = integration.convert(prompt, variables)

        # Assert
        assert result["system"] == "You are a helpful assistant."

    def test_variable_substitution_in_messages(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test variable substitution in user/assistant messages."""
        # Arrange
        prompt = Prompt(
            id="var_messages",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="My name is {{name}}."),
                    Message(role=Role.ASSISTANT, content="Hello {{name}}!"),
                ],
                variables=["name"],
            ),
        )
        variables = {"name": "Alice"}

        # Act
        result = integration.convert(prompt, variables)

        # Assert
        assert result["messages"][0]["content"] == "My name is Alice."
        assert result["messages"][1]["content"] == "Hello Alice!"

    # Test: Error handling
    def test_convert_handles_template_rendering_error(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test error handling when template rendering fails."""
        # Arrange
        mock_engine = Mock(spec=TemplateEngine)
        mock_engine.render = AsyncMock(side_effect=Exception("Rendering failed"))

        integration = AnthropicIntegration(mock_engine)

        prompt = Prompt(
            id="error_prompt",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[Message(role=Role.USER, content="Test {{var}}")]
            ),
        )

        # Act & Assert
        with pytest.raises(ConversionError, match="Failed to render chat template"):
            integration.convert(prompt, {})

    def test_conversion_error_includes_prompt_id(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test that ConversionError includes prompt_id in context."""
        # Arrange
        prompt = Prompt(
            id="my_anthropic_prompt",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[Message(role=Role.USER, content="Test")]
            ),
        )
        prompt.__dict__["chat_template"] = None

        # Act & Assert
        with pytest.raises(ConversionError) as exc_info:
            integration.convert(prompt, {})

        assert exc_info.value.context.get("prompt_id") == "my_anthropic_prompt"

    def test_conversion_error_includes_framework(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test that ConversionError includes framework in context."""
        # Arrange
        prompt = Prompt(
            id="test",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[Message(role=Role.USER, content="Test")]
            ),
        )
        prompt.__dict__["chat_template"] = None

        # Act & Assert
        with pytest.raises(ConversionError) as exc_info:
            integration.convert(prompt, {})

        assert exc_info.value.context.get("framework") == "anthropic"

    # Test: Compatibility validation
    def test_validate_compatibility_returns_true_for_chat(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test that Anthropic integration is compatible with CHAT format."""
        # Arrange
        chat_prompt = Prompt(
            id="chat",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[Message(role=Role.USER, content="Test")]
            ),
        )

        # Act
        result = integration.validate_compatibility(chat_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_returns_false_for_text(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test that Anthropic integration is not compatible with TEXT format."""
        # Arrange
        text_prompt = Prompt(
            id="text",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )

        # Act
        result = integration.validate_compatibility(text_prompt)

        # Assert
        assert result is False

    def test_validate_compatibility_returns_false_for_other_formats(
        self, integration: AnthropicIntegration
    ) -> None:
        """Test that Anthropic integration only supports CHAT format."""
        # Arrange
        completion_prompt = Prompt(
            id="completion",
            format=PromptFormat.COMPLETION,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )
        instruction_prompt = Prompt(
            id="instruction",
            format=PromptFormat.INSTRUCTION,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )

        # Act & Assert
        assert integration.validate_compatibility(completion_prompt) is False
        assert integration.validate_compatibility(instruction_prompt) is False

    # Test: Strict validation mode
    def test_strict_validation_mode_default(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that strict_validation defaults to True."""
        # Act
        integration = AnthropicIntegration(template_engine)

        # Assert
        assert integration.strict_validation is True

    def test_strict_validation_mode_explicit_false(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that strict_validation can be set to False."""
        # Act
        integration = AnthropicIntegration(template_engine, strict_validation=False)

        # Assert
        assert integration.strict_validation is False
