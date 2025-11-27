"""Unit tests for LiteLLM integration."""

import pytest
from unittest.mock import AsyncMock

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
from prompt_manager.integrations.litellm import LiteLLMIntegration


class TestLiteLLMIntegration:
    """Test suite for LiteLLMIntegration class."""

    @pytest.fixture
    def template_engine(self) -> TemplateEngine:
        """Create a TemplateEngine instance."""
        return TemplateEngine()

    @pytest.fixture
    def integration(self, template_engine: TemplateEngine) -> LiteLLMIntegration:
        """Create a LiteLLMIntegration instance."""
        return LiteLLMIntegration(template_engine)

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

    # Test: Initialization and delegation
    def test_integration_creates_openai_integration(
        self, integration: LiteLLMIntegration
    ) -> None:
        """Test that LiteLLM integration creates OpenAI integration internally."""
        # Assert
        assert integration._openai_integration is not None
        assert hasattr(integration._openai_integration, "convert")

    def test_integration_passes_template_engine_to_openai(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that template engine is passed to OpenAI integration."""
        # Act
        integration = LiteLLMIntegration(template_engine)

        # Assert
        assert integration._openai_integration.template_engine is template_engine

    def test_integration_passes_strict_validation_to_openai(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that strict_validation is passed to OpenAI integration."""
        # Act
        integration = LiteLLMIntegration(template_engine, strict_validation=False)

        # Assert
        assert integration._openai_integration.strict_validation is False

    # Test: Text prompt conversion (delegates to OpenAI)
    def test_convert_text_prompt_to_string(
        self, integration: LiteLLMIntegration, text_prompt: Prompt
    ) -> None:
        """Test converting TEXT prompt to string (via OpenAI delegation)."""
        # Arrange
        variables = {"name": "Alice"}

        # Act
        result = integration.convert(text_prompt, variables)

        # Assert
        assert isinstance(result, str)
        assert result == "Hello Alice!"

    def test_convert_text_prompt_delegates_to_openai(
        self, integration: LiteLLMIntegration, text_prompt: Prompt
    ) -> None:
        """Test that convert delegates to OpenAI integration."""
        # Arrange
        mock_result = "Mocked result"
        mock_convert = AsyncMock(return_value=mock_result)
        integration._openai_integration.convert = mock_convert  # type: ignore

        variables = {"name": "Test"}

        # Act
        result = integration.convert(text_prompt, variables)

        # Assert
        mock_convert.assert_called_once_with(text_prompt, variables)
        assert result == mock_result

    # Test: Chat prompt conversion (delegates to OpenAI)
    def test_convert_chat_prompt_to_message_list(
        self, integration: LiteLLMIntegration, chat_prompt: Prompt
    ) -> None:
        """Test converting CHAT prompt to OpenAI message list."""
        # Arrange
        variables = {"topic": "AI"}

        # Act
        result = integration.convert(chat_prompt, variables)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are a helpful assistant."
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Tell me about AI."

    def test_convert_chat_prompt_delegates_to_openai(
        self, integration: LiteLLMIntegration, chat_prompt: Prompt
    ) -> None:
        """Test that chat conversion delegates to OpenAI integration."""
        # Arrange
        mock_result = [{"role": "user", "content": "Mocked"}]
        mock_convert = AsyncMock(return_value=mock_result)
        integration._openai_integration.convert = mock_convert  # type: ignore

        variables = {"topic": "Test"}

        # Act
        result = integration.convert(chat_prompt, variables)

        # Assert
        mock_convert.assert_called_once_with(chat_prompt, variables)
        assert result == mock_result

    # Test: Compatibility validation (supports all formats)
    def test_validate_compatibility_returns_true_for_text(
        self, integration: LiteLLMIntegration, text_prompt: Prompt
    ) -> None:
        """Test that LiteLLM is compatible with TEXT format."""
        # Act
        result = integration.validate_compatibility(text_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_returns_true_for_chat(
        self, integration: LiteLLMIntegration, chat_prompt: Prompt
    ) -> None:
        """Test that LiteLLM is compatible with CHAT format."""
        # Act
        result = integration.validate_compatibility(chat_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_returns_true_for_all_formats(
        self, integration: LiteLLMIntegration
    ) -> None:
        """Test that LiteLLM supports all prompt formats (via OpenAI)."""
        # Arrange
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

        # Act & Assert
        assert integration.validate_compatibility(text_prompt) is True
        assert integration.validate_compatibility(chat_prompt) is True
        assert integration.validate_compatibility(completion_prompt) is True

    def test_validate_compatibility_delegates_to_openai(
        self, integration: LiteLLMIntegration, text_prompt: Prompt
    ) -> None:
        """Test that validate_compatibility delegates to OpenAI integration."""
        # Arrange
        # Mock OpenAI's validate_compatibility to return False
        integration._openai_integration.validate_compatibility = lambda p: False  # type: ignore

        # Act
        result = integration.validate_compatibility(text_prompt)

        # Assert
        assert result is False

    # Test: Strict validation mode
    def test_strict_validation_mode_default(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that strict_validation defaults to True."""
        # Act
        integration = LiteLLMIntegration(template_engine)

        # Assert
        assert integration.strict_validation is True
        assert integration._openai_integration.strict_validation is True

    def test_strict_validation_mode_explicit_false(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that strict_validation can be set to False."""
        # Act
        integration = LiteLLMIntegration(template_engine, strict_validation=False)

        # Assert
        assert integration.strict_validation is False
        assert integration._openai_integration.strict_validation is False

    # Test: Properties
    def test_template_engine_property(
        self, integration: LiteLLMIntegration, template_engine: TemplateEngine
    ) -> None:
        """Test that template_engine property returns correct engine."""
        # Assert
        assert integration.template_engine is template_engine

    # Test: Variable substitution
    def test_variable_substitution_in_text_prompt(
        self, integration: LiteLLMIntegration
    ) -> None:
        """Test variable substitution in TEXT prompts."""
        # Arrange
        prompt = Prompt(
            id="var_test",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content="Name: {{name}}, Age: {{age}}",
                variables=["name", "age"],
            ),
        )
        variables = {"name": "Bob", "age": "30"}

        # Act
        result = integration.convert(prompt, variables)

        # Assert
        assert result == "Name: Bob, Age: 30"

    def test_variable_substitution_in_chat_prompt(
        self, integration: LiteLLMIntegration
    ) -> None:
        """Test variable substitution in CHAT prompts."""
        # Arrange
        prompt = Prompt(
            id="chat_var",
            version="1.0.0",
            format=PromptFormat.CHAT,
            status=PromptStatus.ACTIVE,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="My name is {{name}}."),
                ],
                variables=["name"],
            ),
        )
        variables = {"name": "Charlie"}

        # Act
        result = integration.convert(prompt, variables)

        # Assert
        assert len(result) == 1
        assert result[0]["content"] == "My name is Charlie."
