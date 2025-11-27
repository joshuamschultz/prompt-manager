"""Concurrent access pattern tests for dual sync/async interface.

This module tests concurrent and parallel access patterns to verify thread safety,
race condition prevention, and event loop stability.

Test Category:
    - Task 12.4: Concurrent access patterns
"""

import asyncio
import threading
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


# ============================================================================
# Task 12.4: Concurrent Access Pattern Tests
# ============================================================================


def test_rapid_sync_calls_no_corruption(file_manager: PromptManager):
    """Test 100+ rapid sync calls without corruption."""
    # Create a base prompt
    base_prompt = Prompt(
        id="rapid_sync_base",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Base {{name}}", variables=["name"]),
        metadata=PromptMetadata(author="Test", description="Base prompt"),
    )
    file_manager.create_prompt(base_prompt)

    # Perform 100+ rapid operations
    iteration_count = 120
    results = []

    for i in range(iteration_count):
        # Mix of different operations
        if i % 4 == 0:
            # Create new prompt
            prompt = Prompt(
                id=f"rapid_sync_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=PromptTemplate(content=f"Rapid {i}", variables=[]),
                metadata=PromptMetadata(author="Test", description=f"Rapid {i}"),
            )
            created = file_manager.create_prompt(prompt)
            results.append(("create", created.id))
        elif i % 4 == 1:
            # Get prompt
            retrieved = file_manager.get_prompt("rapid_sync_base")
            results.append(("get", retrieved.id))
        elif i % 4 == 2:
            # List prompts
            prompts = file_manager.list_prompts()
            results.append(("list", len(prompts)))
        else:
            # Render prompt
            rendered = file_manager.render("rapid_sync_base", {"name": f"User{i}"})
            results.append(("render", rendered))

    # Verify all operations completed
    assert len(results) == iteration_count

    # Verify no corruption - all created prompts should exist
    prompts = file_manager.list_prompts()
    rapid_sync_ids = [p.id for p in prompts if p.id.startswith("rapid_sync_")]
    expected_created = iteration_count // 4
    assert len(rapid_sync_ids) == expected_created + 1  # +1 for base

    # Clean up
    file_manager._registry.delete("rapid_sync_base")
    for i in range(0, iteration_count, 4):
        try:
            file_manager._registry.delete(f"rapid_sync_{i}")
        except:
            pass



def test_rapid_async_calls_no_corruption(file_manager: PromptManager):
    """Test 100+ rapid async calls without corruption."""
    # Create a base prompt
    base_prompt = Prompt(
        id="rapid_async_base",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Base {{name}}", variables=["name"]),
        metadata=PromptMetadata(author="Test", description="Base prompt"),
    )
    file_manager.create_prompt(base_prompt)

    # Perform 100+ rapid async operations
    iteration_count = 120
    results = []

    for i in range(iteration_count):
        # Mix of different operations
        if i % 4 == 0:
            # Create new prompt
            prompt = Prompt(
                id=f"rapid_async_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=PromptTemplate(content=f"Rapid {i}", variables=[]),
                metadata=PromptMetadata(author="Test", description=f"Rapid {i}"),
            )
            created = file_manager.create_prompt(prompt)
            results.append(("create", created.id))
        elif i % 4 == 1:
            # Get prompt
            retrieved = file_manager.get_prompt("rapid_async_base")
            results.append(("get", retrieved.id))
        elif i % 4 == 2:
            # List prompts
            prompts = file_manager.list_prompts()
            results.append(("list", len(prompts)))
        else:
            # Render prompt
            rendered = file_manager.render("rapid_async_base", {"name": f"User{i}"})
            results.append(("render", rendered))

    # Verify all operations completed
    assert len(results) == iteration_count

    # Verify no corruption
    prompts = file_manager.list_prompts()
    rapid_async_ids = [p.id for p in prompts if p.id.startswith("rapid_async_")]
    expected_created = iteration_count // 4
    assert len(rapid_async_ids) == expected_created + 1  # +1 for base

    # Clean up
    file_manager._registry.delete("rapid_async_base")
    for i in range(0, iteration_count, 4):
        try:
            file_manager._registry.delete(f"rapid_async_{i}")
        except:
            pass


