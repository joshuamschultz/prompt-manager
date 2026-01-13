"""Unit tests for integration type definitions.

These tests validate that TypedDict classes accept valid data structures
and that the type system can catch type errors. Some tests require mypy
for full validation.
"""


from prompt_manager.integrations.types import (
    AnthropicMessage,
    AnthropicMessageDict,
    AnthropicRequest,
    AnthropicRequestDict,
    LiteLLMCompletion,
    LiteLLMMessage,
    OpenAIChatCompletion,
    OpenAIFunctionCallDict,
    OpenAIMessage,
    OpenAIMessageDict,
    OpenAIToolCallDict,
)


class TestOpenAIMessageDict:
    """Test OpenAIMessageDict TypedDict."""

    def test_minimal_valid_message(self) -> None:
        """Test creating a minimal valid OpenAI message."""
        message: OpenAIMessageDict = {
            "role": "user",
            "content": "Hello!",
        }

        assert message["role"] == "user"
        assert message["content"] == "Hello!"

    def test_message_with_name(self) -> None:
        """Test OpenAI message with name field."""
        message: OpenAIMessageDict = {
            "role": "user",
            "content": "Hello!",
            "name": "Alice",
        }

        assert message["name"] == "Alice"

    def test_message_with_tool_calls(self) -> None:
        """Test OpenAI message with tool_calls field."""
        message: OpenAIMessageDict = {
            "role": "assistant",
            "content": "Let me check the weather.",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": "{}"},
                }
            ],
        }

        assert len(message["tool_calls"]) == 1

    def test_message_with_function_call(self) -> None:
        """Test OpenAI message with deprecated function_call field."""
        message: OpenAIMessageDict = {
            "role": "assistant",
            "content": "Calling function...",
            "function_call": {"name": "get_weather", "arguments": "{}"},
        }

        assert message["function_call"]["name"] == "get_weather"

    def test_message_with_tool_call_id(self) -> None:
        """Test OpenAI message with tool_call_id (for function responses)."""
        message: OpenAIMessageDict = {
            "role": "tool",
            "content": '{"temperature": 72}',
            "tool_call_id": "call_123",
        }

        assert message["tool_call_id"] == "call_123"

    def test_message_with_structured_content(self) -> None:
        """Test OpenAI message with structured content (for vision)."""
        message: OpenAIMessageDict = {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
            ],
        }

        assert isinstance(message["content"], list)


class TestAnthropicMessageDict:
    """Test AnthropicMessageDict TypedDict."""

    def test_minimal_valid_message(self) -> None:
        """Test creating a minimal valid Anthropic message."""
        message: AnthropicMessageDict = {
            "role": "user",
            "content": "Hello, Claude!",
        }

        assert message["role"] == "user"
        assert message["content"] == "Hello, Claude!"

    def test_assistant_message(self) -> None:
        """Test Anthropic assistant message."""
        message: AnthropicMessageDict = {
            "role": "assistant",
            "content": "Hello! How can I help you today?",
        }

        assert message["role"] == "assistant"

    def test_message_with_structured_content(self) -> None:
        """Test Anthropic message with structured content array."""
        message: AnthropicMessageDict = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this image"},
                {"type": "image", "source": {"type": "url", "url": "https://example.com/img.jpg"}},
            ],
        }

        assert isinstance(message["content"], list)


class TestOpenAIFunctionCallDict:
    """Test OpenAIFunctionCallDict TypedDict."""

    def test_valid_function_call(self) -> None:
        """Test creating a valid function call."""
        function_call: OpenAIFunctionCallDict = {
            "name": "get_weather",
            "arguments": '{"location": "San Francisco", "unit": "fahrenheit"}',
        }

        assert function_call["name"] == "get_weather"
        assert "San Francisco" in function_call["arguments"]


class TestOpenAIToolCallDict:
    """Test OpenAIToolCallDict TypedDict."""

    def test_valid_tool_call(self) -> None:
        """Test creating a valid tool call."""
        tool_call: OpenAIToolCallDict = {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"location": "NYC"}',
            },
        }

        assert tool_call["id"] == "call_abc123"
        assert tool_call["type"] == "function"
        assert tool_call["function"]["name"] == "get_weather"


class TestAnthropicRequestDict:
    """Test AnthropicRequestDict TypedDict."""

    def test_minimal_valid_request(self) -> None:
        """Test creating a minimal valid Anthropic request."""
        request: AnthropicRequestDict = {
            "model": "claude-3-opus-20240229",
            "messages": [{"role": "user", "content": "Hello!"}],
            "max_tokens": 1024,
        }

        assert request["model"] == "claude-3-opus-20240229"
        assert request["max_tokens"] == 1024
        assert len(request["messages"]) == 1

    def test_request_with_system_message(self) -> None:
        """Test Anthropic request with system message."""
        request: AnthropicRequestDict = {
            "model": "claude-3-opus-20240229",
            "messages": [{"role": "user", "content": "Hello!"}],
            "max_tokens": 1024,
            "system": "You are a helpful assistant.",
        }

        assert request["system"] == "You are a helpful assistant."

    def test_request_with_temperature(self) -> None:
        """Test Anthropic request with temperature parameter."""
        request: AnthropicRequestDict = {
            "model": "claude-3-opus-20240229",
            "messages": [{"role": "user", "content": "Hello!"}],
            "max_tokens": 1024,
            "temperature": 0.7,
        }

        assert request["temperature"] == 0.7

    def test_request_with_all_optional_fields(self) -> None:
        """Test Anthropic request with all optional fields."""
        request: AnthropicRequestDict = {
            "model": "claude-3-opus-20240229",
            "messages": [{"role": "user", "content": "Hello!"}],
            "max_tokens": 1024,
            "system": "You are helpful.",
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "stop_sequences": ["STOP"],
            "stream": False,
            "metadata": {"user_id": "12345"},
        }

        assert request["top_p"] == 0.9
        assert request["top_k"] == 50
        assert request["stop_sequences"] == ["STOP"]
        assert request["stream"] is False
        assert request["metadata"]["user_id"] == "12345"


