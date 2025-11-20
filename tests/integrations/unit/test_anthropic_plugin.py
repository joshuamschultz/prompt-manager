"""Unit tests for Anthropic plugin."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

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
from prompt_manager.plugins.anthropic_plugin import AnthropicPlugin


class TestAnthropicPlugin:
    """Test suite for AnthropicPlugin class."""

    @pytest.fixture
    def plugin(self) -> AnthropicPlugin:
        """Create an AnthropicPlugin instance."""
        return AnthropicPlugin()

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

    @pytest.fixture
    def text_prompt(self) -> Prompt:
        """Create a TEXT format prompt (not compatible with Anthropic)."""
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

    # Test: Plugin initialization
    def test_plugin_name(self, plugin: AnthropicPlugin) -> None:
        """Test that plugin has correct name."""
        assert plugin.name == "anthropic"

    def test_plugin_version(self, plugin: AnthropicPlugin) -> None:
        """Test that plugin has correct version."""
        assert plugin.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_plugin_initialization_default_config(
        self, plugin: AnthropicPlugin
    ) -> None:
        """Test plugin initialization with default configuration."""
        # Act
        await plugin.initialize({})

        # Assert
        assert plugin._initialized is True
        assert plugin._integration is not None

    @pytest.mark.asyncio
    async def test_plugin_initialization_with_strict_validation_true(
        self, plugin: AnthropicPlugin
    ) -> None:
        """Test plugin initialization with strict_validation=True."""
        # Act
        await plugin.initialize({"strict_validation": True})

        # Assert
        assert plugin._integration is not None
        assert plugin._integration.strict_validation is True

    @pytest.mark.asyncio
    async def test_plugin_initialization_with_strict_validation_false(
        self, plugin: AnthropicPlugin
    ) -> None:
        """Test plugin initialization with strict_validation=False."""
        # Act
        await plugin.initialize({"strict_validation": False})

        # Assert
        assert plugin._integration is not None
        assert plugin._integration.strict_validation is False

    @pytest.mark.asyncio
    async def test_plugin_initialization_creates_template_engine(
        self, plugin: AnthropicPlugin
    ) -> None:
        """Test that plugin initialization creates template engine."""
        # Act
        await plugin.initialize({})

        # Assert
        assert plugin._integration is not None
        assert plugin._integration.template_engine is not None

    # Test: Render for framework
    @pytest.mark.asyncio
    async def test_render_for_framework_chat_prompt(
        self, plugin: AnthropicPlugin, chat_prompt: Prompt
    ) -> None:
        """Test rendering CHAT prompt."""
        # Arrange
        await plugin.initialize({})
        variables = {"topic": "AI"}

        # Act
        result = await plugin.render_for_framework(chat_prompt, variables)

        # Assert
        assert isinstance(result, dict)
        assert "messages" in result
        assert "system" in result
        assert result["system"] == "You are a helpful assistant."
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "Tell me about AI."

    @pytest.mark.asyncio
    async def test_render_for_framework_before_initialization_raises_error(
        self, plugin: AnthropicPlugin, chat_prompt: Prompt
    ) -> None:
        """Test that rendering before initialization raises PluginError."""
        # Act & Assert
        with pytest.raises(PluginError, match="not initialized"):
            await plugin.render_for_framework(chat_prompt, {})

    @pytest.mark.asyncio
    async def test_render_for_framework_delegates_to_integration(
        self, plugin: AnthropicPlugin, chat_prompt: Prompt
    ) -> None:
        """Test that render_for_framework delegates to integration.convert."""
        # Arrange
        await plugin.initialize({})

        # Mock the integration's convert method
        mock_result = {"messages": [{"role": "user", "content": "Mocked"}]}
        mock_convert = AsyncMock(return_value=mock_result)
        plugin._integration.convert = mock_convert  # type: ignore

        variables = {"topic": "Test"}

        # Act
        result = await plugin.render_for_framework(chat_prompt, variables)

        # Assert
        mock_convert.assert_called_once_with(chat_prompt, variables)
        assert result == mock_result

    # Test: Validate compatibility
    @pytest.mark.asyncio
    async def test_validate_compatibility_returns_true_for_chat(
        self, plugin: AnthropicPlugin, chat_prompt: Prompt
    ) -> None:
        """Test that Anthropic plugin is compatible with CHAT format."""
        # Arrange
        await plugin.initialize({})

        # Act
        result = await plugin.validate_compatibility(chat_prompt)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_compatibility_returns_false_for_text(
        self, plugin: AnthropicPlugin, text_prompt: Prompt
    ) -> None:
        """Test that Anthropic plugin is not compatible with TEXT format."""
        # Arrange
        await plugin.initialize({})

        # Act
        result = await plugin.validate_compatibility(text_prompt)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_compatibility_before_initialization_raises_error(
        self, plugin: AnthropicPlugin, chat_prompt: Prompt
    ) -> None:
        """Test that validation before initialization raises PluginError."""
        # Act & Assert
        with pytest.raises(PluginError, match="not initialized"):
            await plugin.validate_compatibility(chat_prompt)

    @pytest.mark.asyncio
    async def test_validate_compatibility_delegates_to_integration(
        self, plugin: AnthropicPlugin, chat_prompt: Prompt
    ) -> None:
        """Test that validate_compatibility delegates to integration."""
        # Arrange
        await plugin.initialize({})

        # Mock the integration's validate_compatibility method
        mock_validate = Mock(return_value=False)
        plugin._integration.validate_compatibility = mock_validate  # type: ignore

        # Act
        result = await plugin.validate_compatibility(chat_prompt)

        # Assert
        mock_validate.assert_called_once_with(chat_prompt)
        assert result is False

    # Test: Shutdown
    @pytest.mark.asyncio
    async def test_shutdown_clears_initialized_flag(
        self, plugin: AnthropicPlugin
    ) -> None:
        """Test that shutdown clears initialized flag."""
        # Arrange
        await plugin.initialize({})
        assert plugin._initialized is True

        # Act
        await plugin.shutdown()

        # Assert
        assert plugin._initialized is False

    # Test: Configuration management
    @pytest.mark.asyncio
    async def test_get_config_returns_configuration(
        self, plugin: AnthropicPlugin
    ) -> None:
        """Test that get_config returns plugin configuration."""
        # Arrange
        config = {"strict_validation": False, "custom_option": "value"}
        await plugin.initialize(config)

        # Act
        result = plugin.get_config()

        # Assert
        assert result == config

    @pytest.mark.asyncio
    async def test_get_config_returns_copy(self, plugin: AnthropicPlugin) -> None:
        """Test that get_config returns a copy of configuration."""
        # Arrange
        await plugin.initialize({"key": "value"})

        # Act
        config1 = plugin.get_config()
        config2 = plugin.get_config()

        # Assert
        assert config1 == config2
        assert config1 is not config2  # Different objects

    # Test: String representation
    def test_repr(self, plugin: AnthropicPlugin) -> None:
        """Test string representation of plugin."""
        # Act
        result = repr(plugin)

        # Assert
        assert "AnthropicPlugin" in result
        assert "name='anthropic'" in result
        assert "version='1.0.0'" in result

    # Test: Error handling
    @pytest.mark.asyncio
    async def test_initialization_failure_raises_plugin_error(self) -> None:
        """Test that initialization failures are wrapped in PluginError."""
        # Arrange
        plugin = AnthropicPlugin()

        # Mock TemplateEngine to raise exception
        with patch(
            "prompt_manager.plugins.anthropic_plugin.TemplateEngine",
            side_effect=Exception("Template engine failed"),
        ):
            # Act & Assert
            with pytest.raises(PluginError, match="Failed to initialize Anthropic"):
                await plugin.initialize({})

    @pytest.mark.asyncio
    async def test_render_with_null_integration_raises_error(
        self, plugin: AnthropicPlugin, chat_prompt: Prompt
    ) -> None:
        """Test that rendering with null integration raises PluginError."""
        # Arrange
        await plugin.initialize({})
        plugin._integration = None  # Simulate null integration
        plugin._initialized = True  # But keep initialized flag

        # Act & Assert
        with pytest.raises(PluginError, match="Integration not initialized"):
            await plugin.render_for_framework(chat_prompt, {})

    @pytest.mark.asyncio
    async def test_validate_with_null_integration_raises_error(
        self, plugin: AnthropicPlugin, chat_prompt: Prompt
    ) -> None:
        """Test that validation with null integration raises PluginError."""
        # Arrange
        await plugin.initialize({})
        plugin._integration = None  # Simulate null integration
        plugin._initialized = True  # But keep initialized flag

        # Act & Assert
        with pytest.raises(PluginError, match="Integration not initialized"):
            await plugin.validate_compatibility(chat_prompt)

    # Test: Reinitialization
    @pytest.mark.asyncio
    async def test_reinitialization_allowed(self, plugin: AnthropicPlugin) -> None:
        """Test that plugin can be reinitialized with different config."""
        # Arrange & Act
        await plugin.initialize({"strict_validation": True})
        first_integration = plugin._integration

        await plugin.initialize({"strict_validation": False})
        second_integration = plugin._integration

        # Assert
        assert first_integration is not second_integration
        assert second_integration.strict_validation is False
