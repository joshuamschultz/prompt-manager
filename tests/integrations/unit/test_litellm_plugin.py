"""Unit tests for LiteLLM plugin."""

from unittest.mock import AsyncMock, Mock, patch

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
from prompt_manager.exceptions import PluginError
from prompt_manager.plugins.litellm_plugin import LiteLLMPlugin


class TestLiteLLMPlugin:
    """Test suite for LiteLLMPlugin class."""

    @pytest.fixture
    def plugin(self) -> LiteLLMPlugin:
        """Create a LiteLLMPlugin instance."""
        return LiteLLMPlugin()

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

    # Test: Plugin initialization
    def test_plugin_name(self, plugin: LiteLLMPlugin) -> None:
        """Test that plugin has correct name."""
        assert plugin.name == "litellm"

    def test_plugin_version(self, plugin: LiteLLMPlugin) -> None:
        """Test that plugin has correct version."""
        assert plugin.version == "1.0.0"

    def test_plugin_initialization_default_config(
        self, plugin: LiteLLMPlugin
    ) -> None:
        """Test plugin initialization with default configuration."""
        # Act
        plugin.initialize({})

        # Assert
        assert plugin._initialized is True
        assert plugin._integration is not None

    def test_plugin_initialization_with_strict_validation_true(
        self, plugin: LiteLLMPlugin
    ) -> None:
        """Test plugin initialization with strict_validation=True."""
        # Act
        plugin.initialize({"strict_validation": True})

        # Assert
        assert plugin._integration is not None
        assert plugin._integration.strict_validation is True

    def test_plugin_initialization_with_strict_validation_false(
        self, plugin: LiteLLMPlugin
    ) -> None:
        """Test plugin initialization with strict_validation=False."""
        # Act
        plugin.initialize({"strict_validation": False})

        # Assert
        assert plugin._integration is not None
        assert plugin._integration.strict_validation is False

    def test_plugin_initialization_creates_template_engine(
        self, plugin: LiteLLMPlugin
    ) -> None:
        """Test that plugin initialization creates template engine."""
        # Act
        plugin.initialize({})

        # Assert
        assert plugin._integration is not None
        assert plugin._integration.template_engine is not None

    # Test: Render for framework
    def test_render_for_framework_text_prompt(
        self, plugin: LiteLLMPlugin, text_prompt: Prompt
    ) -> None:
        """Test rendering TEXT prompt."""
        # Arrange
        plugin.initialize({})
        variables = {"name": "Alice"}

        # Act
        result = plugin.render_for_framework(text_prompt, variables)

        # Assert
        assert isinstance(result, str)
        assert result == "Hello Alice!"

    def test_render_for_framework_chat_prompt(
        self, plugin: LiteLLMPlugin, chat_prompt: Prompt
    ) -> None:
        """Test rendering CHAT prompt."""
        # Arrange
        plugin.initialize({})
        variables = {"topic": "AI"}

        # Act
        result = plugin.render_for_framework(chat_prompt, variables)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are a helpful assistant."
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Tell me about AI."

    def test_render_for_framework_before_initialization_raises_error(
        self, plugin: LiteLLMPlugin, text_prompt: Prompt
    ) -> None:
        """Test that rendering before initialization raises PluginError."""
        # Act & Assert
        with pytest.raises(PluginError, match="not initialized"):
            plugin.render_for_framework(text_prompt, {})

    def test_render_for_framework_delegates_to_integration(
        self, plugin: LiteLLMPlugin, text_prompt: Prompt
    ) -> None:
        """Test that render_for_framework delegates to integration.convert."""
        # Arrange
        plugin.initialize({})

        # Mock the integration's convert method
        mock_convert = AsyncMock(return_value="Mocked result")
        plugin._integration.convert = mock_convert  # type: ignore

        variables = {"name": "Test"}

        # Act
        result = plugin.render_for_framework(text_prompt, variables)

        # Assert
        mock_convert.assert_called_once_with(text_prompt, variables)
        assert result == "Mocked result"

    # Test: Validate compatibility
    def test_validate_compatibility_returns_true_for_text(
        self, plugin: LiteLLMPlugin, text_prompt: Prompt
    ) -> None:
        """Test that LiteLLM plugin is compatible with TEXT format."""
        # Arrange
        plugin.initialize({})

        # Act
        result = plugin.validate_compatibility(text_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_returns_true_for_chat(
        self, plugin: LiteLLMPlugin, chat_prompt: Prompt
    ) -> None:
        """Test that LiteLLM plugin is compatible with CHAT format."""
        # Arrange
        plugin.initialize({})

        # Act
        result = plugin.validate_compatibility(chat_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_returns_true_for_all_formats(
        self, plugin: LiteLLMPlugin
    ) -> None:
        """Test that LiteLLM plugin supports all formats (via OpenAI)."""
        # Arrange
        plugin.initialize({})

        completion_prompt = Prompt(
            id="completion",
            format=PromptFormat.COMPLETION,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test"),
        )

        # Act
        result = plugin.validate_compatibility(completion_prompt)

        # Assert
        assert result is True

    def test_validate_compatibility_before_initialization_raises_error(
        self, plugin: LiteLLMPlugin, text_prompt: Prompt
    ) -> None:
        """Test that validation before initialization raises PluginError."""
        # Act & Assert
        with pytest.raises(PluginError, match="not initialized"):
            plugin.validate_compatibility(text_prompt)

    def test_validate_compatibility_delegates_to_integration(
        self, plugin: LiteLLMPlugin, text_prompt: Prompt
    ) -> None:
        """Test that validate_compatibility delegates to integration."""
        # Arrange
        plugin.initialize({})

        # Mock the integration's validate_compatibility method
        mock_validate = Mock(return_value=False)
        plugin._integration.validate_compatibility = mock_validate  # type: ignore

        # Act
        result = plugin.validate_compatibility(text_prompt)

        # Assert
        mock_validate.assert_called_once_with(text_prompt)
        assert result is False

    # Test: Shutdown
    def test_shutdown_clears_initialized_flag(
        self, plugin: LiteLLMPlugin
    ) -> None:
        """Test that shutdown clears initialized flag."""
        # Arrange
        plugin.initialize({})
        assert plugin._initialized is True

        # Act
        plugin.shutdown()

        # Assert
        assert plugin._initialized is False

    # Test: Configuration management
    def test_get_config_returns_configuration(
        self, plugin: LiteLLMPlugin
    ) -> None:
        """Test that get_config returns plugin configuration."""
        # Arrange
        config = {"strict_validation": False, "custom_option": "value"}
        plugin.initialize(config)

        # Act
        result = plugin.get_config()

        # Assert
        assert result == config

    def test_get_config_returns_copy(self, plugin: LiteLLMPlugin) -> None:
        """Test that get_config returns a copy of configuration."""
        # Arrange
        plugin.initialize({"key": "value"})

        # Act
        config1 = plugin.get_config()
        config2 = plugin.get_config()

        # Assert
        assert config1 == config2
        assert config1 is not config2  # Different objects

    # Test: String representation
    def test_repr(self, plugin: LiteLLMPlugin) -> None:
        """Test string representation of plugin."""
        # Act
        result = repr(plugin)

        # Assert
        assert "LiteLLMPlugin" in result
        assert "name='litellm'" in result
        assert "version='1.0.0'" in result

    # Test: Error handling
    def test_initialization_failure_raises_plugin_error(self) -> None:
        """Test that initialization failures are wrapped in PluginError."""
        # Arrange
        plugin = LiteLLMPlugin()

        # Mock TemplateEngine to raise exception
        with (
            patch(
                "prompt_manager.plugins.litellm_plugin.TemplateEngine",
                side_effect=Exception("Template engine failed"),
            ),
            pytest.raises(PluginError, match="Failed to initialize LiteLLM"),
        ):
            # Act
            plugin.initialize({})

    def test_render_with_null_integration_raises_error(
        self, plugin: LiteLLMPlugin, text_prompt: Prompt
    ) -> None:
        """Test that rendering with null integration raises PluginError."""
        # Arrange
        plugin.initialize({})
        plugin._integration = None  # Simulate null integration
        plugin._initialized = True  # But keep initialized flag

        # Act & Assert
        with pytest.raises(PluginError, match="Integration not initialized"):
            plugin.render_for_framework(text_prompt, {})

    def test_validate_with_null_integration_raises_error(
        self, plugin: LiteLLMPlugin, text_prompt: Prompt
    ) -> None:
        """Test that validation with null integration raises PluginError."""
        # Arrange
        plugin.initialize({})
        plugin._integration = None  # Simulate null integration
        plugin._initialized = True  # But keep initialized flag

        # Act & Assert
        with pytest.raises(PluginError, match="Integration not initialized"):
            plugin.validate_compatibility(text_prompt)

    # Test: Multiple formats
    def test_render_multiple_format_prompts(
        self, plugin: LiteLLMPlugin, text_prompt: Prompt, chat_prompt: Prompt
    ) -> None:
        """Test rendering multiple different format prompts."""
        # Arrange
        plugin.initialize({})

        # Act
        text_result = plugin.render_for_framework(text_prompt, {"name": "Bob"})
        chat_result = plugin.render_for_framework(chat_prompt, {"topic": "ML"})

        # Assert
        assert isinstance(text_result, str)
        assert text_result == "Hello Bob!"

        assert isinstance(chat_result, list)
        assert len(chat_result) == 2
        assert chat_result[1]["content"] == "Tell me about ML."

    # Test: Reinitialization
    def test_reinitialization_allowed(self, plugin: LiteLLMPlugin) -> None:
        """Test that plugin can be reinitialized with different config."""
        # Arrange & Act
        plugin.initialize({"strict_validation": True})
        first_integration = plugin._integration

        plugin.initialize({"strict_validation": False})
        second_integration = plugin._integration

        # Assert
        assert first_integration is not second_integration
        assert second_integration.strict_validation is False