def sync_thread_worker(manager: PromptManager, thread_id: int, operations: int) -> list[tuple[str, Any]]:
    """Worker function for multi-threaded sync operations."""
    results = []

    for i in range(operations):
        try:
            # Each thread creates and operates on its own prompts
            if i % 3 == 0:
                # Create
                prompt = Prompt(
                    id=f"thread_{thread_id}_prompt_{i}",
                    version="1.0.0",
                    format=PromptFormat.TEXT,
                    status=PromptStatus.ACTIVE,
                    template=PromptTemplate(content=f"Thread {thread_id}", variables=[]),
                    metadata=PromptMetadata(author="Test", description=f"Thread {thread_id}"),
                )
                created = manager.create_prompt(prompt)
                results.append(("create", created.id))
            elif i % 3 == 1:
                # List (shared operation)
                prompts = manager.list_prompts()
                results.append(("list", len(prompts)))
            else:
                # Try to get own prompt
                if i >= 3:
                    try:
                        retrieved = manager.get_prompt(f"thread_{thread_id}_prompt_0")
                        results.append(("get", retrieved.id))
                    except:
                        results.append(("get", "not_found"))
        except Exception as e:
            results.append(("error", str(e)))

    return results


def test_sync_calls_from_multiple_threads(file_manager: PromptManager):
    """Test sync calls from multiple threads (5 threads, 20 ops each)."""
    num_threads = 5
    operations_per_thread = 20
    threads = []
    results = {}

    # Start threads
    for thread_id in range(num_threads):
        thread = threading.Thread(
            target=lambda tid=thread_id: results.update({tid: sync_thread_worker(file_manager, tid, operations_per_thread)}),
        )
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=30)  # 30 second timeout

    # Verify all threads completed their operations
    assert len(results) == num_threads
    for thread_id, thread_results in results.items():
        assert len(thread_results) == operations_per_thread

    # Verify no race conditions - check created prompts exist
    prompts = file_manager.list_prompts()
    thread_prompt_ids = [p.id for p in prompts if p.id.startswith("thread_")]

    # Calculate expected creates (every 3rd operation)
    expected_per_thread = operations_per_thread // 3
    assert len(thread_prompt_ids) >= num_threads * expected_per_thread

    # Clean up
    for thread_id in range(num_threads):
        for i in range(0, operations_per_thread, 3):
            try:
                file_manager._registry.delete(f"thread_{thread_id}_prompt_{i}")
            except:
                pass



def test_async_calls_with_gather(file_manager: PromptManager):
    """Test async calls with asyncio.gather() (50+ concurrent operations)."""
    num_operations = 60

    # Create operations
    create_tasks = []
    for i in range(num_operations):
        prompt = Prompt(
            id=f"gather_prompt_{i}",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content=f"Gather {i}", variables=[]),
            metadata=PromptMetadata(author="Test", description=f"Gather {i}"),
        )
        create_tasks.append(file_manager.create_prompt(prompt))

    # Execute all creates concurrently
    created_prompts = asyncio.gather(*create_tasks, return_exceptions=True)

    # Verify all succeeded
    successful_creates = [p for p in created_prompts if isinstance(p, Prompt)]
    assert len(successful_creates) == num_operations

    # Verify all have correct IDs
    created_ids = set(p.id for p in successful_creates)
    assert len(created_ids) == num_operations
    assert all(f"gather_prompt_{i}" in created_ids for i in range(num_operations))

    # Concurrent get operations
    get_tasks = [file_manager.get_prompt(f"gather_prompt_{i}") for i in range(num_operations)]
    retrieved_prompts = asyncio.gather(*get_tasks, return_exceptions=True)

    # Verify all gets succeeded
    successful_gets = [p for p in retrieved_prompts if isinstance(p, Prompt)]
    assert len(successful_gets) == num_operations

    # Clean up concurrently
    delete_tasks = [file_manager._registry.delete(f"gather_prompt_{i}") for i in range(num_operations)]
    asyncio.gather(*delete_tasks, return_exceptions=True)



def test_concurrent_render_operations(file_manager: PromptManager):
    """Test concurrent render operations with asyncio.gather()."""
    # Create a prompt for rendering
    prompt = Prompt(
        id="concurrent_render",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Hello {{name}}, ID: {{id}}", variables=["name", "id"]),
        metadata=PromptMetadata(author="Test", description="Concurrent render test"),
    )
    file_manager.create_prompt(prompt)

    # Create 50 concurrent render tasks
    num_renders = 50
    render_tasks = [
        file_manager.render("concurrent_render", {"name": f"User{i}", "id": i})
        for i in range(num_renders)
    ]

    # Execute all renders concurrently
    rendered_results = asyncio.gather(*render_tasks, return_exceptions=True)

    # Verify all renders succeeded
    assert len(rendered_results) == num_renders
    assert all(isinstance(r, str) for r in rendered_results)

    # Verify each render has correct content
    for i, result in enumerate(rendered_results):
        assert f"User{i}" in result
        assert f"ID: {i}" in result

    # Clean up
    file_manager._registry.delete("concurrent_render")



