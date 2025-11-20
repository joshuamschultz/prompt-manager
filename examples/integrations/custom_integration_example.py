"""
Custom Integration Example

This example demonstrates how to create a custom framework integration for Prompt Manager.
Learn how to:
1. Extend BaseIntegration class
2. Implement required protocol methods
3. Handle framework-specific requirements
4. Create a plugin for auto-discovery (optional)

This is a complete, working example that you can use as a template for your own integrations.

Requirements:
    pip install agentic-prompt-manager

Usage:
    python custom_integration_example.py
"""

import asyncio
from collections.abc import Mapping
from typing import Any, TypedDict

from prompt_manager import PromptManager, Prompt
from prompt_manager.core.models import (
    PromptFormat,
    PromptTemplate,
    PromptStatus,
    ChatPromptTemplate,
    Message,
    Role,
)
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import InMemoryStorage
from prompt_manager.core.template import TemplateEngine
from prompt_manager.integrations.base import BaseIntegration
from prompt_manager.exceptions import IntegrationError


# Step 1: Define your framework's types
class MyFrameworkMessage(TypedDict, total=False):
    """Message format for MyFramework."""
    type: str  # "system", "user", "assistant"
    text: str
    metadata: dict[str, Any]  # Optional metadata


class MyFrameworkPrompt(TypedDict):
    """Complete prompt format for MyFramework."""
    messages: list[MyFrameworkMessage]
    config: dict[str, Any]


