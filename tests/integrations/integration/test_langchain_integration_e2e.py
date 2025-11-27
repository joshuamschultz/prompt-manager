"""End-to-end integration tests for LangChain integration."""

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
from prompt_manager.integrations.langchain import LangChainIntegration, LANGCHAIN_AVAILABLE


@pytest.fixture
def template_engine():
    return TemplateEngine()


@pytest.fixture
def langchain_integration(template_engine):
    if not LANGCHAIN_AVAILABLE:
        pytest.skip("LangChain not available")
    return LangChainIntegration(template_engine)


class TestLangChainE2E:
    @pytest.mark.integration
    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
    def test_text_to_prompt_template(self, langchain_integration):
        """Test converting text prompt to LangChain PromptTemplate."""
        prompt = Prompt(
            id="test",
            format=PromptFormat.TEXT,
            template=PromptTemplate(content="Hello {name}!"),
        )

        result = langchain_integration.convert(prompt, {})

        # Verify it's a LangChain PromptTemplate
        assert result is not None
        assert hasattr(result, "format")

    @pytest.mark.integration
    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
    def test_chat_to_chat_prompt_template(self, langchain_integration):
        """Test converting chat prompt to LangChain ChatPromptTemplate."""
        prompt = Prompt(
            id="test",
            format=PromptFormat.CHAT,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(role=Role.SYSTEM, content="You are {role}."),
                    Message(role=Role.USER, content="{message}"),
                ]
            ),
        )

        result = langchain_integration.convert(prompt, {})

        # Verify it's a LangChain ChatPromptTemplate
        assert result is not None
        assert hasattr(result, "format_messages")
