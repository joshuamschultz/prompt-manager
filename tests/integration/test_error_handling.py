"""Error handling and edge case tests for dual sync/async interface.

This module tests comprehensive error handling across both sync and async execution
modes, ensuring consistent behavior and clear error messages.

Test Categories:
    - Task 12.1: Nested event loop detection
    - Task 12.2: Closed event loop handling
    - Task 12.3: Exception consistency across sync/async modes
    - Task 12.5: Storage error handling
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from prompt_manager import PromptManager
from prompt_manager.core.models import (
    Prompt,
    PromptFormat,
    PromptMetadata,
    PromptStatus,
    PromptTemplate,
)
from prompt_manager.exceptions import (
    PromptNotFoundError,
    SchemaParseError,
    SchemaValidationError,
    StorageReadError,
    StorageWriteError,
    TemplateError,
    TemplateRenderError,
    TemplateSyntaxError,
    VersionError,
    VersionNotFoundError,
)


# ============================================================================
# Task 12.1: Nested Event Loop Detection Tests
# ============================================================================



def test_nested_event_loop_detection_in_async_context(file_manager: PromptManager):
    """Test that run_sync() raises clear error when called from async context."""
    # Inside async context, trying to use run_sync should raise
    with pytest.raises(RuntimeError, match="Cannot call synchronous method from async context"):
        from prompt_manager.utils.async_helpers import run_sync
        # Create a simple coroutine to test
        def simple_coro():
            return "test"
        run_sync(simple_coro())



def test_nested_loop_error_message_includes_example(file_manager: PromptManager):
    """Verify error message includes usage example."""
    with pytest.raises(RuntimeError) as exc_info:
        from prompt_manager.utils.async_helpers import run_sync
        def dummy():
            return []
        run_sync(dummy())

    error_message = str(exc_info.value)
    assert "You're already in an async function" in error_message
    assert "await" in error_message
    assert "Example:" in error_message



def test_nested_loop_detection_with_get_or_create_loop():
    """Test get_or_create_event_loop raises error in async context."""
    from prompt_manager.utils.async_helpers import get_or_create_event_loop

    with pytest.raises(RuntimeError, match="Cannot call synchronous method"):
        get_or_create_event_loop()


def simulated_fastapi_handler(manager: PromptManager) -> dict[str, Any]:
    """Simulate a FastAPI handler (async context)."""
    # Proper async usage
    prompts = manager.list_prompts()
    return {"count": len(prompts)}



def test_nested_loop_in_simulated_fastapi(file_manager: PromptManager):
    """Test correct async usage in simulated FastAPI handler."""
    # Create test prompts
    for i in range(3):
        prompt = Prompt(
            id=f"fastapi_test_{i}",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content=f"Test {i}", variables=[]),
            metadata=PromptMetadata(author="Test", description=f"Prompt {i}"),
        )
        file_manager.create_prompt(prompt)

    # Proper async usage should work fine
    result = simulated_fastapi_handler(file_manager)
    assert result["count"] == 3


def broken_fastapi_handler(manager: PromptManager) -> dict[str, Any]:
    """Simulate a broken FastAPI handler (attempts sync call in async context)."""
    # This is wrong and should raise
    from prompt_manager.utils.async_helpers import run_sync
    def list_coro():
        return manager.list_prompts()
    prompts = run_sync(list_coro())
    return {"count": len(prompts)}



def test_nested_loop_error_in_simulated_fastapi(file_manager: PromptManager):
    """Test that incorrect sync call in FastAPI handler raises error."""
    with pytest.raises(RuntimeError, match="Cannot call synchronous method"):
        broken_fastapi_handler(file_manager)



def test_is_async_context_detection():
    """Test is_async_context correctly detects async context."""
    from prompt_manager.utils.async_helpers import is_async_context

    # Inside async function, should be True
    assert is_async_context() is True

    # Nested async call should still be True
    def nested():
        return is_async_context()

    assert nested() is True


# ============================================================================
# Task 12.2: Closed Event Loop Handling Tests
# ============================================================================


def test_sync_call_after_loop_closed(file_manager: PromptManager):
    """Test sync call after loop.close() creates new loop successfully."""
    # Create and close a loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.close()

    # Sync call should create new loop and work fine
    prompt = Prompt(
        id="after_close",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Test", variables=[]),
        metadata=PromptMetadata(author="Test", description="Test"),
    )
    created = file_manager.create_prompt(prompt)
    assert created.id == "after_close"

    # Clean up
    file_manager._registry.delete("after_close")


def test_multiple_calls_after_loop_closed(file_manager: PromptManager):
    """Test multiple sync calls after loop closed work correctly."""
    # Create and close a loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.close()

    # Multiple sync calls should all work
    for i in range(5):
        prompt = Prompt(
            id=f"multi_after_close_{i}",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content=f"Test {i}", variables=[]),
            metadata=PromptMetadata(author="Test", description=f"Test {i}"),
        )
        created = file_manager.create_prompt(prompt)
        assert created.id == f"multi_after_close_{i}"

    # Verify all were created
    prompts = file_manager.list_prompts()
    created_ids = [p.id for p in prompts if p.id.startswith("multi_after_close_")]
    assert len(created_ids) == 5

    # Clean up
    for i in range(5):
        file_manager._registry.delete(f"multi_after_close_{i}")


def test_no_event_loop_leaks_after_closed_loop(file_manager: PromptManager):
    """Verify no event loop leaks after creating new loops."""
    # Create and close a loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.close()

    # Perform operations
    prompt = Prompt(
        id="leak_test",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Test", variables=[]),
        metadata=PromptMetadata(author="Test", description="Test"),
    )
    file_manager.create_prompt(prompt)

    # Check no running tasks (would indicate leak)
    current_loop = asyncio.get_event_loop()
    # Use all_tasks with current_loop for compatibility
    all_tasks = asyncio.all_tasks(current_loop)
    assert len(all_tasks) == 0, "Event loop has leaked tasks"

    # Clean up
    file_manager._registry.delete("leak_test")


def test_closed_loop_recovery_with_rendering(file_manager: PromptManager):
    """Test that rendering works after loop closed."""
    # Create prompt first
    prompt = Prompt(
        id="render_after_close",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Hello {{name}}", variables=["name"]),
        metadata=PromptMetadata(author="Test", description="Test"),
    )
    file_manager.create_prompt(prompt)

    # Close loop
    loop = asyncio.get_event_loop()
    loop.close()

    # Rendering should work with new loop
    result = file_manager.render("render_after_close", {"name": "World"})
    assert result == "Hello World"

    # Clean up
    file_manager._registry.delete("render_after_close")


# ============================================================================
# Task 12.3: Exception Consistency Tests
# ============================================================================


def test_prompt_not_found_error_consistency(file_manager: PromptManager):
    """Test PromptNotFoundError raised identically in sync and async modes."""
    # Sync mode
    with pytest.raises(PromptNotFoundError) as exc_info_sync:
        file_manager.get_prompt("nonexistent_prompt_id")

    sync_error = exc_info_sync.value
    sync_message = str(sync_error)

    # Async mode
    def async_get():
        return file_manager.get_prompt("nonexistent_prompt_id")

    with pytest.raises(PromptNotFoundError) as exc_info_async:
        asyncio.run(async_get())

    async_error = exc_info_async.value
    async_message = str(async_error)

    # Verify identical error messages
    assert sync_message == async_message
    assert "nonexistent_prompt_id" in sync_message
    assert "not found" in sync_message.lower()

    # Verify exception attributes preserved
    assert sync_error.context["prompt_id"] == "nonexistent_prompt_id"
    assert async_error.context["prompt_id"] == "nonexistent_prompt_id"


def test_template_render_error_consistency(file_manager: PromptManager):
    """Test TemplateRenderError raised identically in sync and async modes."""
    # Create prompt with template that will fail rendering
    prompt = Prompt(
        id="failing_template",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(
            content="Hello {{name}}, you have {{#if items}}{{items.length}}{{/if}} items",
            variables=["name", "items"],
        ),
        metadata=PromptMetadata(author="Test", description="Test"),
    )
    file_manager.create_prompt(prompt)

    # Sync mode - missing required variable
    with pytest.raises((TemplateError, TemplateRenderError)) as exc_info_sync:
        file_manager.render("failing_template", {})

    sync_message = str(exc_info_sync.value)

    # Async mode - missing required variable
    def async_render():
        return file_manager.render("failing_template", {})

    with pytest.raises((TemplateError, TemplateRenderError)) as exc_info_async:
        asyncio.run(async_render())

    async_message = str(exc_info_async.value)

    # Verify similar error messages (may differ slightly in details)
    assert type(exc_info_sync.value).__name__ == type(exc_info_async.value).__name__

    # Clean up
    file_manager._registry.delete("failing_template")


def test_template_syntax_error_consistency(file_manager: PromptManager):
    """Test TemplateSyntaxError raised identically in sync and async modes."""
    # Create prompt with invalid template syntax
    prompt = Prompt(
        id="syntax_error_template",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(
            content="Hello {{#if unclosed}",  # Unclosed block
            variables=[],
        ),
        metadata=PromptMetadata(author="Test", description="Test"),
    )

    # Both modes should fail during create_prompt (template validation)
    # Sync mode
    sync_exception_type = None
    try:
        file_manager.create_prompt(prompt)
    except Exception as e:
        sync_exception_type = type(e).__name__

    # Async mode
    def async_create():
        return file_manager.create_prompt(prompt)

    async_exception_type = None
    try:
        asyncio.run(async_create())
    except Exception as e:
        async_exception_type = type(e).__name__

    # Verify same exception type raised
    assert sync_exception_type == async_exception_type


def test_schema_validation_error_consistency(file_manager: PromptManager, integration_tmp_path: Path):
    """Test SchemaValidationError raised identically in sync and async modes."""
    # Create a schema file
    schema_file = integration_tmp_path / "test_schema.json"
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    }
    schema_file.write_text(json.dumps(schema))

    # Load schema
    schemas = file_manager.load_schemas(str(schema_file))
    schema_id = list(schemas.keys())[0]

    # Invalid data (missing required field)
    invalid_data = {"name": "Alice"}  # Missing 'age'

    # Sync mode
    with pytest.raises(SchemaValidationError) as exc_info_sync:
        file_manager.validate_output(invalid_data, schema_id)

    sync_message = str(exc_info_sync.value)

    # Async mode
    def async_validate():
        return file_manager.validate_output(invalid_data, schema_id)

    with pytest.raises(SchemaValidationError) as exc_info_async:
        asyncio.run(async_validate())

    async_message = str(exc_info_async.value)

    # Verify error messages mention the issue
    assert "age" in sync_message.lower() or "required" in sync_message.lower()
    assert "age" in async_message.lower() or "required" in async_message.lower()


def test_schema_parse_error_consistency(file_manager: PromptManager, integration_tmp_path: Path):
    """Test SchemaParseError raised identically in sync and async modes."""
    # Create invalid JSON schema file
    schema_file = integration_tmp_path / "invalid_schema.json"
    schema_file.write_text("{invalid json syntax")

    # Sync mode
    with pytest.raises((SchemaParseError, json.JSONDecodeError)) as exc_info_sync:
        file_manager.load_schemas(str(schema_file))

    sync_exception_type = type(exc_info_sync.value).__name__

    # Async mode
    def async_load():
        return file_manager.load_schemas(str(schema_file))

    with pytest.raises((SchemaParseError, json.JSONDecodeError)) as exc_info_async:
        asyncio.run(async_load())

    async_exception_type = type(exc_info_async.value).__name__

    # Verify same exception type
    assert sync_exception_type == async_exception_type


def test_version_not_found_error_consistency(file_manager: PromptManager):
    """Test VersionNotFoundError raised identically in sync and async modes."""
    # Create a prompt
    prompt = Prompt(
        id="version_test",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Test", variables=[]),
        metadata=PromptMetadata(author="Test", description="Test"),
    )
    file_manager.create_prompt(prompt)

    # Try to get non-existent version
    # Sync mode
    with pytest.raises((VersionNotFoundError, PromptNotFoundError)) as exc_info_sync:
        file_manager.get_prompt("version_test", version="99.99.99")

    sync_message = str(exc_info_sync.value)

    # Async mode
    def async_get():
        return file_manager.get_prompt("version_test", version="99.99.99")

    with pytest.raises((VersionNotFoundError, PromptNotFoundError)) as exc_info_async:
        asyncio.run(async_get())

    async_message = str(exc_info_async.value)

    # Verify error messages are similar
    assert "version_test" in sync_message
    assert "version_test" in async_message

    # Clean up
    file_manager._registry.delete("version_test")


def test_storage_error_exception_consistency(file_manager: PromptManager):
    """Test storage errors raised identically in sync and async modes."""
    # Test with nonexistent prompt ID (triggers storage read)
    # Sync mode
    with pytest.raises(PromptNotFoundError) as exc_info_sync:
        file_manager.get_prompt("nonexistent_storage_test")

    # Async mode
    def async_get():
        return file_manager.get_prompt("nonexistent_storage_test")

    with pytest.raises(PromptNotFoundError) as exc_info_async:
        asyncio.run(async_get())

    # Both should raise PromptNotFoundError (storage abstraction)
    assert type(exc_info_sync.value) == type(exc_info_async.value)


def test_exception_attributes_preserved(file_manager: PromptManager):
    """Test that exception attributes are preserved across both modes."""
    # Test with PromptNotFoundError which has custom attributes
    # Sync mode
    with pytest.raises(PromptNotFoundError) as exc_info_sync:
        file_manager.get_prompt("test_attrs", version="1.2.3")

    sync_error = exc_info_sync.value
    assert sync_error.context["prompt_id"] == "test_attrs"
    assert sync_error.context["version"] == "1.2.3"

    # Async mode
    def async_get():
        return file_manager.get_prompt("test_attrs", version="1.2.3")

    with pytest.raises(PromptNotFoundError) as exc_info_async:
        asyncio.run(async_get())

    async_error = exc_info_async.value
    assert async_error.context["prompt_id"] == "test_attrs"
    assert async_error.context["version"] == "1.2.3"

    # Verify attributes match
    assert sync_error.context == async_error.context


# ============================================================================
# Task 12.5: Storage Error Handling Tests
# ============================================================================


def test_file_permission_error_sync_mode(integration_tmp_path: Path):
    """Test file permission errors in sync mode."""
    from prompt_manager.core.registry import PromptRegistry
    from prompt_manager.storage.file import FileSystemStorage
    from prompt_manager.versioning.store import VersionStore

    # Create read-only directory
    readonly_dir = integration_tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o444)  # Read-only

    try:
        storage = FileSystemStorage(readonly_dir / "prompts")
        registry = PromptRegistry(storage=storage)
        version_store = VersionStore(storage_path=readonly_dir / "versions")
        manager = PromptManager(registry=registry, version_store=version_store)

        prompt = Prompt(
            id="permission_test",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test", variables=[]),
            metadata=PromptMetadata(author="Test", description="Test"),
        )

        # Sync mode should raise storage error
        with pytest.raises((StorageWriteError, PermissionError, OSError)):
            manager.create_prompt(prompt)

    finally:
        # Cleanup - restore permissions
        readonly_dir.chmod(0o755)



def test_file_permission_error_async_mode(integration_tmp_path: Path):
    """Test file permission errors in async mode."""
    from prompt_manager.core.registry import PromptRegistry
    from prompt_manager.storage.file import FileSystemStorage
    from prompt_manager.versioning.store import VersionStore

    # Create read-only directory
    readonly_dir = integration_tmp_path / "readonly_async"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o444)  # Read-only

    try:
        storage = FileSystemStorage(readonly_dir / "prompts")
        registry = PromptRegistry(storage=storage)
        version_store = VersionStore(storage_path=readonly_dir / "versions")
        manager = PromptManager(registry=registry, version_store=version_store)

        prompt = Prompt(
            id="permission_test_async",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content="Test", variables=[]),
            metadata=PromptMetadata(author="Test", description="Test"),
        )

        # Async mode should raise storage error
        with pytest.raises((StorageWriteError, PermissionError, OSError)):
            manager.create_prompt(prompt)

    finally:
        # Cleanup - restore permissions
        readonly_dir.chmod(0o755)


def test_corrupted_file_error_sync_mode(file_manager: PromptManager, integration_tmp_path: Path):
    """Test corrupted file errors in sync mode."""
    # Create a corrupted prompt file directly
    storage_path = integration_tmp_path / "prompts"
    storage_path.mkdir(exist_ok=True)
    corrupted_file = storage_path / "corrupted_prompt.json"
    corrupted_file.write_text("{invalid json content}}")

    # Try to load corrupted file
    with pytest.raises((StorageReadError, json.JSONDecodeError)):
        file_manager._registry._storage.load("corrupted_prompt")



def test_corrupted_file_error_async_mode(file_manager: PromptManager, integration_tmp_path: Path):
    """Test corrupted file errors in async mode."""
    # Create a corrupted prompt file directly
    storage_path = integration_tmp_path / "prompts"
    storage_path.mkdir(exist_ok=True)
    corrupted_file = storage_path / "corrupted_prompt_async.json"
    corrupted_file.write_text("{invalid json content}}")

    # Try to load corrupted file in async mode
    with pytest.raises((StorageReadError, json.JSONDecodeError)):
        file_manager._registry._storage.load("corrupted_prompt_async")


def test_missing_file_error_consistency(file_manager: PromptManager):
    """Test FileNotFoundError raised identically in both modes."""
    # Sync mode
    with pytest.raises(PromptNotFoundError):
        file_manager.get_prompt("definitely_does_not_exist")

    # Async mode
    def async_get():
        return file_manager.get_prompt("definitely_does_not_exist")

    with pytest.raises(PromptNotFoundError):
        asyncio.run(async_get())


def test_partial_failure_no_state_corruption_sync(file_manager: PromptManager):
    """Verify partial failures don't corrupt state in sync mode."""
    # Create a valid prompt
    valid_prompt = Prompt(
        id="valid_before_failure",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Valid", variables=[]),
        metadata=PromptMetadata(author="Test", description="Valid"),
    )
    file_manager.create_prompt(valid_prompt)

    # Attempt operation that will fail
    try:
        file_manager.get_prompt("nonexistent")
    except PromptNotFoundError:
        pass

    # Verify previous prompt still accessible
    retrieved = file_manager.get_prompt("valid_before_failure")
    assert retrieved.id == "valid_before_failure"

    # Clean up
    file_manager._registry.delete("valid_before_failure")