# Step 2: Create integration class
class MyFrameworkIntegration(BaseIntegration[MyFrameworkPrompt]):
    """
    Custom integration for MyFramework.

    This integration converts Prompt Manager prompts to MyFramework's format.
    """

    async def convert(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> MyFrameworkPrompt:
        """
        Convert Prompt Manager prompt to MyFramework format.

        Args:
            prompt: Prompt to convert
            variables: Variables for template rendering

        Returns:
            MyFrameworkPrompt with messages and config

        Raises:
            IntegrationError: If conversion fails
        """
        # Validate compatibility first
        if not self.validate_compatibility(prompt):
            raise IntegrationError(
                f"Prompt format {prompt.format} not supported by MyFramework. "
                f"MyFramework only supports CHAT format."
            )

        # Route to appropriate conversion method
        if prompt.format == PromptFormat.CHAT:
            return await self._convert_chat(prompt, variables)
        else:
            # Fallback for TEXT format (convert to single user message)
            return await self._convert_text(prompt, variables)

    async def _convert_chat(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> MyFrameworkPrompt:
        """Convert CHAT format prompt."""
        if not prompt.chat_template:
            raise IntegrationError("Chat template required for CHAT format")

        messages: list[MyFrameworkMessage] = []

        for msg in prompt.chat_template.messages:
            # Render message content with variables
            rendered = await self.template_engine.render(
                msg.content,
                variables,
            )

            # Convert to framework format
            framework_msg: MyFrameworkMessage = {
                "type": self._map_role(msg.role),
                "text": rendered,
            }

            # Add metadata if available
            if msg.name or msg.function_call or msg.tool_calls:
                framework_msg["metadata"] = {
                    "name": msg.name,
                    "function_call": msg.function_call,
                    "tool_calls": msg.tool_calls,
                }

            messages.append(framework_msg)

        # Return framework-specific format
        return MyFrameworkPrompt(
            messages=messages,
            config={
                "temperature": 0.7,  # Framework default
                "max_tokens": 1000,
            }
        )

    async def _convert_text(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> MyFrameworkPrompt:
        """Convert TEXT format prompt to framework format."""
        if not prompt.template:
            raise IntegrationError("Template required for TEXT format")

        # Render template
        rendered = await self.template_engine.render(
            prompt.template.content,
            variables,
            partials=prompt.template.partials,
        )

        # Convert to single user message
        messages: list[MyFrameworkMessage] = [{
            "type": "user",
            "text": rendered,
        }]

        return MyFrameworkPrompt(
            messages=messages,
            config={"temperature": 0.7}
        )

    def _map_role(self, role: Role) -> str:
        """
        Map Prompt Manager roles to MyFramework types.

        MyFramework uses: "system", "user", "assistant"
        """
        mapping = {
            Role.SYSTEM: "system",
            Role.USER: "user",
            Role.ASSISTANT: "assistant",
            Role.FUNCTION: "user",  # Framework doesn't support function, map to user
            Role.TOOL: "user",      # Framework doesn't support tool, map to user
        }

        if role not in mapping:
            raise IntegrationError(f"Unsupported role for MyFramework: {role}")

        return mapping[role]

    def validate_compatibility(self, prompt: Prompt) -> bool:
        """
        Validate prompt compatibility with MyFramework.

        MyFramework supports CHAT format primarily, but can handle TEXT.

        Returns:
            True if compatible
        """
        # MyFramework prefers CHAT format but can handle TEXT
        return prompt.format in (PromptFormat.CHAT, PromptFormat.TEXT)


# Optional Step 3: Create plugin for auto-discovery
from prompt_manager.plugins.base import BasePlugin


class MyFrameworkPlugin(BasePlugin):
    """Plugin for MyFramework integration with auto-discovery."""

    def __init__(self):
        super().__init__(
            name="myframework",
            version="1.0.0",
        )
        self._integration: MyFrameworkIntegration | None = None

    async def _initialize_impl(self, config: Mapping[str, Any]) -> None:
        """Initialize the integration."""
        # Create template engine
        template_engine = TemplateEngine()

        # Create integration instance
        self._integration = MyFrameworkIntegration(
            template_engine=template_engine,
            strict_validation=config.get("strict_validation", True),
        )

    async def render_for_framework(
        self,
        prompt: Prompt,
        variables: Mapping[str, Any],
    ) -> Any:
        """Render prompt in MyFramework format."""
        self._ensure_initialized()
        assert self._integration is not None
        return await self._integration.convert(prompt, variables)

    async def validate_compatibility(self, prompt: Prompt) -> bool:
        """Validate prompt compatibility."""
        self._ensure_initialized()
        assert self._integration is not None
        return self._integration.validate_compatibility(prompt)


# Example usage
async def example_basic_usage():
    """Example: Basic custom integration usage."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Custom Integration Usage")
    print("=" * 60)

    # Setup
    storage = InMemoryStorage()
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)
    template_engine = TemplateEngine()

    # Create custom integration
    integration = MyFrameworkIntegration(template_engine)

    # Create a chat prompt
    prompt = Prompt(
        id="test_prompt",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(role=Role.SYSTEM, content="You are a helpful assistant."),
                Message(role=Role.USER, content="{{question}}"),
            ],
            variables=["question"],
        ),
    )

    # Convert to MyFramework format
    result = await integration.convert(prompt, {"question": "What is AI?"})

    print(f"\nCustom Framework Format:")
    print(f"Messages: {len(result['messages'])}")
    for i, msg in enumerate(result['messages']):
        print(f"  {i + 1}. {msg['type']:9} - {msg['text'][:60]}...")
    print(f"Config: {result['config']}")


async def example_role_mapping():
    """Example: Custom role mapping."""
    print("\n" + "=" * 60)
    print("Example 2: Role Mapping")
    print("=" * 60)

    template_engine = TemplateEngine()
    integration = MyFrameworkIntegration(template_engine)

    # Test different roles
    roles_to_test = [Role.SYSTEM, Role.USER, Role.ASSISTANT, Role.FUNCTION]

    print("\nRole mapping:")
    for role in roles_to_test:
        try:
            mapped = integration._map_role(role)
            print(f"  {role.value:10} → {mapped}")
        except IntegrationError as e:
            print(f"  {role.value:10} → Error: {e}")


async def example_compatibility_validation():
    """Example: Compatibility validation."""
    print("\n" + "=" * 60)
    print("Example 3: Compatibility Validation")
    print("=" * 60)

    template_engine = TemplateEngine()
    integration = MyFrameworkIntegration(template_engine)

    # Test different formats
    formats_to_test = [
        (PromptFormat.CHAT, "CHAT format (preferred)"),
        (PromptFormat.TEXT, "TEXT format (supported)"),
        (PromptFormat.COMPLETION, "COMPLETION format"),
    ]

    print("\nCompatibility check:")
    for fmt, description in formats_to_test:
        if fmt == PromptFormat.CHAT:
            prompt = Prompt(
                id="test",
                version="1.0.0",
                format=fmt,
                status=PromptStatus.ACTIVE,
                chat_template=ChatPromptTemplate(messages=[]),
            )
        else:
            prompt = Prompt(
                id="test",
                version="1.0.0",
                format=fmt,
                status=PromptStatus.ACTIVE,
                template=PromptTemplate(content="test"),
            )

        compatible = integration.validate_compatibility(prompt)
        status = "✓ Compatible" if compatible else "✗ Not compatible"
        print(f"  {description:30} {status}")


async def example_plugin_usage():
    """Example: Using the plugin."""
    print("\n" + "=" * 60)
    print("Example 4: Plugin Usage")
    print("=" * 60)

    # Create and initialize plugin
    plugin = MyFrameworkPlugin()
    await plugin.initialize({})

    print(f"\nPlugin info:")
    print(f"  Name: {plugin.name}")
    print(f"  Version: {plugin.version}")
    print(f"  Initialized: {plugin.is_initialized}")

    # Use plugin to render
    prompt = Prompt(
        id="test",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(role=Role.USER, content="Hello {{name}}!"),
            ],
            variables=["name"],
        ),
    )

    result = await plugin.render_for_framework(prompt, {"name": "World"})
    print(f"\nRendered via plugin:")
    print(f"  Messages: {len(result['messages'])}")
    print(f"  First message: {result['messages'][0]}")


async def main():
    """Run all examples."""
    print("Custom Integration Example")
    print("=" * 60)
    print("\nThis example shows how to create a custom framework integration.")
    print("Use this as a template for integrating Prompt Manager with your framework.")

    await example_basic_usage()
    await example_role_mapping()
    await example_compatibility_validation()
    await example_plugin_usage()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Customize MyFrameworkIntegration for your framework")
    print("  2. Implement your framework's specific message format")
    print("  3. Add custom validation logic")
    print("  4. Create plugin for auto-discovery (optional)")
    print("  5. Add entry point in pyproject.toml (for plugins)")
    print("\nSee docs/INTEGRATION_GUIDE.md for detailed guide")


if __name__ == "__main__":
    asyncio.run(main())
