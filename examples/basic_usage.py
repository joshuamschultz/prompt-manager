"""
Basic usage examples for the Prompt Manager.

This file demonstrates common use cases and patterns.
"""

import asyncio
from pathlib import Path

from prompt_manager import PromptManager, Prompt, PromptMetadata
from prompt_manager.core.models import (
    ChatPromptTemplate,
    Message,
    PromptFormat,
    PromptStatus,
    PromptTemplate,
    Role,
)
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.observability import LoggingObserver, MetricsCollector
from prompt_manager.storage import FileSystemStorage, YAMLLoader
from prompt_manager.versioning import VersionStore


async def example_1_simple_text_prompt() -> None:
    """Example 1: Create and render a simple text prompt."""
    print("\n=== Example 1: Simple Text Prompt ===\n")

    # Setup
    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Create prompt
    prompt = Prompt(
        id="greeting",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(
            content="Hello {{name}}! Welcome to {{service}}.",
            variables=["name", "service"],
        ),
        metadata=PromptMetadata(
            author="System",
            description="Simple greeting prompt",
            tags=["greeting", "welcome"],
        ),
    )

    # Register and render
    await manager.create_prompt(prompt)

    result = await manager.render(
        "greeting",
        {"name": "Alice", "service": "Prompt Manager"},
    )

    print(f"Rendered: {result}")


async def example_2_chat_prompt() -> None:
    """Example 2: Create and render a chat-based prompt."""
    print("\n=== Example 2: Chat Prompt ===\n")

    # Setup
    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Create chat prompt
    prompt = Prompt(
        id="customer_support",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="You are a helpful customer support agent for {{company}}. "
                    "Be professional and empathetic.",
                ),
                Message(
                    role=Role.USER,
                    content="{{customer_query}}",
                ),
            ],
            variables=["company", "customer_query"],
        ),
        metadata=PromptMetadata(
            author="Support Team",
            description="Customer support chat template",
            tags=["support", "chat"],
            category="customer-service",
            model_recommendations=["gpt-4", "claude-3-opus"],
            temperature=0.7,
        ),
    )

    await manager.create_prompt(prompt)

    result = await manager.render(
        "customer_support",
        {
            "company": "Acme Corp",
            "customer_query": "I need help with my recent order.",
        },
    )

    print(f"Rendered:\n{result}")


async def example_3_versioning() -> None:
    """Example 3: Version management and history."""
    print("\n=== Example 3: Versioning ===\n")

    # Setup with version store
    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    version_store = VersionStore(Path("./data/versions"))
    manager = PromptManager(registry=registry, version_store=version_store)

    # Create initial version
    prompt = Prompt(
        id="marketing_email",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(
            content="Hi {{name}}, check out our new product!",
            variables=["name"],
        ),
    )

    await manager.create_prompt(
        prompt,
        changelog="Initial version",
        created_by="marketing_team",
    )
    print("Created v1.0.0")

    # Update prompt
    prompt.template = PromptTemplate(
        content="Hi {{name}}, discover our amazing new {{product}}! "
        "Use code {{discount_code}} for {{discount}}% off.",
        variables=["name", "product", "discount_code", "discount"],
    )

    await manager.update_prompt(
        prompt,
        bump_version=True,
        changelog="Added product details and discount",
        created_by="marketing_team",
    )
    print("Created v1.0.1")

    # Get history
    history = await manager.get_history("marketing_email")
    print("\nVersion History:")
    for version in history:
        print(f"  {version.version}: {version.changelog} (by {version.created_by})")


async def example_4_observability() -> None:
    """Example 4: Observability with logging and metrics."""
    print("\n=== Example 4: Observability ===\n")

    # Setup with observers
    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    metrics = MetricsCollector()
    logging_obs = LoggingObserver()

    manager = PromptManager(
        registry=registry,
        metrics=metrics,
        observers=[logging_obs],
    )

    # Create and render prompts
    prompt = Prompt(
        id="test_metrics",
        version="1.0.0",
        format=PromptFormat.TEXT,
        template=PromptTemplate(content="Test {{var}}", variables=["var"]),
    )

    await manager.create_prompt(prompt)

    # Render multiple times
    for i in range(10):
        await manager.render("test_metrics", {"var": f"value_{i}"})

    # Get metrics
    metrics_data = await manager.get_metrics()
    print("\nMetrics:")
    print(f"  Total renders: {metrics_data['operations']['summary']['total_renders']}")
    print(
        f"  Avg duration: "
        f"{metrics_data['operations']['performance']['avg_duration_ms']:.2f}ms"
    )


