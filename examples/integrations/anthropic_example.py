"""
Anthropic SDK (Claude) Integration Example

This example demonstrates how to use Prompt Manager with the Anthropic SDK to:
1. Convert CHAT prompts to Anthropic/Claude message format
2. Handle system messages (Anthropic's single system message requirement)
3. Validate message alternation (user/assistant pattern)
4. Use prompts with Claude API

Requirements:
    pip install agentic-prompt-manager[anthropic]

Environment:
    ANTHROPIC_API_KEY=sk-ant-...  # Set this in .env file or environment

Usage:
    python anthropic_example.py
"""

import asyncio
import os

# Optional: Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from prompt_manager import PromptManager, Prompt
from prompt_manager.core.models import (
    PromptFormat,
    PromptStatus,
    PromptMetadata,
    ChatPromptTemplate,
    Message,
    Role,
)
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import InMemoryStorage
from prompt_manager.integrations import AnthropicIntegration


async def create_sample_prompts(manager: PromptManager) -> None:
    """Create sample prompts for demonstration."""

    # Basic chat prompt with system message
    basic_prompt = Prompt(
        id="claude_assistant",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="You are Claude, an AI assistant created by Anthropic. "
                    "You are helpful, harmless, and honest. Your expertise is in {{domain}}.",
                ),
                Message(
                    role=Role.USER,
                    content="{{user_question}}",
                ),
            ],
            variables=["domain", "user_question"],
        ),
        metadata=PromptMetadata(
            author="Example",
            description="Basic Claude assistant prompt",
            tags=["claude", "assistant"],
        ),
    )

    # Multi-turn conversation prompt
    conversation_prompt = Prompt(
        id="research_assistant",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="You are a research assistant specializing in {{research_area}}. "
                    "Provide detailed, well-researched responses with citations when possible.",
                ),
                Message(
                    role=Role.USER,
                    content="I need help researching: {{topic}}",
                ),
                Message(
                    role=Role.ASSISTANT,
                    content="I'd be happy to help you research {{topic}}. "
                    "What specific aspects would you like me to focus on?",
                ),
                Message(
                    role=Role.USER,
                    content="{{follow_up_question}}",
                ),
            ],
            variables=["research_area", "topic", "follow_up_question"],
        ),
        metadata=PromptMetadata(
            author="Example",
            description="Multi-turn research conversation",
            tags=["research", "multi-turn"],
        ),
    )

    await manager.create_prompt(basic_prompt)
    await manager.create_prompt(conversation_prompt)
    print("Created sample prompts: claude_assistant, research_assistant")


