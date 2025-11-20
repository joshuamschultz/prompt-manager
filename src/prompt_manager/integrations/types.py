"""Type definitions for framework integrations.

This module provides type aliases and TypedDict classes for framework-specific
message formats. These types ensure type safety when converting prompts to
framework-native formats.
"""

from typing import Any, TypeAlias, TypedDict

# ============================================================================
# OpenAI Types
# ============================================================================

OpenAIMessage: TypeAlias = dict[str, Any]
"""Type alias for OpenAI message format.

OpenAI messages are dictionaries with flexible structure. The actual structure
is defined by the OpenAIMessageDict TypedDict below for better type checking.

Example:
    >>> message: OpenAIMessage = {
    ...     "role": "user",
    ...     "content": "Hello, world!"
    ... }

See Also:
    - OpenAIMessageDict: Typed dictionary version with specific fields
    - OpenAIChatCompletion: Type alias for message arrays
"""

OpenAIChatCompletion: TypeAlias = list[OpenAIMessage]
"""Type alias for OpenAI chat completion format.

An OpenAI chat completion is an array of messages representing a conversation.
This is the format expected by the OpenAI Chat Completions API.

Example:
    >>> completion: OpenAIChatCompletion = [
    ...     {"role": "system", "content": "You are a helpful assistant."},
    ...     {"role": "user", "content": "Hello!"},
    ...     {"role": "assistant", "content": "Hi there! How can I help?"}
    ... ]

Reference:
    https://platform.openai.com/docs/api-reference/chat/create
"""


# ============================================================================
# Anthropic Types
# ============================================================================

AnthropicMessage: TypeAlias = dict[str, Any]
"""Type alias for Anthropic message format.

Anthropic messages have a simpler structure than OpenAI, typically containing
just role and content fields. The actual structure is defined by the
AnthropicMessageDict TypedDict below.

Example:
    >>> message: AnthropicMessage = {
    ...     "role": "user",
    ...     "content": "Hello, Claude!"
    ... }

See Also:
    - AnthropicMessageDict: Typed dictionary version with specific fields
    - AnthropicRequest: Complete request payload type

Reference:
    https://docs.anthropic.com/claude/reference/messages_post
"""

AnthropicRequest: TypeAlias = dict[str, Any]
"""Type alias for complete Anthropic API request.

The Anthropic Messages API expects a request with system message (optional)
and messages array. This type represents the complete payload.

Example:
    >>> request: AnthropicRequest = {
    ...     "system": "You are a helpful assistant.",
    ...     "messages": [
    ...         {"role": "user", "content": "Hello!"},
    ...         {"role": "assistant", "content": "Hi there!"}
    ...     ],
    ...     "max_tokens": 1024,
    ...     "model": "claude-3-opus-20240229"
    ... }

Reference:
    https://docs.anthropic.com/claude/reference/messages_post
"""


# ============================================================================
# LangChain Types
# ============================================================================

LangChainPrompt: TypeAlias = Any
"""Type alias for LangChain prompt templates.

LangChain prompts can be various types depending on the template format:
- PromptTemplate for text prompts
- ChatPromptTemplate for chat-based prompts
- FewShotPromptTemplate for few-shot examples
- Other custom template types

This uses Any because LangChain has many prompt template classes and we want
to support all of them without creating tight coupling.

Example:
    >>> from langchain.prompts import PromptTemplate
    >>> template: LangChainPrompt = PromptTemplate(
    ...     input_variables=["name"],
    ...     template="Hello {name}!"
    ... )

Reference:
    https://python.langchain.com/docs/modules/model_io/prompts/
"""


# ============================================================================
# LiteLLM Types
# ============================================================================

# LiteLLM uses OpenAI-compatible format, so we reuse OpenAI types
LiteLLMMessage: TypeAlias = OpenAIMessage
"""Type alias for LiteLLM message format.

LiteLLM uses the same message format as OpenAI since it provides a unified
interface to multiple providers using OpenAI's format as the standard.

Example:
    >>> message: LiteLLMMessage = {
    ...     "role": "user",
    ...     "content": "Hello!"
    ... }

Reference:
    https://docs.litellm.ai/docs/completion/input
"""

LiteLLMCompletion: TypeAlias = OpenAIChatCompletion
"""Type alias for LiteLLM completion format.

LiteLLM completions follow the same array format as OpenAI chat completions
since LiteLLM acts as a proxy using OpenAI's format.

Example:
    >>> completion: LiteLLMCompletion = [
    ...     {"role": "system", "content": "You are helpful."},
    ...     {"role": "user", "content": "Hello!"}
    ... ]

Reference:
    https://docs.litellm.ai/docs/completion/input
"""


