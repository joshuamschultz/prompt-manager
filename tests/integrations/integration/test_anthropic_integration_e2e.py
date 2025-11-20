"""End-to-end integration tests for Anthropic SDK integration."""

import pytest
from prompt_manager.core.models import (
    Prompt,
    PromptFormat,
    ChatPromptTemplate,
    Message,
    Role,
)
from prompt_manager.core.template import TemplateEngine
from prompt_manager.integrations.anthropic import AnthropicIntegration


@pytest.fixture
def template_engine():
    return TemplateEngine()


@pytest.fixture
def anthropic_integration(template_engine):
    return AnthropicIntegration(template_engine)


class TestAnthropicChatE2E:
    @pytest.mark.integration
    async def test_chat_with_system_message(self, anthropic_integration):
        """Test chat prompt with system message."""
        prompt = Prompt(
            id="test",
            format=PromptFormat.CHAT,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.SYSTEM, content="You are {{assistant_role}}."),
                    Message(role=Role.USER, content="{{question}}"),
                ]
            ),
        )

        result = await anthropic_integration.convert(
            prompt,
            {"assistant_role": "helpful assistant", "question": "Hello?"},
        )

        assert "system" in result
        assert "helpful assistant" in result["system"]
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"

    @pytest.mark.integration
    async def test_message_alternation(self, anthropic_integration):
        """Test message alternation validation."""
        prompt = Prompt(
            id="test",
            format=PromptFormat.CHAT,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.USER, content="Question 1"),
                    Message(role=Role.ASSISTANT, content="Answer 1"),
                    Message(role=Role.USER, content="Question 2"),
                ]
            ),
        )

        result = await anthropic_integration.convert(prompt, {})

        assert len(result["messages"]) == 3
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"
        assert result["messages"][2]["role"] == "user"
