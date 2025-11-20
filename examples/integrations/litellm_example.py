"""
LiteLLM Integration Example

This example demonstrates how to use Prompt Manager with LiteLLM to:
1. Convert prompts to LiteLLM format (OpenAI-compatible)
2. Use with multiple LLM providers (OpenAI, Anthropic, Google, etc.)
3. Handle provider routing and fallbacks
4. Work with unified interface across 100+ LLM providers

Requirements:
    pip install prompt-manager[litellm]

Environment:
    OPENAI_API_KEY=sk-...        # For OpenAI models
    ANTHROPIC_API_KEY=sk-ant-... # For Claude models
    # etc. for other providers

Usage:
    python litellm_example.py
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
    PromptTemplate,
    PromptStatus,
    PromptMetadata,
    ChatPromptTemplate,
    Message,
    Role,
)
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import InMemoryStorage
from prompt_manager.integrations import LiteLLMIntegration


async def create_sample_prompts(manager: PromptManager) -> None:
    """Create sample prompts for demonstration."""

    # Multi-provider compatible chat prompt
    chat_prompt = Prompt(
        id="universal_assistant",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="You are a helpful AI assistant. Answer questions clearly and concisely.",
                ),
                Message(
                    role=Role.USER,
                    content="{{user_question}}",
                ),
            ],
            variables=["user_question"],
        ),
        metadata=PromptMetadata(
            author="Example",
            description="Universal assistant prompt (works with all providers)",
            tags=["assistant", "multi-provider"],
        ),
    )

    await manager.create_prompt(chat_prompt)
    print("Created sample prompt: universal_assistant")


async def example_basic_conversion(
    manager: PromptManager,
    integration: LiteLLMIntegration,
) -> None:
    """Example: Convert prompt to LiteLLM format."""
    print("\n" + "=" * 60)
    print("Example 1: LiteLLM Format Conversion")
    print("=" * 60)

    # Get prompt
    prompt = await manager.get_prompt("universal_assistant")
    print(f"\nPrompt ID: {prompt.id}")
    print(f"Format: {prompt.format.value}")

    # Convert to LiteLLM format (OpenAI-compatible)
    messages = await integration.convert(prompt, {
        "user_question": "What is the capital of France?"
    })

    print(f"\nLiteLLM Format (OpenAI-compatible):")
    print(f"Type: {type(messages)}")
    print(f"Messages:")
    for i, msg in enumerate(messages):
        print(f"  {i + 1}. {msg['role']:9} - {msg['content'][:60]}...")


async def example_multi_provider_usage(
    manager: PromptManager,
    integration: LiteLLMIntegration,
    use_real_api: bool = False,
) -> None:
    """Example: Use same prompt with multiple providers."""
    print("\n" + "=" * 60)
    print("Example 2: Multi-Provider Usage")
    print("=" * 60)

    # Get prompt and convert
    prompt = await manager.get_prompt("universal_assistant")
    messages = await integration.convert(prompt, {
        "user_question": "Explain quantum computing in one sentence"
    })

    print(f"\nConverted prompt can be used with any LiteLLM-supported provider:")

    if use_real_api:
        try:
            import litellm

            # Try multiple providers
            providers = [
                ("gpt-4", "OpenAI"),
                ("claude-3-5-sonnet-20241022", "Anthropic"),
                ("gemini-pro", "Google"),
            ]

            for model, provider_name in providers:
                try:
                    print(f"\n{provider_name} ({model}):")
                    response = await litellm.acompletion(
                        model=model,
                        messages=messages,
                        max_tokens=50,
                    )
                    print(f"  Response: {response.choices[0].message.content[:80]}...")
                except Exception as e:
                    print(f"  Error: {e}")
                    print(f"  (May need API key for {provider_name})")

        except Exception as e:
            print(f"\nError: {e}")
    else:
        # Demo mode
        print("\nDemo Mode: Would call LiteLLM with:")
        print(f"  Messages: {messages}")
        print(f"\nSupported providers (examples):")
        print(f"  - OpenAI: gpt-4, gpt-3.5-turbo")
        print(f"  - Anthropic: claude-3-5-sonnet, claude-3-opus")
        print(f"  - Google: gemini-pro, gemini-1.5-pro")
        print(f"  - Azure: azure/gpt-4")
        print(f"  - Cohere: command-r-plus")
        print(f"  - And 100+ more providers...")
        print(f"\n(Set use_real_api=True to make actual API calls)")


async def example_provider_fallback(
    manager: PromptManager,
    integration: LiteLLMIntegration,
    use_real_api: bool = False,
) -> None:
    """Example: Provider fallback strategy."""
    print("\n" + "=" * 60)
    print("Example 3: Provider Fallback Strategy")
    print("=" * 60)

    # Get prompt and convert
    prompt = await manager.get_prompt("universal_assistant")
    messages = await integration.convert(prompt, {
        "user_question": "What is machine learning?"
    })

    if use_real_api:
        try:
            import litellm

            # Define fallback chain
            providers = ["gpt-4", "claude-3-5-sonnet-20241022", "gpt-3.5-turbo"]

            print(f"\nTrying providers in order: {providers}")

            for model in providers:
                try:
                    print(f"\nAttempting: {model}")
                    response = await litellm.acompletion(
                        model=model,
                        messages=messages,
                        max_tokens=100,
                    )
                    print(f"Success! Response:")
                    print(f"  {response.choices[0].message.content[:100]}...")
                    break
                except Exception as e:
                    print(f"  Failed: {e}")
                    continue
            else:
                print("\nAll providers failed")

        except Exception as e:
            print(f"\nError: {e}")
    else:
        # Demo mode
        print("\nDemo Mode: Fallback strategy would:")
        print(f"  1. Try primary provider (gpt-4)")
        print(f"  2. If fails, try secondary (claude-3-5-sonnet)")
        print(f"  3. If fails, try tertiary (gpt-3.5-turbo)")
        print(f"\nThis ensures high availability across providers")


async def example_provider_routing(
    manager: PromptManager,
    integration: LiteLLMIntegration,
) -> None:
    """Example: Route to specific providers based on requirements."""
    print("\n" + "=" * 60)
    print("Example 4: Provider Routing")
    print("=" * 60)

    # Get prompt
    prompt = await manager.get_prompt("universal_assistant")

    # Define routing logic
    routing_rules = {
        "cost_sensitive": "gpt-3.5-turbo",       # Cheapest
        "quality_focused": "gpt-4",              # Best quality
        "long_context": "claude-3-5-sonnet-20241022",  # 200k context
        "speed_critical": "gpt-3.5-turbo",       # Fastest
    }

    print(f"\nRouting rules:")
    for use_case, model in routing_rules.items():
        print(f"  {use_case:20} → {model}")

    # Example routing
    use_case = "quality_focused"
    selected_model = routing_rules[use_case]

    messages = await integration.convert(prompt, {
        "user_question": "Complex question requiring detailed analysis"
    })

    print(f"\nFor use case '{use_case}', routing to: {selected_model}")
    print(f"Messages ready: {len(messages)} message(s)")


async def example_text_completion_mode(
    manager: PromptManager,
    integration: LiteLLMIntegration,
) -> None:
    """Example: TEXT format for completion mode."""
    print("\n" + "=" * 60)
    print("Example 5: Text Completion Mode")
    print("=" * 60)

    # Create TEXT format prompt
    text_prompt = Prompt(
        id="completion_prompt",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(
            content="Complete the following sentence: {{sentence_start}}",
            variables=["sentence_start"],
        ),
    )

    # Convert to LiteLLM format
    result = await integration.convert(text_prompt, {
        "sentence_start": "The future of artificial intelligence is"
    })

    print(f"\nTEXT format conversion:")
    print(f"Type: {type(result)}")
    print(f"Result: {result}")
    print(f"\nNote: For completion mode, some providers use this as user message")


async def main():
    """Run all examples."""
    print("LiteLLM Integration Example")
    print("=" * 60)

    # Setup
    storage = InMemoryStorage()
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)
    integration = LiteLLMIntegration(manager.template_engine)

    # Create sample prompts
    await create_sample_prompts(manager)

    # Run examples
    await example_basic_conversion(manager, integration)

    # Check if any API key is available
    has_api_key = any([
        os.getenv("OPENAI_API_KEY"),
        os.getenv("ANTHROPIC_API_KEY"),
        os.getenv("GOOGLE_API_KEY"),
    ])

    if not has_api_key:
        print("\nNote: No LLM API keys detected. Running in demo mode.")
        print("Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or other provider keys to make real API calls.")

    await example_multi_provider_usage(manager, integration, use_real_api=has_api_key)
    await example_provider_fallback(manager, integration, use_real_api=has_api_key)
    await example_provider_routing(manager, integration)
    await example_text_completion_mode(manager, integration)

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print("\nLiteLLM supports 100+ providers including:")
    print("  - OpenAI, Anthropic, Google, Cohere, Azure")
    print("  - AWS Bedrock, Vertex AI, Hugging Face")
    print("  - Replicate, Together AI, Perplexity, and more")
    print("\nSee https://docs.litellm.ai/docs/providers for full list")


if __name__ == "__main__":
    asyncio.run(main())