async def example_basic_conversion(
    manager: PromptManager,
    integration: AnthropicIntegration,
) -> None:
    """Example: Basic chat prompt conversion."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Anthropic Format Conversion")
    print("=" * 60)

    # Get prompt
    prompt = await manager.get_prompt("claude_assistant")
    print(f"\nPrompt ID: {prompt.id}")
    print(f"Format: {prompt.format.value}")
    print(f"Messages: {len(prompt.chat_template.messages)}")

    # Convert to Anthropic format
    result = await integration.convert(prompt, {
        "domain": "quantum computing",
        "user_question": "Explain quantum entanglement in simple terms",
    })

    print(f"\nAnthropic Format:")
    print(f"Type: {type(result)}")
    print(f"\nSystem message:")
    print(f"  {result.get('system', 'None')[:100]}...")
    print(f"\nMessages array:")
    for i, msg in enumerate(result["messages"]):
        print(f"  Message {i + 1}:")
        print(f"    Role: {msg['role']}")
        print(f"    Content: {msg['content'][:80]}...")


async def example_multi_turn_conversation(
    manager: PromptManager,
    integration: AnthropicIntegration,
) -> None:
    """Example: Multi-turn conversation with alternating messages."""
    print("\n" + "=" * 60)
    print("Example 2: Multi-Turn Conversation")
    print("=" * 60)

    # Get prompt
    prompt = await manager.get_prompt("research_assistant")
    print(f"\nPrompt ID: {prompt.id}")
    print(f"Messages in template: {len(prompt.chat_template.messages)}")

    # Convert to Anthropic format
    result = await integration.convert(prompt, {
        "research_area": "artificial intelligence",
        "topic": "transformer architectures",
        "follow_up_question": "How do attention mechanisms work?",
    })

    print(f"\nAnthropic Format:")
    print(f"System: {result.get('system', 'None')[:80]}...")
    print(f"\nMessage alternation (required by Anthropic):")
    for i, msg in enumerate(result["messages"]):
        print(f"  {i + 1}. {msg['role']:9} - {msg['content'][:60]}...")


async def example_with_anthropic_sdk(
    manager: PromptManager,
    integration: AnthropicIntegration,
    use_real_api: bool = False,
) -> None:
    """Example: Use converted prompt with Anthropic SDK."""
    print("\n" + "=" * 60)
    print("Example 3: Using with Anthropic SDK")
    print("=" * 60)

    # Get prompt and convert
    prompt = await manager.get_prompt("claude_assistant")
    result = await integration.convert(prompt, {
        "domain": "creative writing",
        "user_question": "Write a haiku about artificial intelligence",
    })

    print(f"\nConverted prompt ready for Claude API")
    print(f"System message: {bool(result.get('system'))}")
    print(f"User messages: {len(result['messages'])}")

    if use_real_api:
        # Real API call (requires ANTHROPIC_API_KEY)
        try:
            import anthropic

            client = anthropic.AsyncAnthropic()
            print("\nCalling Claude API...")

            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=result.get("system"),  # Optional system message
                messages=result["messages"],
            )

            print(f"\nResponse:")
            print(response.content[0].text)

        except Exception as e:
            print(f"\nError calling Anthropic API: {e}")
            print("Make sure ANTHROPIC_API_KEY is set in your environment")
    else:
        # Mock/demo mode
        print("\nDemo Mode: Would call Anthropic API with:")
        print(f"  Model: claude-3-5-sonnet-20241022")
        print(f"  System: {result.get('system', 'None')[:50]}...")
        print(f"  Messages: {len(result['messages'])} messages")
        print(f"\n(Set use_real_api=True to make actual API calls)")


async def example_system_message_handling(
    manager: PromptManager,
    integration: AnthropicIntegration,
) -> None:
    """Example: Anthropic's system message requirements."""
    print("\n" + "=" * 60)
    print("Example 4: System Message Handling")
    print("=" * 60)

    from prompt_manager.exceptions import IntegrationError

    # Create prompt with multiple system messages (invalid for Anthropic)
    invalid_prompt = Prompt(
        id="invalid_multi_system",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(role=Role.SYSTEM, content="First system message"),
                Message(role=Role.SYSTEM, content="Second system message"),  # Invalid!
                Message(role=Role.USER, content="User message"),
            ],
            variables=[],
        ),
    )

    try:
        result = await integration.convert(invalid_prompt, {})
        print("Unexpected: Should have raised an error")
    except IntegrationError as e:
        print(f"\nExpected error (multiple system messages):")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {e}")

    # Create prompt without system message (valid)
    valid_prompt = Prompt(
        id="no_system",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(role=Role.USER, content="Hello"),
                Message(role=Role.ASSISTANT, content="Hi there!"),
                Message(role=Role.USER, content="How are you?"),
            ],
            variables=[],
        ),
    )

    try:
        result = await integration.convert(valid_prompt, {})
        print(f"\nValid conversion (no system message):")
        print(f"  System: {result.get('system', 'None')}")
        print(f"  Messages: {len(result['messages'])}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def example_message_alternation_validation(
    manager: PromptManager,
    integration: AnthropicIntegration,
) -> None:
    """Example: Message alternation requirements."""
    print("\n" + "=" * 60)
    print("Example 5: Message Alternation Validation")
    print("=" * 60)

    from prompt_manager.exceptions import IntegrationError

    # Create prompt with invalid alternation (two user messages in a row)
    invalid_prompt = Prompt(
        id="invalid_alternation",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(role=Role.USER, content="First user message"),
                Message(role=Role.USER, content="Second user message"),  # Invalid!
            ],
            variables=[],
        ),
    )

    try:
        result = await integration.convert(invalid_prompt, {})
        print("Unexpected: Should have raised an error")
    except IntegrationError as e:
        print(f"\nExpected error (messages don't alternate):")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {e}")

    # Valid alternation
    valid_prompt = Prompt(
        id="valid_alternation",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(role=Role.USER, content="User message 1"),
                Message(role=Role.ASSISTANT, content="Assistant response 1"),
                Message(role=Role.USER, content="User message 2"),
            ],
            variables=[],
        ),
    )

    try:
        result = await integration.convert(valid_prompt, {})
        print(f"\nValid conversion (proper alternation):")
        for i, msg in enumerate(result["messages"]):
            print(f"  {i + 1}. {msg['role']}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def main():
    """Run all examples."""
    print("Anthropic SDK (Claude) Integration Example")
    print("=" * 60)

    # Setup
    storage = InMemoryStorage()
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Create template engine for integration
    from prompt_manager.core.template import TemplateEngine
    template_engine = TemplateEngine()
    integration = AnthropicIntegration(template_engine)

    # Create sample prompts
    await create_sample_prompts(manager)

    # Run examples
    await example_basic_conversion(manager, integration)
    await example_multi_turn_conversation(manager, integration)

    # Check if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    use_real_api = api_key is not None and api_key.startswith("sk-ant-")

    if not use_real_api:
        print("\nNote: ANTHROPIC_API_KEY not set. Running in demo mode.")
        print("Set ANTHROPIC_API_KEY environment variable to make real API calls.")

    await example_with_anthropic_sdk(manager, integration, use_real_api=use_real_api)
    await example_system_message_handling(manager, integration)
    await example_message_alternation_validation(manager, integration)

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