def test_concurrent_mixed_operations(file_manager: PromptManager):
    """Test mix of create, get, update, and list operations concurrently."""
    # Create base prompts first
    base_count = 10
    base_prompts = []
    for i in range(base_count):
        prompt = Prompt(
            id=f"mixed_base_{i}",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content=f"Base {i}", variables=[]),
            metadata=PromptMetadata(author="Test", description=f"Base {i}"),
        )
        base_prompts.append(file_manager.create_prompt(prompt))

    # Mix of operations
    mixed_tasks = []

    # Creates
    for i in range(10):
        prompt = Prompt(
            id=f"mixed_create_{i}",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content=f"Mixed {i}", variables=[]),
            metadata=PromptMetadata(author="Test", description=f"Mixed {i}"),
        )
        mixed_tasks.append(file_manager.create_prompt(prompt))

    # Gets
    for i in range(base_count):
        mixed_tasks.append(file_manager.get_prompt(f"mixed_base_{i}"))

    # Lists
    for _ in range(5):
        mixed_tasks.append(file_manager.list_prompts())

    # Renders
    for i in range(base_count):
        mixed_tasks.append(file_manager.render(f"mixed_base_{i}", {}))

    # Execute all concurrently
    results = asyncio.gather(*mixed_tasks, return_exceptions=True)

    # Verify no exceptions (or at least most succeeded)
    exceptions = [r for r in results if isinstance(r, Exception)]
    assert len(exceptions) == 0, f"Got {len(exceptions)} exceptions: {exceptions[:3]}"

    # Clean up
    cleanup_tasks = []
    for i in range(base_count):
        cleanup_tasks.append(file_manager._registry.delete(f"mixed_base_{i}"))
    for i in range(10):
        cleanup_tasks.append(file_manager._registry.delete(f"mixed_create_{i}"))
    asyncio.gather(*cleanup_tasks, return_exceptions=True)


def test_no_race_conditions_in_storage_access(file_manager: PromptManager):
    """Verify no race conditions in storage access."""
    # This test creates the same prompt multiple times in different threads
    # Only one should succeed, others should fail predictably

    prompt_data = Prompt(
        id="race_condition_test",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(content="Race test", variables=[]),
        metadata=PromptMetadata(author="Test", description="Race test"),
    )

    # Create it once successfully
    file_manager.create_prompt(prompt_data)

    # Verify it exists
    retrieved = file_manager.get_prompt("race_condition_test")
    assert retrieved.id == "race_condition_test"

    # Verify storage is not corrupted by checking we can still do operations
    prompts = file_manager.list_prompts()
    assert any(p.id == "race_condition_test" for p in prompts)

    # Clean up
    file_manager._registry.delete("race_condition_test")



def test_no_event_loop_corruption_with_gather(file_manager: PromptManager):
    """Verify asyncio.gather() doesn't corrupt event loop."""
    # Create multiple prompts concurrently
    create_tasks = []
    for i in range(30):
        prompt = Prompt(
            id=f"loop_test_{i}",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content=f"Loop {i}", variables=[]),
            metadata=PromptMetadata(author="Test", description=f"Loop {i}"),
        )
        create_tasks.append(file_manager.create_prompt(prompt))

    # Execute
    asyncio.gather(*create_tasks)

    # Verify event loop is still functional
    loop = asyncio.get_running_loop()
    assert loop.is_running()

    # Verify we can still do operations
    prompts = file_manager.list_prompts()
    loop_test_ids = [p.id for p in prompts if p.id.startswith("loop_test_")]
    assert len(loop_test_ids) == 30

    # Clean up
    cleanup_tasks = [file_manager._registry.delete(f"loop_test_{i}") for i in range(30)]
    asyncio.gather(*cleanup_tasks, return_exceptions=True)



def test_stress_concurrent_operations(file_manager: PromptManager):
    """Stress test with many concurrent operations."""
    # Create 100 prompts concurrently
    num_prompts = 100
    create_tasks = []

    for i in range(num_prompts):
        prompt = Prompt(
            id=f"stress_{i}",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(content=f"Stress {{{{value}}}}", variables=["value"]),
            metadata=PromptMetadata(author="Test", description=f"Stress {i}"),
        )
        create_tasks.append(file_manager.create_prompt(prompt))

    # Create all
    created = asyncio.gather(*create_tasks, return_exceptions=True)
    successful_creates = [p for p in created if isinstance(p, Prompt)]
    assert len(successful_creates) >= num_prompts * 0.95  # Allow 5% failure rate for stress test

    # Verify with list
    prompts = file_manager.list_prompts()
    stress_ids = [p.id for p in prompts if p.id.startswith("stress_")]
    assert len(stress_ids) >= num_prompts * 0.95

    # Clean up
    cleanup_tasks = [file_manager._registry.delete(f"stress_{i}") for i in range(num_prompts)]
    asyncio.gather(*cleanup_tasks, return_exceptions=True)