async def example_5_yaml_import() -> None:
    """Example 5: Load prompts from YAML."""
    print("\n=== Example 5: YAML Import ===\n")

    # Create example YAML file
    yaml_path = Path("./data/prompts.yaml")
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    if not yaml_path.exists():
        YAMLLoader.create_example_yaml(yaml_path)
        print(f"Created example YAML at {yaml_path}")

    # Load from YAML
    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    loader = YAMLLoader(registry)

    count = await loader.import_to_registry(yaml_path)
    print(f"Imported {count} prompts from YAML")

    # List imported prompts
    manager = PromptManager(registry=registry)
    prompts = await manager.list_prompts()

    print("\nImported prompts:")
    for prompt in prompts:
        print(f"  - {prompt.id} v{prompt.version}: {prompt.metadata.description}")


async def example_6_filtering() -> None:
    """Example 6: Filter and search prompts."""
    print("\n=== Example 6: Filtering ===\n")

    # Setup
    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Create multiple prompts with different tags
    prompts_data = [
        ("sales_email", ["sales", "email"], "marketing"),
        ("support_chat", ["support", "chat"], "customer-service"),
        ("onboarding", ["onboarding", "email"], "product"),
    ]

    for prompt_id, tags, category in prompts_data:
        prompt = Prompt(
            id=prompt_id,
            version="1.0.0",
            format=PromptFormat.TEXT,
            template=PromptTemplate(content="Test", variables=[]),
            metadata=PromptMetadata(tags=tags, category=category),
        )
        await manager.create_prompt(prompt)

    # Filter by tags
    email_prompts = await manager.list_prompts(tags=["email"])
    print(f"\nEmail prompts: {[p.id for p in email_prompts]}")

    # Filter by category
    marketing_prompts = await manager.list_prompts(category="marketing")
    print(f"Marketing prompts: {[p.id for p in marketing_prompts]}")

    # Filter by status
    active_prompts = await manager.list_prompts(status="active")
    print(f"Active prompts: {len(active_prompts)}")


async def example_7_error_handling() -> None:
    """Example 7: Error handling patterns."""
    print("\n=== Example 7: Error Handling ===\n")

    from prompt_manager.exceptions import (
        PromptNotFoundError,
        TemplateRenderError,
        PromptValidationError,
    )

    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Handle missing prompt
    try:
        await manager.render("nonexistent", {})
    except PromptNotFoundError as e:
        print(f"Caught expected error: {e}")

    # Handle validation error
    try:
        invalid_prompt = Prompt(
            id="invalid",
            version="not-semver",  # Invalid version
            format=PromptFormat.TEXT,
            template=PromptTemplate(content="Test", variables=[]),
        )
    except PromptValidationError as e:
        print(f"Caught validation error: {e}")


async def example_8_schema_validation() -> None:
    """Example 8: Schema validation with auto-injection."""
    print("\n=== Example 8: Schema Validation ===\n")

    # Setup
    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Load schemas from individual files
    schema_count = await manager.load_schemas(Path("./schemas-individual"))
    print(f"Loaded {schema_count} validation schemas")

    # Create a prompt with schema validation
    from prompt_manager.core.models import (
        ChatPromptTemplate,
        Message,
        Role,
    )

    prompt = Prompt(
        id="code_review_assistant",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="You are an expert code reviewer. Analyze the provided {{language}} code.",
                ),
                Message(
                    role=Role.USER,
                    content="Review this code:\n\n{{code}}",
                ),
            ],
            variables=["language", "code"],
        ),
        metadata=PromptMetadata(
            author="Engineering Team",
            description="Code review with schema validation",
            tags=["code-review", "validation"],
        ),
        input_schema="code_review_input",  # Schema will be auto-injected
    )

    await manager.create_prompt(prompt)

    # Render with variables - schema description will be auto-injected
    result = await manager.render(
        "code_review_assistant",
        {
            "language": "python",
            "code": "def add(a, b):\n    return a + b",
        },
    )

    print("\nRendered prompt with auto-injected schema description:")
    print("-" * 60)
    print(result)
    print("-" * 60)


