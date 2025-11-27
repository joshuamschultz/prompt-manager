"""End-to-end integration tests for LiteLLM integration."""

import pytest
from prompt_manager.core.models import (
    Prompt,
    PromptFormat,
    PromptTemplate,
    ChatPromptTemplate,
    Message,
    Role,
)
from prompt_manager.core.template import TemplateEngine
from prompt_manager.integrations.litellm import LiteLLMIntegration


@pytest.fixture
def template_engine():
    return TemplateEngine()


@pytest.fixture
def litellm_integration(template_engine):
    return LiteLLMIntegration(template_engine)


class TestLiteLLME2E:
    @pytest.mark.integration
    def test_text_prompt(self, litellm_integration):
        """Test text prompt conversion (delegates to OpenAI format)."""
        prompt = Prompt(
            id="test",
            format=PromptFormat.TEXT,
            template=PromptTemplate(content="Hello {{name}}!"),
        )

        result = litellm_integration.convert(prompt, {"name": "World"})

        assert isinstance(result, str)
        assert "Hello World!" in result

    @pytest.mark.integration
    def test_chat_prompt(self, litellm_integration):
        """Test chat prompt conversion (delegates to OpenAI format)."""
        prompt = Prompt(
            id="test",
            format=PromptFormat.CHAT,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="{{message}}"),
                ]
            ),
        )

        result = litellm_integration.convert(prompt, {"message": "Hi!"})

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert "Hi!" in result[0]["content"]
