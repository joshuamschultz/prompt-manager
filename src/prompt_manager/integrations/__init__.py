"""Framework integrations for Prompt Manager.

This module provides integrations with popular LLM frameworks, enabling seamless
conversion of Prompt Manager prompts to framework-specific formats.

Supported Integrations
----------------------
- **OpenAI**: Convert prompts to OpenAI SDK message format
- **Anthropic**: Convert prompts to Anthropic Messages API format
- **LangChain**: Convert prompts to LangChain template format
- **LiteLLM**: Convert prompts to LiteLLM (OpenAI-compatible) format

Usage
-----
Each integration implements the BaseIntegration protocol and provides
async conversion methods to transform prompts into framework-specific formats.

    from prompt_manager.integrations import OpenAIIntegration
    from prompt_manager import PromptManager

    manager = PromptManager(registry=registry)
    integration = OpenAIIntegration(template_engine=manager._engine)

    prompt = manager._registry.get("my_prompt")
    openai_messages = integration.convert(prompt, variables)

Lazy Loading
------------
Integrations are loaded on-demand to minimize import overhead and avoid
requiring all framework dependencies when only using a subset.

Custom Integrations
-------------------
To create a custom integration, extend BaseIntegration and implement:
- `convert()`: Transform prompt to framework format
- `validate_compatibility()`: Check if prompt is compatible

See docs/INTEGRATION_GUIDE.md for detailed implementation instructions.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from prompt_manager.integrations.base import BaseIntegration
    from prompt_manager.integrations.openai import OpenAIIntegration
    from prompt_manager.integrations.anthropic import AnthropicIntegration
    from prompt_manager.integrations.langchain import LangChainIntegration
    from prompt_manager.integrations.litellm import LiteLLMIntegration

__all__ = [
    "BaseIntegration",
    "OpenAIIntegration",
    "AnthropicIntegration",
    "LangChainIntegration",
    "LiteLLMIntegration",
]


def __getattr__(name: str) -> Any:
    """Lazy import pattern for framework integrations.

    This function enables on-demand importing of integration classes,
    avoiding the overhead of loading all framework dependencies when
    only a subset is needed.

    Args:
        name: The name of the attribute to import

    Returns:
        The requested integration class or base class

    Raises:
        AttributeError: If the requested name is not a valid export

    Example:
        >>> from prompt_manager.integrations import OpenAIIntegration
        >>> # Only openai.py is imported, not anthropic, langchain, etc.
    """
    if name == "BaseIntegration":
        from prompt_manager.integrations.base import BaseIntegration
        return BaseIntegration
    elif name == "OpenAIIntegration":
        from prompt_manager.integrations.openai import OpenAIIntegration
        return OpenAIIntegration
    elif name == "AnthropicIntegration":
        from prompt_manager.integrations.anthropic import AnthropicIntegration
        return AnthropicIntegration
    elif name == "LangChainIntegration":
        from prompt_manager.integrations.langchain import LangChainIntegration
        return LangChainIntegration
    elif name == "LiteLLMIntegration":
        from prompt_manager.integrations.litellm import LiteLLMIntegration
        return LiteLLMIntegration

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
