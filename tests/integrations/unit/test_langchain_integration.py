"""Unit tests for LangChain integration."""


import pytest

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
from prompt_manager.exceptions import ConversionError, IntegrationNotAvailableError
from prompt_manager.integrations.langchain import (
    LANGCHAIN_AVAILABLE,
    LangChainIntegration,
)

# Skip all tests if LangChain is not available
pytestmark = pytest.mark.skipif(
    not LANGCHAIN_AVAILABLE,
    reason="langchain-core not installed"
)


class TestLangChainIntegration:
    """Test suite for LangChainIntegration class."""

    @pytest.fixture
    def template_engine(self) -> TemplateEngine:
        """Create a TemplateEngine instance."""
        return TemplateEngine()

    @pytest.fixture
    def integration(self, template_engine: TemplateEngine) -> LangChainIntegration:
        """Create a LangChainIntegration instance."""
        return LangChainIntegration(template_engine)

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
    def test_convert_text_prompt_to_prompt_template(
        self, integration: LangChainIntegration, text_prompt: Prompt
    ) -> None:
        """Test converting TEXT prompt to LangChain PromptTemplate."""
        # Arrange
        from langchain_core.prompts import PromptTemplate
        variables = {"name": "Alice"}

        # Act
        result = integration.convert(text_prompt, variables)

        # Assert
        assert isinstance(result, PromptTemplate)
        # Verify the template uses f-string format
        assert "{name}" in result.template

    def test_convert_text_prompt_with_multiple_variables(
        self, integration: LangChainIntegration
    ) -> None:
        """Test TEXT prompt conversion with multiple variables."""
        # Arrange
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
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

        # Act
        result = integration.convert(prompt, {})

        # Assert
        assert isinstance(result, LCPromptTemplate)
        # Verify Handlebars {{}} converted to f-string {}
        assert "{name}" in result.template
        assert "{age}" in result.template
        assert "{{" not in result.template

    def test_convert_text_prompt_missing_template_raises_error(
        self, integration: LangChainIntegration
    ) -> None:
        """Test error when TEXT prompt has no template."""
        # Arrange
        prompt = Prompt(
            id="no_template",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )
        prompt.__dict__["template"] = None

        # Act & Assert
        with pytest.raises(ConversionError, match="TEXT format requires template"):
            integration.convert(prompt, {})

    # Test: Chat prompt conversion
    def test_convert_chat_prompt_to_chat_prompt_template(
        self, integration: LangChainIntegration, chat_prompt: Prompt
    ) -> None:
        """Test converting CHAT prompt to LangChain ChatPromptTemplate."""
        # Arrange
        from langchain_core.prompts import ChatPromptTemplate
        variables = {"topic": "AI"}

        # Act
        result = integration.convert(chat_prompt, variables)

        # Assert
        assert isinstance(result, ChatPromptTemplate)
        # Verify we have 2 message templates
        assert len(result.messages) == 2

    def test_convert_chat_prompt_with_all_roles(
        self, integration: LangChainIntegration
    ) -> None:
        """Test CHAT prompt with multiple roles."""
        # Arrange
        from langchain_core.prompts import ChatPromptTemplate as LCChatPromptTemplate
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
                ],
            ),
        )

        # Act
        result = integration.convert(prompt, {})

        # Assert
        assert isinstance(result, LCChatPromptTemplate)
        assert len(result.messages) == 3

    def test_convert_chat_prompt_missing_template_raises_error(
        self, integration: LangChainIntegration
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

    # Test: Handlebars to f-string conversion
    def test_handlebars_to_fstring_simple(
        self, integration: LangChainIntegration
    ) -> None:
        """Test simple Handlebars to f-string conversion."""
        # Act
        result = integration._handlebars_to_fstring("Hello {{name}}!")

        # Assert
        assert result == "Hello {name}!"

    def test_handlebars_to_fstring_multiple_variables(
        self, integration: LangChainIntegration
    ) -> None:
        """Test multiple variable conversion."""
        # Act
        result = integration._handlebars_to_fstring("{{greeting}} {{name}}, age {{age}}")

        # Assert
        assert result == "{greeting} {name}, age {age}"

    def test_handlebars_to_fstring_no_variables(
        self, integration: LangChainIntegration
    ) -> None:
        """Test conversion with no variables."""
        # Act
        result = integration._handlebars_to_fstring("Hello world!")

        # Assert
        assert result == "Hello world!"

    # Test: Compatibility validation
    def test_validate_compatibility_returns_true_for_text(
        self, integration: LangChainIntegration, text_prompt: Prompt
    ) -> None:
        """Test that LangChain integration is compatible with TEXT format."""
        # Act
        result = integration.validate_compatibility(text_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_returns_true_for_chat(
        self, integration: LangChainIntegration, chat_prompt: Prompt
    ) -> None:
        """Test that LangChain integration is compatible with CHAT format."""
        # Act
        result = integration.validate_compatibility(chat_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_returns_false_for_other_formats(
        self, integration: LangChainIntegration
    ) -> None:
        """Test that LangChain integration only supports TEXT and CHAT."""
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

    # Test: Error handling
    def test_convert_handles_creation_error(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test error handling when template creation fails."""
        # Arrange
        integration = LangChainIntegration(template_engine)

        # Create a prompt with content that will cause PromptTemplate.from_template to fail
        # (We'll use a mock to simulate this failure)
        prompt = Prompt(
            id="error_prompt",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )

        # Mock PromptTemplate.from_template to raise exception
        from langchain_core.prompts import PromptTemplate as LCPromptTemplate
        original_from_template = LCPromptTemplate.from_template

        def mock_from_template(*args, **kwargs):
            raise ValueError("Template creation failed")

        LCPromptTemplate.from_template = staticmethod(mock_from_template)

        try:
            # Act & Assert
            with pytest.raises(ConversionError, match="Failed to create PromptTemplate"):
                integration.convert(prompt, {})
        finally:
            # Restore original method
            LCPromptTemplate.from_template = staticmethod(original_from_template)

    def test_conversion_error_includes_prompt_id(
        self, integration: LangChainIntegration
    ) -> None:
        """Test that ConversionError includes prompt_id in context."""
        # Arrange
        prompt = Prompt(
            id="my_langchain_prompt",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )
        prompt.__dict__["template"] = None

        # Act & Assert
        with pytest.raises(ConversionError) as exc_info:
            integration.convert(prompt, {})

        assert exc_info.value.context.get("prompt_id") == "my_langchain_prompt"

    def test_conversion_error_includes_framework(
        self, integration: LangChainIntegration
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
        prompt.__dict__["template"] = None

        # Act & Assert
        with pytest.raises(ConversionError) as exc_info:
            integration.convert(prompt, {})

        assert exc_info.value.context.get("framework") == "langchain"

    # Test: Strict validation mode
    def test_strict_validation_mode_default(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that strict_validation defaults to True."""
        # Act
        integration = LangChainIntegration(template_engine)

        # Assert
        assert integration.strict_validation is True

    def test_strict_validation_mode_explicit_false(
        self, template_engine: TemplateEngine
    ) -> None:
        """Test that strict_validation can be set to False."""
        # Act
        integration = LangChainIntegration(template_engine, strict_validation=False)

        # Assert
        assert integration.strict_validation is False


def test_langchain_not_available_raises_integration_not_available_error() -> None:
    """Test that IntegrationNotAvailableError is raised when langchain-core not installed."""
    # This test is only relevant if LANGCHAIN_AVAILABLE is False
    if LANGCHAIN_AVAILABLE:
        pytest.skip("LangChain is available, skipping unavailability test")

    # Arrange
    template_engine = TemplateEngine()

    # Act & Assert
    with pytest.raises(IntegrationNotAvailableError):
        LangChainIntegration(template_engine)
