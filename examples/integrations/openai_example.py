"""
OpenAI SDK Integration Example

This example demonstrates how to use Prompt Manager with the OpenAI SDK to:
1. Convert TEXT and CHAT prompts to OpenAI message format
2. Use prompts with OpenAI's API (GPT-4, GPT-3.5, etc.)
3. Handle variables and template rendering
4. Work with function calling and tool use

Requirements:
    pip install agentic-prompt-manager[openai]

Environment:
    OPENAI_API_KEY=sk-...  # Set this in .env file or environment

Usage:
    python openai_example.py
"""

import asyncio
import os
from pathlib import Path

# Optional: Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from prompt_manager import PromptManager, Prompt
from prompt_manager.core.models import (
    PromptFormat,
    PromptTemplate,
    PromptStatus,
    PromptMetadata,
    ChatPromptTemplate,
    Message,
    Role,
)
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import InMemoryStorage
from prompt_manager.integrations import OpenAIIntegration


async def create_sample_prompts(manager: PromptManager) -> None:
    """Create sample prompts for demonstration."""

    # TEXT format prompt
    text_prompt = Prompt(
        id="greeting",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(
            content="Hello {{name}}! Welcome to {{service}}. How can I help you today?",
            variables=["name", "service"],
        ),
        metadata=PromptMetadata(
            author="Example",
            description="Simple greeting prompt",
            tags=["greeting", "text"],
        ),
    )

    # CHAT format prompt
    chat_prompt = Prompt(
        id="customer_support",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="You are a helpful customer support assistant for {{company}}. "
                    "Be friendly, professional, and concise. Always prioritize customer satisfaction.",
                ),
                Message(
                    role=Role.USER,
                    content="{{user_query}}",
                ),
            ],
            variables=["company", "user_query"],
        ),
        metadata=PromptMetadata(
            author="Example",
            description="Customer support chat prompt",
            tags=["customer-support", "chat"],
        ),
    )

    # Register prompts
    await manager.create_prompt(text_prompt)
    await manager.create_prompt(chat_prompt)
    print("Created sample prompts: greeting, customer_support")


async def example_text_prompt_conversion(
    manager: PromptManager,
    integration: OpenAIIntegration,
) -> None:
    """Example: Convert TEXT prompt to OpenAI format."""
    print("\n" + "=" * 60)
    print("Example 1: TEXT Prompt Conversion")
    print("=" * 60)

    # Get prompt
    prompt = await manager.get_prompt("greeting")
    print(f"\nPrompt ID: {prompt.id}")
    print(f"Format: {prompt.format.value}")
    print(f"Template: {prompt.template.content}")

    # Convert to OpenAI format
    result = await integration.convert(prompt, {
        "name": "Alice",
        "service": "Prompt Manager",
    })

    print(f"\nOpenAI Format (TEXT → string):")
    print(f"Type: {type(result)}")
    print(f"Content: {result}")


async def example_chat_prompt_conversion(
    manager: PromptManager,
    integration: OpenAIIntegration,
) -> None:
    """Example: Convert CHAT prompt to OpenAI messages."""
    print("\n" + "=" * 60)
    print("Example 2: CHAT Prompt Conversion")
    print("=" * 60)

    # Get prompt
    prompt = await manager.get_prompt("customer_support")
    print(f"\nPrompt ID: {prompt.id}")
    print(f"Format: {prompt.format.value}")
    print(f"Messages: {len(prompt.chat_template.messages)}")

    # Convert to OpenAI format
    messages = await integration.convert(prompt, {
        "company": "Acme Corp",
        "user_query": "How do I reset my password?",
    })

    print(f"\nOpenAI Format (CHAT → list of message dicts):")
    print(f"Type: {type(messages)}")
    print(f"Number of messages: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"\nMessage {i + 1}:")
        print(f"  Role: {msg['role']}")
        print(f"  Content: {msg['content'][:100]}...")


async def example_with_openai_sdk(
    manager: PromptManager,
    integration: OpenAIIntegration,
    use_real_api: bool = False,
) -> None:
    """Example: Use converted prompt with OpenAI SDK."""
    print("\n" + "=" * 60)
    print("Example 3: Using with OpenAI SDK")
    print("=" * 60)

    # Get prompt and convert
    prompt = await manager.get_prompt("customer_support")
    messages = await integration.convert(prompt, {
        "company": "Acme Corp",
        "user_query": "What are your business hours?",
    })

    print(f"\nConverted {len(messages)} messages for OpenAI API")

    if use_real_api:
        # Real API call (requires OPENAI_API_KEY)
        try:
            import openai

            client = openai.AsyncOpenAI()
            print("\nCalling OpenAI API...")

            response = await client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=150,
            )

            print(f"\nResponse:")
            print(response.choices[0].message.content)

        except Exception as e:
            print(f"\nError calling OpenAI API: {e}")
            print("Make sure OPENAI_API_KEY is set in your environment")
    else:
        # Mock/demo mode
        print("\nDemo Mode: Would call OpenAI API with:")
        print(f"  Model: gpt-4")
        print(f"  Messages: {messages}")
        print(f"\n(Set use_real_api=True to make actual API calls)")


async def example_error_handling(
    manager: PromptManager,
    integration: OpenAIIntegration,
) -> None:
    """Example: Error handling and validation."""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)

    from prompt_manager.exceptions import ConversionError

    # Try converting with missing variable
    prompt = await manager.get_prompt("customer_support")

    try:
        messages = await integration.convert(prompt, {
            "company": "Acme Corp",
            # Missing "user_query" variable
        })
    except Exception as e:
        print(f"\nExpected error (missing variable):")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {e}")

    # Successful conversion with all variables
    try:
        messages = await integration.convert(prompt, {
            "company": "Acme Corp",
            "user_query": "Test query",
        })
        print(f"\nSuccessful conversion:")
        print(f"  Created {len(messages)} messages")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def main():
    """Run all examples."""
    print("OpenAI SDK Integration Example")
    print("=" * 60)

    # Setup
    storage = InMemoryStorage()
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Create template engine for integration
    from prompt_manager.core.template import TemplateEngine
    template_engine = TemplateEngine()
    integration = OpenAIIntegration(template_engine)

    # Create sample prompts
    await create_sample_prompts(manager)

    # Run examples
    await example_text_prompt_conversion(manager, integration)
    await example_chat_prompt_conversion(manager, integration)

    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    use_real_api = api_key is not None and api_key.startswith("sk-")

    if not use_real_api:
        print("\nNote: OPENAI_API_KEY not set. Running in demo mode.")
        print("Set OPENAI_API_KEY environment variable to make real API calls.")

    await example_with_openai_sdk(manager, integration, use_real_api=use_real_api)
    await example_error_handling(manager, integration)

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
