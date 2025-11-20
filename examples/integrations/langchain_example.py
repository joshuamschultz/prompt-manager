"""
LangChain Integration Example

This example demonstrates how to use Prompt Manager with LangChain to:
1. Convert prompts to LangChain PromptTemplate and ChatPromptTemplate
2. Use in LCEL (LangChain Expression Language) chains
3. Handle template syntax conversion (Handlebars to f-string)
4. Work with partial variables and chain composition

Requirements:
    pip install agentic-prompt-manager[langchain]
    pip install langchain-openai  # For LLM examples

Environment:
    OPENAI_API_KEY=sk-...  # Optional, for LLM examples

Usage:
    python langchain_example.py
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
    PromptTemplate as PMPromptTemplate,
    PromptStatus,
    PromptMetadata,
    ChatPromptTemplate as PMChatPromptTemplate,
    Message,
    Role,
)
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage import InMemoryStorage
from prompt_manager.integrations import LangChainIntegration


async def create_sample_prompts(manager: PromptManager) -> None:
    """Create sample prompts for demonstration."""

    # TEXT format prompt
    text_prompt = Prompt(
        id="summarizer",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PMPromptTemplate(
            content="Summarize the following {{content_type}} in {{max_words}} words or less:\n\n{{content}}",
            variables=["content_type", "max_words", "content"],
        ),
        metadata=PromptMetadata(
            author="Example",
            description="Text summarization prompt",
            tags=["summarization", "text"],
        ),
    )

    # CHAT format prompt
    chat_prompt = Prompt(
        id="code_reviewer",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=PMChatPromptTemplate(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="You are an expert code reviewer specializing in {{language}}. "
                    "Provide constructive feedback on code quality, best practices, and potential issues.",
                ),
                Message(
                    role=Role.USER,
                    content="Please review this {{language}} code:\n\n```{{language}}\n{{code}}\n```",
                ),
            ],
            variables=["language", "code"],
        ),
        metadata=PromptMetadata(
            author="Example",
            description="Code review prompt",
            tags=["code-review", "chat"],
        ),
    )

    await manager.create_prompt(text_prompt)
    await manager.create_prompt(chat_prompt)
    print("Created sample prompts: summarizer, code_reviewer")


async def example_text_to_prompt_template(
    manager: PromptManager,
    integration: LangChainIntegration,
) -> None:
    """Example: Convert TEXT prompt to LangChain PromptTemplate."""
    print("\n" + "=" * 60)
    print("Example 1: TEXT → LangChain PromptTemplate")
    print("=" * 60)

    # Get prompt
    prompt = await manager.get_prompt("summarizer")
    print(f"\nOriginal Prompt:")
    print(f"  ID: {prompt.id}")
    print(f"  Format: {prompt.format.value}")
    print(f"  Template: {prompt.template.content[:80]}...")

    # Convert to LangChain PromptTemplate
    lc_template = await integration.convert(prompt, {})

    print(f"\nLangChain PromptTemplate:")
    print(f"  Type: {type(lc_template).__name__}")
    print(f"  Input variables: {lc_template.input_variables}")

    # Use the template
    result = lc_template.format(
        content_type="article",
        max_words="50",
        content="Long article text here...",
    )
    print(f"\nFormatted result:")
    print(f"  {result[:100]}...")


async def example_chat_to_chat_prompt_template(
    manager: PromptManager,
    integration: LangChainIntegration,
) -> None:
    """Example: Convert CHAT prompt to LangChain ChatPromptTemplate."""
    print("\n" + "=" * 60)
    print("Example 2: CHAT → LangChain ChatPromptTemplate")
    print("=" * 60)

    # Get prompt
    prompt = await manager.get_prompt("code_reviewer")
    print(f"\nOriginal Prompt:")
    print(f"  ID: {prompt.id}")
    print(f"  Format: {prompt.format.value}")
    print(f"  Messages: {len(prompt.chat_template.messages)}")

    # Convert to LangChain ChatPromptTemplate
    lc_template = await integration.convert(prompt, {})

    print(f"\nLangChain ChatPromptTemplate:")
    print(f"  Type: {type(lc_template).__name__}")
    print(f"  Input variables: {lc_template.input_variables}")
    print(f"  Messages: {len(lc_template.messages)}")

    # Format the template
    messages = lc_template.format_messages(
        language="Python",
        code="def hello(): print('world')",
    )
    print(f"\nFormatted messages:")
    for i, msg in enumerate(messages):
        print(f"  {i + 1}. {msg.__class__.__name__}: {str(msg.content)[:60]}...")


async def example_lcel_chain_composition(
    manager: PromptManager,
    integration: LangChainIntegration,
    use_real_llm: bool = False,
) -> None:
    """Example: Use in LCEL (LangChain Expression Language) chain."""
    print("\n" + "=" * 60)
    print("Example 3: LCEL Chain Composition")
    print("=" * 60)

    # Get prompt and convert
    prompt = await manager.get_prompt("summarizer")
    lc_template = await integration.convert(prompt, {})

    print(f"\nCreating LCEL chain with PromptTemplate")

    if use_real_llm:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.output_parsers import StrOutputParser

            # Create chain: prompt | llm | parser
            llm = ChatOpenAI(model="gpt-4", temperature=0.7)
            parser = StrOutputParser()
            chain = lc_template | llm | parser

            print(f"Chain: PromptTemplate | ChatOpenAI | StrOutputParser")
            print("\nInvoking chain...")

            # Invoke chain
            result = await chain.ainvoke({
                "content_type": "article",
                "max_words": "30",
                "content": "Artificial intelligence is rapidly transforming many industries. "
                "From healthcare to finance, AI systems are becoming more sophisticated and widely deployed.",
            })

            print(f"\nResult:")
            print(f"  {result}")

        except Exception as e:
            print(f"\nError: {e}")
            print("Make sure langchain-openai is installed and OPENAI_API_KEY is set")
    else:
        # Demo mode
        print(f"Demo Mode: Chain would be:")
        print(f"  PromptTemplate | ChatOpenAI | StrOutputParser")
        print(f"\nInput variables: {lc_template.input_variables}")
        print(f"\n(Set use_real_llm=True and install langchain-openai to run with real LLM)")


async def example_template_syntax_conversion(
    manager: PromptManager,
    integration: LangChainIntegration,
) -> None:
    """Example: Handlebars to f-string conversion."""
    print("\n" + "=" * 60)
    print("Example 4: Template Syntax Conversion")
    print("=" * 60)

    # Show original Handlebars syntax
    prompt = await manager.get_prompt("summarizer")
    print(f"\nOriginal (Handlebars syntax):")
    print(f"  {prompt.template.content}")

    # Convert to LangChain (uses f-string syntax)
    lc_template = await integration.convert(prompt, {})

    print(f"\nConverted (f-string syntax):")
    print(f"  {lc_template.template}")

    print(f"\nNote: {{{{variable}}}} (Handlebars) → {{variable}} (f-string)")


async def example_partial_variables(
    manager: PromptManager,
    integration: LangChainIntegration,
) -> None:
    """Example: Using partial variables."""
    print("\n" + "=" * 60)
    print("Example 5: Partial Variables")
    print("=" * 60)

    # Create prompt with partials
    prompt_with_partials = Prompt(
        id="templated_email",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PMPromptTemplate(
            content="Dear {{recipient_name}},\n\n{{email_body}}\n\n{{signature}}",
            variables=["recipient_name", "email_body"],
            partials={"signature": "Best regards,\nThe Team"},
        ),
    )

    # Convert to LangChain
    lc_template = await integration.convert(prompt_with_partials, {})

    print(f"\nPrompt with partials:")
    print(f"  Input variables: {lc_template.input_variables}")
    print(f"  Partial variables: {lc_template.partial_variables}")

    # Format with partial already filled
    result = lc_template.format(
        recipient_name="Alice",
        email_body="Thank you for your inquiry.",
    )

    print(f"\nFormatted result:")
    print(result)


async def example_error_handling(
    integration: LangChainIntegration,
) -> None:
    """Example: Error handling and validation."""
    print("\n" + "=" * 60)
    print("Example 6: Error Handling")
    print("=" * 60)

    from prompt_manager.exceptions import IntegrationError

    # Try with TEXT format (supported)
    text_prompt = Prompt(
        id="test_text",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PMPromptTemplate(content="Test {{var}}"),
    )

    try:
        result = await integration.convert(text_prompt, {})
        print(f"\nTEXT format: ✓ Supported")
        print(f"  Result type: {type(result).__name__}")
    except IntegrationError as e:
        print(f"Unexpected error: {e}")

    # Try with CHAT format (supported)
    chat_prompt = Prompt(
        id="test_chat",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=PMChatPromptTemplate(
            messages=[Message(role=Role.USER, content="Test")],
        ),
    )

    try:
        result = await integration.convert(chat_prompt, {})
        print(f"CHAT format: ✓ Supported")
        print(f"  Result type: {type(result).__name__}")
    except IntegrationError as e:
        print(f"Unexpected error: {e}")


async def main():
    """Run all examples."""
    print("LangChain Integration Example")
    print("=" * 60)

    # Setup
    storage = InMemoryStorage()
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)
    integration = LangChainIntegration(manager.template_engine)

    # Create sample prompts
    await create_sample_prompts(manager)

    # Run examples
    await example_text_to_prompt_template(manager, integration)
    await example_chat_to_chat_prompt_template(manager, integration)

    # Check if API key and langchain-openai available
    api_key = os.getenv("OPENAI_API_KEY")
    use_real_llm = api_key is not None and api_key.startswith("sk-")

    try:
        import langchain_openai
        if not use_real_llm:
            print("\nNote: OPENAI_API_KEY not set. Running LCEL example in demo mode.")
    except ImportError:
        print("\nNote: langchain-openai not installed. Skipping LLM example.")
        use_real_llm = False

    await example_lcel_chain_composition(manager, integration, use_real_llm=use_real_llm)
    await example_template_syntax_conversion(manager, integration)
    await example_partial_variables(manager, integration)
    await example_error_handling(integration)

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
