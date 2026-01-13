"""End-to-end tests for plugin discovery and registration."""

import pytest

from prompt_manager.plugins.registry import PluginRegistry


class TestPluginDiscoveryE2E:
    @pytest.mark.integration
    def test_plugin_registry_initialization(self):
        """Test that plugin registry can be initialized."""
        registry = PluginRegistry()
        assert registry is not None

    @pytest.mark.integration
    def test_openai_plugin_registration(self):
        """Test that OpenAI plugin can be loaded."""
        from prompt_manager.plugins.openai_plugin import OpenAIPlugin

        plugin = OpenAIPlugin()
        plugin.initialize({})

        assert plugin.name == "openai"
        assert plugin.version == "1.0.0"

    @pytest.mark.integration
    def test_plugin_provides_integration(self):
        """Test that plugin provides integration functionality."""
        from prompt_manager.core.models import Prompt, PromptFormat, PromptTemplate
        from prompt_manager.plugins.openai_plugin import OpenAIPlugin

        plugin = OpenAIPlugin()
        plugin.initialize({})

        prompt = Prompt(
            id="test",
            format=PromptFormat.TEXT,
            template=PromptTemplate(content="Hello!"),
        )

        result = plugin.render_for_framework(prompt, {})
        assert isinstance(result, str)
        assert "Hello!" in result