# ============================================================================
# TypedDict Definitions
# ============================================================================


class OpenAIMessageDict(TypedDict, total=False):
    """TypedDict for OpenAI message format with type safety.

    This provides a more structured type definition than the OpenAIMessage
    type alias, allowing mypy to catch missing or invalid fields.

    Attributes:
        role: The role of the message sender (required)
            Valid values: "system", "user", "assistant", "function", "tool"
        content: The message content (required)
            Can be string or structured content for vision models
        name: Optional name of the function/tool or user
        function_call: Deprecated function calling format (use tool_calls)
        tool_calls: Array of tool/function calls made by the assistant
        tool_call_id: ID of the tool call this message is responding to

    Example:
        >>> message: OpenAIMessageDict = {
        ...     "role": "user",
        ...     "content": "Hello, GPT!"
        ... }
        >>> # Type checker will catch missing 'role' or 'content'
        >>> # Type checker will catch invalid field names

    Reference:
        https://platform.openai.com/docs/api-reference/chat/create
    """

    role: str  # Required
    content: str | list[dict[str, Any]]  # Required
    name: str  # Optional
    function_call: dict[str, Any]  # Optional (deprecated)
    tool_calls: list[dict[str, Any]]  # Optional
    tool_call_id: str  # Optional


class AnthropicMessageDict(TypedDict, total=False):
    """TypedDict for Anthropic message format with type safety.

    Anthropic's message format is simpler than OpenAI's, focusing on role
    and content with optional metadata.

    Attributes:
        role: The role of the message sender (required)
            Valid values: "user", "assistant"
        content: The message content (required)
            Can be string or structured content array

    Example:
        >>> message: AnthropicMessageDict = {
        ...     "role": "user",
        ...     "content": "Hello, Claude!"
        ... }

    Note:
        Anthropic uses a separate 'system' field in the request payload
        rather than including system messages in the messages array.

    Reference:
        https://docs.anthropic.com/claude/reference/messages_post
    """

    role: str  # Required
    content: str | list[dict[str, Any]]  # Required


class OpenAIFunctionCallDict(TypedDict):
    """TypedDict for OpenAI function call format.

    Deprecated in favor of tool_calls, but still supported for compatibility.

    Attributes:
        name: The name of the function to call
        arguments: JSON string containing the function arguments

    Example:
        >>> function_call: OpenAIFunctionCallDict = {
        ...     "name": "get_weather",
        ...     "arguments": '{"location": "San Francisco"}'
        ... }

    Reference:
        https://platform.openai.com/docs/api-reference/chat/create
    """

    name: str
    arguments: str


class OpenAIToolCallDict(TypedDict):
    """TypedDict for OpenAI tool call format.

    The current standard for function/tool calling in OpenAI's API.

    Attributes:
        id: Unique identifier for this tool call
        type: The type of tool (currently only "function")
        function: The function call details

    Example:
        >>> tool_call: OpenAIToolCallDict = {
        ...     "id": "call_abc123",
        ...     "type": "function",
        ...     "function": {
        ...         "name": "get_weather",
        ...         "arguments": '{"location": "SF"}'
        ...     }
        ... }

    Reference:
        https://platform.openai.com/docs/api-reference/chat/create
    """

    id: str
    type: str
    function: OpenAIFunctionCallDict


class AnthropicRequestDict(TypedDict, total=False):
    """TypedDict for complete Anthropic API request payload.

    Defines the structure of a request to the Anthropic Messages API.

    Attributes:
        model: The model identifier (required)
        messages: Array of conversation messages (required)
        system: Optional system message (separate from messages array)
        max_tokens: Maximum tokens to generate (required)
        temperature: Sampling temperature 0-1 (optional)
        top_p: Nucleus sampling parameter (optional)
        top_k: Top-k sampling parameter (optional)
        metadata: Optional metadata for the request
        stop_sequences: Optional sequences that stop generation
        stream: Whether to stream the response (optional)

    Example:
        >>> request: AnthropicRequestDict = {
        ...     "model": "claude-3-opus-20240229",
        ...     "messages": [{"role": "user", "content": "Hello!"}],
        ...     "max_tokens": 1024,
        ...     "system": "You are a helpful assistant."
        ... }

    Reference:
        https://docs.anthropic.com/claude/reference/messages_post
    """

    model: str  # Required
    messages: list[AnthropicMessageDict]  # Required
    max_tokens: int  # Required
    system: str  # Optional
    temperature: float  # Optional
    top_p: float  # Optional
    top_k: int  # Optional
    metadata: dict[str, Any]  # Optional
    stop_sequences: list[str]  # Optional
    stream: bool  # Optional