def test_partial_failure_no_state_corruption_async(file_manager: PromptManager):
    """Verify partial failures don't corrupt state in async mode."""
    # Create a valid prompt
    valid_prompt = Prompt(
        id="valid_before_failure_async",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Valid", variables=[]),
        metadata=PromptMetadata(author="Test", description="Valid"),
    )
    file_manager.create_prompt(valid_prompt)

    # Attempt operation that will fail
    try:
        file_manager.get_prompt("nonexistent")
    except PromptNotFoundError:
        pass

    # Verify previous prompt still accessible
    retrieved = file_manager.get_prompt("valid_before_failure_async")
    assert retrieved.id == "valid_before_failure_async"

    # Clean up
    file_manager._registry.delete("valid_before_failure_async")


def test_storage_error_handling_with_recovery(file_manager: PromptManager):
    """Test that storage errors are handled gracefully with recovery."""
    # Attempt to get nonexistent prompt
    try:
        file_manager.get_prompt("recovery_test_nonexistent")
    except PromptNotFoundError:
        pass

    # System should still work after error
    prompt = Prompt(
        id="recovery_test_success",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Success", variables=[]),
        metadata=PromptMetadata(author="Test", description="Test"),
    )
    created = file_manager.create_prompt(prompt)
    assert created.id == "recovery_test_success"

    # Clean up
    file_manager._registry.delete("recovery_test_success")
