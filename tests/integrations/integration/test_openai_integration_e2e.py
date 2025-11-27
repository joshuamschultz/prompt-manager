"""End-to-end integration tests for OpenAI SDK integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from prompt_manager.core.models import (
    Prompt,
    PromptFormat,
    PromptTemplate,
    ChatPromptTemplate,
    Message,
    Role,
)
from prompt_manager.core.template import TemplateEngine
from prompt_manager.integrations.openai import OpenAIIntegration


@pytest.fixture
def template_engine():
    """Provide template engine for tests."""
    return TemplateEngine()


@pytest.fixture
def openai_integration(template_engine):
    """Provide OpenAI integration instance."""
    return OpenAIIntegration(template_engine)


class TestOpenAITextCompletionE2E:
    """Test OpenAI text completion end-to-end workflow."""

    @pytest.mark.integration
    def test_text_prompt_to_openai_completion(self, openai_integration):
        """Test converting text prompt to OpenAI completion format."""
        # Create prompt
        prompt = Prompt(
            id="greeting",
            format=PromptFormat.TEXT,
            template=PromptTemplate(
                content="Hello {{name}}! Welcome to {{company}}."
            ),
        )

        # Convert to OpenAI format
        result = openai_integration.convert(
            prompt,
            {"name": "Alice", "company": "Acme Corp"},
        )

        # Verify format
        assert isinstance(result, str)
        assert "Hello Alice!" in result
        assert "Welcome to Acme Corp" in result

    @pytest.mark.integration
    def test_text_prompt_with_openai_sdk(self, openai_integration):
        """Test text prompt works with OpenAI SDK (mocked)."""
        prompt = Prompt(
            id="question",
            format=PromptFormat.TEXT,
            template=PromptTemplate(
                content="Answer this question: {{question}}"
            ),
        )

        # Convert prompt
        text = openai_integration.convert(
            prompt,
            {"question": "What is Python?"},
        )

        # Mock OpenAI SDK call
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].text = "Python is a programming language."

            mock_client = AsyncMock()
            mock_client.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Use with OpenAI SDK (mocked)
            import openai

            client = openai.AsyncOpenAI(api_key="test-key")
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=text,
            )

            # Verify SDK was called correctly
            assert mock_client.completions.create.called
            call_args = mock_client.completions.create.call_args
            assert call_args.kwargs["prompt"] == text
            assert response.choices[0].text


class TestOpenAIChatCompletionE2E:
    """Test OpenAI chat completion end-to-end workflow."""

    @pytest.mark.integration
    def test_chat_prompt_to_openai_messages(self, openai_integration):
        """Test converting chat prompt to OpenAI messages format."""
        # Create chat prompt
        prompt = Prompt(
            id="customer_support",
            format=PromptFormat.CHAT,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(
                        role=Role.SYSTEM,
                        content="You are a helpful {{company}} support agent.",
                    ),
                    Message(
                        role=Role.USER,
                        content="{{user_query}}",
                    ),
                ]
            ),
        )

        # Convert to OpenAI format
        messages = openai_integration.convert(
            prompt,
            {
                "company": "Acme Corp",
                "user_query": "How do I reset my password?",
            },
        )

        # Verify format
        assert isinstance(messages, list)
        assert len(messages) == 2

        # Verify system message
        assert messages[0]["role"] == "system"
        assert "Acme Corp" in messages[0]["content"]

        # Verify user message
        assert messages[1]["role"] == "user"
        assert "reset my password" in messages[1]["content"]

    @pytest.mark.integration
    def test_chat_prompt_with_openai_sdk(self, openai_integration):
        """Test chat prompt works with OpenAI SDK (mocked)."""
        prompt = Prompt(
            id="assistant",
            format=PromptFormat.CHAT,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(
                        role=Role.SYSTEM,
                        content="You are a helpful assistant.",
                    ),
                    Message(
                        role=Role.USER,
                        content="{{user_message}}",
                    ),
                ]
            ),
        )

        # Convert prompt
        messages = openai_integration.convert(
            prompt,
            {"user_message": "Tell me a joke"},
        )

        # Mock OpenAI SDK call
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Why did the chicken cross the road?"

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Use with OpenAI SDK (mocked)
            import openai

            client = openai.AsyncOpenAI(api_key="test-key")
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
            )

            # Verify SDK was called correctly
            assert mock_client.chat.completions.create.called
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["messages"] == messages
            assert response.choices[0].message.content


class TestOpenAIFunctionCallingE2E:
    """Test OpenAI function calling end-to-end workflow."""

    @pytest.mark.integration
    def test_chat_with_function_call(self, openai_integration):
        """Test chat prompt with function calling metadata."""
        prompt = Prompt(
            id="function_caller",
            format=PromptFormat.CHAT,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(
                        role=Role.USER,
                        content="What's the weather in {{location}}?",
                    ),
                ]
            ),
        )

        # Convert prompt
        messages = openai_integration.convert(
            prompt,
            {"location": "San Francisco"},
        )

        # Mock OpenAI SDK call with function calling
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.function_call = MagicMock()
            mock_response.choices[0].message.function_call.name = "get_weather"
            mock_response.choices[0].message.function_call.arguments = '{"location": "San Francisco"}'

            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Use with OpenAI SDK (mocked)
            import openai

            client = openai.AsyncOpenAI(api_key="test-key")

            # Define function
            functions = [
                {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                        },
                    },
                }
            ]

            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                functions=functions,
            )

            # Verify function call in response
            assert response.choices[0].message.function_call.name == "get_weather"


class TestOpenAIVariableSubstitutionE2E:
    """Test variable substitution in OpenAI integration."""

    @pytest.mark.integration
    def test_multiple_variables_in_chat(self, openai_integration):
        """Test multiple variable substitution in chat messages."""
        prompt = Prompt(
            id="personalized_chat",
            format=PromptFormat.CHAT,
            chat_template=ChatPromptTemplate(
                messages=[
                    Message(
                        role=Role.SYSTEM,
                        content="You are {{assistant_name}}, a {{role}} at {{company}}.",
                    ),
                    Message(
                        role=Role.USER,
                        content="Hello, I'm {{user_name}}. {{greeting}}",
                    ),
                ]
            ),
        )

        # Convert with multiple variables
        messages = openai_integration.convert(
            prompt,
            {
                "assistant_name": "Alex",
                "role": "customer success manager",
                "company": "TechCorp",
                "user_name": "Bob",
                "greeting": "How can you help me today?",
            },
        )

        # Verify all variables substituted
        assert "Alex" in messages[0]["content"]
        assert "customer success manager" in messages[0]["content"]
        assert "TechCorp" in messages[0]["content"]
        assert "Bob" in messages[1]["content"]
        assert "How can you help me today?" in messages[1]["content"]

    @pytest.mark.integration
    def test_complex_template_all_variables(self, openai_integration):
        """Test complex template with all variables provided."""
        prompt = Prompt(
            id="complex_template",
            format=PromptFormat.TEXT,
            template=PromptTemplate(
                content="Welcome to {{company}}! {{greeting}} Contact us at {{email}}.",
            ),
        )

        # Convert with all variables
        result = openai_integration.convert(
            prompt,
            {
                "company": "Acme Corp",
                "greeting": "We're here to help.",
                "email": "support@acme.com",
            },
        )

        # Verify all variables substituted
        assert "Acme Corp" in result
        assert "We're here to help" in result
        assert "support@acme.com" in result


class TestOpenAIErrorHandlingE2E:
    """Test error handling in OpenAI integration end-to-end."""

    @pytest.mark.integration
    def test_missing_variable_raises_error(self, openai_integration):
        """Test that missing required variable raises error."""
        from prompt_manager.exceptions import ConversionError

        prompt = Prompt(
            id="test",
            format=PromptFormat.TEXT,
            template=PromptTemplate(content="Hello {{name}}!"),
        )

        # Should raise error for missing variable
        with pytest.raises(ConversionError):
            openai_integration.convert(prompt, {})