class TestTypeAliases:
    """Test type aliases work correctly."""

    def test_openai_message_alias(self) -> None:
        """Test OpenAIMessage type alias."""
        message: OpenAIMessage = {"role": "user", "content": "Hello!"}

        assert message["role"] == "user"

    def test_openai_chat_completion_alias(self) -> None:
        """Test OpenAIChatCompletion type alias."""
        completion: OpenAIChatCompletion = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
        ]

        assert len(completion) == 2

    def test_anthropic_message_alias(self) -> None:
        """Test AnthropicMessage type alias."""
        message: AnthropicMessage = {"role": "user", "content": "Hello!"}

        assert message["role"] == "user"

    def test_anthropic_request_alias(self) -> None:
        """Test AnthropicRequest type alias."""
        request: AnthropicRequest = {
            "model": "claude-3-opus-20240229",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 100,
        }

        assert request["model"] == "claude-3-opus-20240229"

    def test_litellm_message_alias(self) -> None:
        """Test LiteLLMMessage type alias (OpenAI-compatible)."""
        message: LiteLLMMessage = {"role": "user", "content": "Hello!"}

        assert message["role"] == "user"

    def test_litellm_completion_alias(self) -> None:
        """Test LiteLLMCompletion type alias (OpenAI-compatible)."""
        completion: LiteLLMCompletion = [
            {"role": "user", "content": "Hello!"},
        ]

        assert len(completion) == 1


class TestTypeCompatibility:
    """Test type compatibility between different message formats."""

    def test_litellm_compatible_with_openai(self) -> None:
        """Test that LiteLLM messages are compatible with OpenAI format."""
        openai_msg: OpenAIMessage = {"role": "user", "content": "Hello"}
        litellm_msg: LiteLLMMessage = openai_msg  # Should be compatible

        assert litellm_msg["role"] == "user"

    def test_litellm_completion_compatible_with_openai(self) -> None:
        """Test that LiteLLM completions are compatible with OpenAI format."""
        openai_completion: OpenAIChatCompletion = [
            {"role": "user", "content": "Hello"}
        ]
        litellm_completion: LiteLLMCompletion = openai_completion  # Compatible

        assert len(litellm_completion) == 1


class TestMessageValidation:
    """Test that message structures are validated correctly."""

    def test_openai_message_requires_role_and_content(self) -> None:
        """Test that OpenAI messages conceptually need role and content."""
        # TypedDict doesn't enforce required fields at runtime
        # This test documents the expected structure
        message: OpenAIMessageDict = {
            "role": "user",
            "content": "Test",
        }

        assert "role" in message
        assert "content" in message

    def test_anthropic_message_requires_role_and_content(self) -> None:
        """Test that Anthropic messages conceptually need role and content."""
        message: AnthropicMessageDict = {
            "role": "user",
            "content": "Test",
        }

        assert "role" in message
        assert "content" in message

    def test_anthropic_request_requires_model_messages_max_tokens(self) -> None:
        """Test that Anthropic requests need required fields."""
        request: AnthropicRequestDict = {
            "model": "claude-3-opus-20240229",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 1024,
        }

        assert "model" in request
        assert "messages" in request
        assert "max_tokens" in request


class TestComplexMessageStructures:
    """Test complex message structures with multiple features."""

    def test_openai_multimodal_message(self) -> None:
        """Test OpenAI message with multimodal content."""
        message: OpenAIMessageDict = {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high",
                    },
                },
            ],
            "name": "ImageAnalyzer",
        }

        assert isinstance(message["content"], list)
        assert message["name"] == "ImageAnalyzer"

    def test_openai_function_calling_conversation(self) -> None:
        """Test OpenAI conversation with function calling."""
        messages: OpenAIChatCompletion = [
            {"role": "user", "content": "What's the weather?"},
            {
                "role": "assistant",
                "content": "Let me check that for you.",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "SF"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "content": '{"temperature": 72, "condition": "sunny"}',
                "tool_call_id": "call_123",
            },
            {
                "role": "assistant",
                "content": "It's 72°F and sunny in San Francisco!",
            },
        ]

        assert len(messages) == 4
        assert messages[1]["tool_calls"] is not None
        assert messages[2]["tool_call_id"] == "call_123"

    def test_anthropic_multimodal_request(self) -> None:
        """Test Anthropic request with multimodal content."""
        request: AnthropicRequestDict = {
            "model": "claude-3-opus-20240229",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image:"},
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": "https://example.com/image.jpg",
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 1024,
            "system": "You are an image analysis expert.",
        }

        assert isinstance(request["messages"][0]["content"], list)
        assert request["system"] is not None