async def example_9_output_validation() -> None:
    """Example 9: Validate LLM output against schema."""
    print("\n=== Example 9: Output Validation ===\n")

    # Setup
    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Load schemas
    await manager.load_schemas(Path("./schemas-individual"))

    # Create prompt with output schema
    prompt = Prompt(
        id="summarizer",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(
            content="Summarize: {{text}}",
            variables=["text"],
        ),
        output_schema="text_summarization_output",  # Defines expected output
    )

    await manager.create_prompt(prompt)

    # Simulate LLM response
    llm_response = {
        "summary": "This is a brief summary of the text.",
        "key_points": ["Point 1", "Point 2", "Point 3"],
        "word_count": 8,
    }

    print("Validating LLM response against output schema...")

    try:
        # Validate the LLM output
        validated = await manager.validate_output(
            "text_summarization_output",
            llm_response
        )
        print("✅ Validation passed!")
        print(f"Validated data: {validated}")

    except Exception as e:
        print(f"❌ Validation failed: {e}")

    # Example: Invalid output
    print("\n--- Testing invalid output ---")
    invalid_response = {
        "summary": "Too short",  # Less than 10 chars (min_length validator)
        "word_count": "invalid",  # Should be integer
    }

    try:
        await manager.validate_output(
            "text_summarization_output",
            invalid_response
        )
    except Exception as e:
        print(f"✅ Correctly caught validation error: {type(e).__name__}")


async def example_10_automatic_validation() -> None:
    """Example 10: Complete automatic validation flow."""
    print("\n=== Example 10: Automatic Validation (Full Flow) ===\n")

    # Setup
    storage = FileSystemStorage(Path("./data/prompts"))
    registry = PromptRegistry(storage=storage)
    manager = PromptManager(registry=registry)

    # Load schemas
    await manager.load_schemas(Path("./schemas-individual"))

    # Create prompt with BOTH input and output schemas
    prompt = Prompt(
        id="auto_summarizer",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(
            content="Please summarize the following {{content_type}}:\n\n{{text}}",
            variables=["content_type", "text"],
        ),
        metadata=PromptMetadata(
            description="Automatic validation example",
        ),
        input_schema="text_summarization_input",   # Auto-validates input
        output_schema="text_summarization_output", # Auto-validates output
    )

    await manager.create_prompt(prompt)

    # ═══════════════════════════════════════════════════════════
    # COMPLETE AUTOMATIC FLOW
    # ═══════════════════════════════════════════════════════════

    print("Step 1: Preparing input (will be auto-validated)...")
    input_vars = {
        "content_type": "article",
        "length": "brief",
        "text": "This is a long article about Python programming. " * 10,
    }

    print("Step 2: Rendering prompt (auto-validates input + injects schemas)...")
    try:
        # Input validation happens automatically during render!
        prompt_text = await manager.render("auto_summarizer", input_vars)
        print("✅ Input validated and prompt rendered!")
        print(f"\nPrompt includes structured output instructions:")
        print("-" * 60)
        print(prompt_text[-500:] if len(prompt_text) > 500 else prompt_text)
        print("-" * 60)
    except Exception as e:
        print(f"❌ Input validation failed: {e}")
        return

    print("\nStep 3: Simulating LLM response...")
    llm_response = {
        "summary": "A comprehensive article exploring Python programming concepts.",
        "key_points": [
            "Python is versatile",
            "Easy to learn",
            "Large ecosystem"
        ],
        "word_count": 42
    }

    print("Step 4: Auto-validating LLM output with render_and_parse()...")
    try:
        # This automatically validates output!
        validated = await manager.render_and_parse(
            "auto_summarizer",
            input_vars,
            llm_response
        )
        print("✅ Output validated successfully!")
        print(f"Validated data: {validated}")

    except Exception as e:
        print(f"❌ Output validation failed: {e}")

    print("\n" + "=" * 60)
    print("COMPLETE AUTOMATIC WORKFLOW:")
    print("1. ✅ Input validated automatically (render)")
    print("2. ✅ Schemas injected into prompt")
    print("3. ✅ Output validated automatically (render_and_parse)")
    print("=" * 60)


async def main() -> None:
    """Run all examples."""
    examples = [
        ("Simple Text Prompt", example_1_simple_text_prompt),
        ("Chat Prompt", example_2_chat_prompt),
        ("Versioning", example_3_versioning),
        ("Observability", example_4_observability),
        ("YAML Import", example_5_yaml_import),
        ("Filtering", example_6_filtering),
        ("Error Handling", example_7_error_handling),
        ("Schema Validation", example_8_schema_validation),
        ("Output Validation", example_9_output_validation),
        ("Automatic Validation", example_10_automatic_validation),
    ]

    print("=" * 60)
    print("Prompt Manager - Usage Examples")
    print("=" * 60)

    for name, example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
