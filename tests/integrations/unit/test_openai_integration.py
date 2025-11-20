"""Unit tests for OpenAI integration."""

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
from prompt_manager.exceptions import ConversionError
from prompt_manager.integrations.openai import OpenAIIntegration


class TestOpenAIIntegration:
    """Test suite for OpenAIIntegration class."""

    @pytest.fixture
    def template_engine(self) -> TemplateEngine:
        """Create a TemplateEngine instance."""
        return TemplateEngine()

    @pytest.fixture
    def integration(self, template_engine: TemplateEngine) -> OpenAIIntegration:
        """Create an OpenAIIntegration instance."""
        return OpenAIIntegration(template_engine)

    @pytest.fixture
    def text_prompt(self) -> Prompt:
        """Create a simple TEXT format prompt."""
        return Prompt(
            id="text_prompt",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content="Hello {{name}}!",
                variables=["name"],
            ),
        )

    @pytest.fixture
    def chat_prompt(self) -> Prompt:
        """Create a CHAT format prompt."""
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

    # Test: Text prompt conversion
    @pytest.mark.asyncio
    async def test_convert_text_prompt_to_string(
        self, integration: OpenAIIntegration, text_prompt: Prompt
    ) -> None:
        """Test converting TEXT prompt to string."""
        # Arrange
        variables = {"name": "Alice"}

        # Act
        result = await integration.convert(text_prompt, variables)

        # Assert
        assert isinstance(result, str)
        assert result == "Hello Alice!"

    @pytest.mark.asyncio
    async def test_convert_text_prompt_with_multiple_variables(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test TEXT prompt conversion with multiple variables."""
        # Arrange
        prompt = Prompt(
            id="multi_var",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content="Hello {{name}}, you are {{age}} years old.",
                variables=["name", "age"],
            ),
        )
        variables = {"name": "Bob", "age": "25"}

        # Act
        result = await integration.convert(prompt, variables)

        # Assert
        assert result == "Hello Bob, you are 25 years old."

    @pytest.mark.asyncio
    async def test_convert_text_prompt_missing_template_raises_error(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test error when TEXT prompt has no template (via mock)."""
        # Arrange
        # Create a valid prompt first, then mock out the template
        prompt = Prompt(
            id="no_template",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )
        # Mock the template to None to simulate missing template
        prompt.__dict__["template"] = None

        # Act & Assert
        with pytest.raises(ConversionError, match="TEXT format requires template"):
            await integration.convert(prompt, {})

    # Test: Chat prompt conversion
    @pytest.mark.asyncio
    async def test_convert_chat_prompt_to_message_list(
        self, integration: OpenAIIntegration, chat_prompt: Prompt
    ) -> None:
        """Test converting CHAT prompt to OpenAI message list."""
        # Arrange
        variables = {"topic": "AI"}

        # Act
        result = await integration.convert(chat_prompt, variables)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are a helpful assistant."
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Tell me about AI."

    @pytest.mark.asyncio
    async def test_convert_chat_prompt_with_all_roles(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test CHAT prompt with all supported roles."""
        # Arrange
        prompt = Prompt(
            id="all_roles",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.SYSTEM, content="System message"),
                    Message(role=Role.USER, content="User message"),
                    Message(role=Role.ASSISTANT, content="Assistant message"),
                    Message(role=Role.FUNCTION, content="Function message"),
                    Message(role=Role.TOOL, content="Tool message"),
                ],
            ),
        )

        # Act
        result = await integration.convert(prompt, {})

        # Assert
        assert len(result) == 5
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"
        assert result[3]["role"] == "function"
        assert result[4]["role"] == "tool"

    @pytest.mark.asyncio
    async def test_convert_chat_prompt_missing_template_raises_error(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test error when CHAT prompt has no chat_template (via mock)."""
        # Arrange
        # Create a valid prompt first, then mock out the chat_template
        prompt = Prompt(
            id="no_chat_template",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[Message(role=Role.USER, content="Test")]
            ),
        )
        # Mock the chat_template to None to simulate missing chat_template
        prompt.__dict__["chat_template"] = None

        # Act & Assert
        with pytest.raises(ConversionError, match="CHAT format requires chat_template"):
            await integration.convert(prompt, {})

    @pytest.mark.asyncio
    async def test_convert_chat_prompt_with_name_field(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test CHAT prompt message with name field."""
        # Arrange
        prompt = Prompt(
            id="named_message",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(
                        role=Role.USER,
                        content="Hello",
                        name="john_doe",
                    ),
                ],
            ),
        )

        # Act
        result = await integration.convert(prompt, {})

        # Assert
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"
        assert result[0]["name"] == "john_doe"

    @pytest.mark.asyncio
    async def test_convert_chat_prompt_without_name_field(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test CHAT prompt message without name field."""
        # Arrange
        prompt = Prompt(
            id="unnamed_message",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="Hello"),
                ],
            ),
        )

        # Act
        result = await integration.convert(prompt, {})

        # Assert
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello"
        assert "name" not in result[0] or result[0].get("name") is None

    # Test: Role mapping
    def test_map_role_system(self, integration: OpenAIIntegration) -> None:
        """Test mapping SYSTEM role to OpenAI format."""
        # Act
        result = integration._map_role(Role.SYSTEM)

        # Assert
        assert result == "system"

    def test_map_role_user(self, integration: OpenAIIntegration) -> None:
        """Test mapping USER role to OpenAI format."""
        # Act
        result = integration._map_role(Role.USER)

        # Assert
        assert result == "user"

    def test_map_role_assistant(self, integration: OpenAIIntegration) -> None:
        """Test mapping ASSISTANT role to OpenAI format."""
        # Act
        result = integration._map_role(Role.ASSISTANT)

        # Assert
        assert result == "assistant"

    def test_map_role_function(self, integration: OpenAIIntegration) -> None:
        """Test mapping FUNCTION role to OpenAI format."""
        # Act
        result = integration._map_role(Role.FUNCTION)

        # Assert
        assert result == "function"

    def test_map_role_tool(self, integration: OpenAIIntegration) -> None:
        """Test mapping TOOL role to OpenAI format."""
        # Act
        result = integration._map_role(Role.TOOL)

        # Assert
        assert result == "tool"

    # Test: Compatibility validation
    def test_validate_compatibility_returns_true_for_text(
        self, integration: OpenAIIntegration, text_prompt: Prompt
    ) -> None:
        """Test that OpenAI integration is compatible with TEXT format."""
        # Act
        result = integration.validate_compatibility(text_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_returns_true_for_chat(
        self, integration: OpenAIIntegration, chat_prompt: Prompt
    ) -> None:
        """Test that OpenAI integration is compatible with CHAT format."""
        # Act
        result = integration.validate_compatibility(chat_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_returns_true_for_all_formats(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test that OpenAI integration supports all prompt formats."""
        # Arrange - Create prompts with different formats
        text_prompt = Prompt(
            id="text",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )
        chat_prompt = Prompt(
            id="chat",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[Message(role=Role.USER, content="Test")]
            ),
        )
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

        # Act & Assert - All formats should be compatible
        assert integration.validate_compatibility(text_prompt) is True
        assert integration.validate_compatibility(chat_prompt) is True
        assert integration.validate_compatibility(completion_prompt) is True
        assert integration.validate_compatibility(instruction_prompt) is True

    # Test: Error handling
    @pytest.mark.asyncio
    async def test_convert_unsupported_format_raises_error(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test error when converting unsupported format."""
        # Arrange
        prompt = Prompt(
            id="completion_prompt",
            version="1.0.0",
            format=PromptFormat.COMPLETION,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )

        # Act & Assert
        with pytest.raises(ConversionError, match="Unsupported prompt format"):
            await integration.convert(prompt, {})

    @pytest.mark.asyncio
    async def test_convert_handles_template_rendering_error(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test error handling when template rendering fails."""
        # Arrange
        mock_engine = Mock(spec=TemplateEngine)
        mock_engine.render = AsyncMock(side_effect=Exception("Rendering failed"))

        integration = OpenAIIntegration(mock_engine)

        prompt = Prompt(
            id="error_prompt",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test {{var}}"),
        )

        # Act & Assert
        with pytest.raises(ConversionError, match="Failed to render text template"):
            await integration.convert(prompt, {})

    @pytest.mark.asyncio
    async def test_convert_chat_handles_rendering_error(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test error handling when chat template rendering fails."""
        # Arrange
        mock_engine = Mock(spec=TemplateEngine)
        mock_engine.render = AsyncMock(side_effect=Exception("Rendering failed"))

        integration = OpenAIIntegration(mock_engine)

        prompt = Prompt(
            id="error_chat",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[Message(role=Role.USER, content="Test {{var}}")]
            ),
        )

        # Act & Assert
        with pytest.raises(ConversionError, match="Failed to render chat template"):
            await integration.convert(prompt, {})

    # Test: Variable substitution
    @pytest.mark.asyncio
    async def test_variable_substitution_in_text_prompt(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test variable substitution works correctly in TEXT prompts."""
        # Arrange
        prompt = Prompt(
            id="var_test",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content="Name: {{name}}, Age: {{age}}, City: {{city}}",
                variables=["name", "age", "city"],
            ),
        )
        variables = {"name": "Alice", "age": "30", "city": "NYC"}

        # Act
        result = await integration.convert(prompt, variables)

        # Assert
        assert result == "Name: Alice, Age: 30, City: NYC"

    @pytest.mark.asyncio
    async def test_variable_substitution_in_chat_prompt(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test variable substitution works correctly in CHAT prompts."""
        # Arrange
        prompt = Prompt(
            id="chat_var_test",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(
                        role=Role.SYSTEM,
                        content="You are a {{role}} assistant.",
                    ),
                    Message(
                        role=Role.USER,
                        content="My name is {{user_name}} and I need help with {{task}}.",
                    ),
                ],
                variables=["role", "user_name", "task"],
            ),
        )
        variables = {"role": "helpful", "user_name": "Bob", "task": "coding"}

        # Act
        result = await integration.convert(prompt, variables)

        # Assert
        assert len(result) == 2
        assert result[0]["content"] == "You are a helpful assistant."
        assert result[1]["content"] == "My name is Bob and I need help with coding."

    # Test: Strict validation mode
    def test_strict_validation_mode_default(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that strict_validation defaults to True."""
        # Act
        integration = OpenAIIntegration(template_engine)

        # Assert
        assert integration.strict_validation is True

    def test_strict_validation_mode_explicit_false(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that strict_validation can be set to False."""
        # Act
        integration = OpenAIIntegration(template_engine, strict_validation=False)

        # Assert
        assert integration.strict_validation is False

    # Test: ConversionError context preservation
    @pytest.mark.asyncio
    async def test_conversion_error_includes_prompt_id(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test that ConversionError includes prompt_id in context."""
        # Arrange
        prompt = Prompt(
            id="my_test_prompt",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )
        # Mock template to None to trigger error
        prompt.__dict__["template"] = None

        # Act & Assert
        with pytest.raises(ConversionError) as exc_info:
            await integration.convert(prompt, {})

        assert exc_info.value.context.get("prompt_id") == "my_test_prompt"

    @pytest.mark.asyncio
    async def test_conversion_error_includes_framework(
        self, integration: OpenAIIntegration
    ) -> None:
        """Test that ConversionError includes framework in context."""
        # Arrange
        prompt = Prompt(
            id="test",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )
        # Mock template to None to trigger error
        prompt.__dict__["template"] = None

        # Act & Assert
        with pytest.raises(ConversionError) as exc_info:
            await integration.convert(prompt, {})

        assert exc_info.value.context.get("framework") == "openai"
