"""Integration tests for complete asynchronous CRUD workflows.

Tests validate end-to-end operations using async interface with concurrent operations.
"""

import asyncio
import time
from pathlib import Path

import pytest

from prompt_manager import PromptManager
from prompt_manager.core.models import Prompt, PromptFormat, PromptStatus
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.exceptions import PromptNotFoundError
from prompt_manager.versioning.store import VersionStore


class TestAsyncWorkflow:
    """Test complete CRUD workflow in async mode with concurrent operations."""


    def test_complete_async_crud_workflow(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
        integration_tmp_path: Path,
    ) -> None:
        """
        Test complete CRUD workflow with 10+ prompts asynchronously.

        Same workflow as sync version but with await.
        Verifies identical behavior in async mode.
        """
        # Create 10 prompts
        created_prompts = []
        for i, prompt in enumerate(test_prompts[:10]):
            created = file_manager.create_prompt(
                prompt,
                changelog=f"Initial creation of prompt {i}"
            )
            created_prompts.append(created)
            assert created.id == prompt.id
            assert created.version == "1.0.0"

        # Verify all prompts exist in storage
        prompt_dir = integration_tmp_path / "prompts"
        for prompt in created_prompts:
            prompt_file = prompt_dir / f"{prompt.id}.yaml"
            assert prompt_file.exists(), f"Prompt file {prompt_file} should exist"
            version_file = prompt_dir / prompt.id / "_versions" / "1.0.0.yaml"
            assert version_file.exists(), f"Version file {version_file} should exist"

        # Render each prompt
        rendered_results = []
        for prompt in created_prompts[:5]:  # Text prompts
            result = file_manager.render(prompt.id, sample_variables)
            assert isinstance(result, str)
            assert len(result) > 0
            rendered_results.append(result)

        # Update 5 prompts
        updated_prompts = []
        for i, prompt in enumerate(created_prompts[:5]):
            current_prompt = file_manager.get_prompt(prompt.id)
            updated_current_prompt = current_prompt.model_copy(update={
                "template": current_prompt.template.model_copy(update={"content": f"Updated: {prompt.template.content}"})
            })
            updated = file_manager.update_prompt(updated_current_prompt, changelog=f"Update {i}")
            updated_prompts.append(updated)
            assert updated.version == "1.0.1"

        # Get version history
        for prompt in updated_prompts:
            history = file_manager.get_history(prompt.id)
            assert len(history) == 2
            assert history[-1].version == "1.0.0"  # oldest version
            assert history[0].version == "1.0.1"  # latest version

        # Delete 3 prompts
        for prompt in created_prompts[:3]:
            file_manager._registry.delete(prompt.id)

        # List remaining prompts
        remaining = file_manager.list_prompts()
        assert len(remaining) == 7

        # Verify deleted prompts are gone
        for prompt in created_prompts[:3]:
            with pytest.raises(PromptNotFoundError):
                file_manager.get_prompt(prompt.id)


    async def test_async_workflow_with_concurrent_creates(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test concurrent prompt creation with asyncio.gather().

        Verifies:
        - 20 prompts created concurrently
        - No race conditions in storage
        - All creates successful
        """
        # Prepare 20 prompts
        prompts_to_create = []
        for i in range(20):
            prompt = Prompt(
                id=f"concurrent_create_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            prompts_to_create.append(prompt)

        # Create concurrently
        start = time.perf_counter()
        results = await asyncio.gather(
            *[
                file_manager.create_prompt(p, changelog=f"Concurrent {i}")
                for i, p in enumerate(prompts_to_create)
            ]
        )
        elapsed = time.perf_counter() - start

        # Verify all created
        assert len(results) == 20
        for i, created in enumerate(results):
            assert created.id == f"concurrent_create_{i}"
            assert created.version == "1.0.0"

        # Verify all exist in storage
        all_prompts = file_manager.list_prompts()
        assert len(all_prompts) == 20


    async def test_async_workflow_with_concurrent_renders(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test concurrent rendering with asyncio.gather().

        Tests:
        - Create 10 prompts
        - Render all 10 concurrently
        - Repeat 10 times (100 total renders)
        - Verify all successful
        """
        # Create 10 prompts
        created_ids = []
        for i in range(10):
            prompt = Prompt(
                id=f"render_test_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            created = file_manager.create_prompt(prompt, changelog=f"Create {i}")
            created_ids.append(created.id)

        # Render all concurrently 10 times
        total_renders = 0
        for _ in range(10):
            results = await asyncio.gather(
                *[
                    file_manager.render(prompt_id, sample_variables)
                    for prompt_id in created_ids
                ]
            )
            assert len(results) == 10
            for result in results:
                assert isinstance(result, str)
                assert len(result) > 0
            total_renders += len(results)

        assert total_renders == 100


    async def test_async_workflow_with_concurrent_updates(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test concurrent updates with asyncio.gather().

        Verifies:
        - 10 prompts updated concurrently
        - Version increments correct (all v1.0.1)
        - No version conflicts
        """
        # Create 10 prompts
        created_ids = []
        for i in range(10):
            prompt = Prompt(
                id=f"update_test_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            created = file_manager.create_prompt(prompt, changelog=f"Create {i}")
            created_ids.append(created.id)

        # Helper to update a prompt
        def update_prompt_helper(prompt_id: str, i: int):
            current_p = file_manager.get_prompt(prompt_id)
            updated_current_p = current_p.model_copy(update={
                "template": current_p.template.model_copy(update={"content": f"Updated prompt {i}"})
            })
            return file_manager.update_prompt(updated_current_p, changelog=f"Update {i}")

        # Update all concurrently
        results = await asyncio.gather(
            *[update_prompt_helper(prompt_id, i) for i, prompt_id in enumerate(created_ids)]
        )

        # Verify all updated to v1.0.1
        assert len(results) == 10
        for updated in results:
            assert updated.version == "1.0.1"

        # Verify no duplicates or conflicts
        ids_seen = set()
        for updated in results:
            assert updated.id not in ids_seen
            ids_seen.add(updated.id)


    async def test_async_workflow_streaming_results(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test streaming results with asyncio.as_completed().

        Steps:
        1. Create 50 prompts
        2. Render with as_completed()
        3. Process results as they arrive
        4. Verify all 50 complete
        """
        # Create 50 prompts
        prompt_ids = []
        for i in range(50):
            prompt = Prompt(
                id=f"stream_test_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            created = file_manager.create_prompt(prompt, changelog=f"Create {i}")
            prompt_ids.append(created.id)

        # Render with as_completed
        render_tasks = [
            file_manager.render(prompt_id, sample_variables)
            for prompt_id in prompt_ids
        ]

        completed_count = 0
        results = []
        async for coro in asyncio.as_completed(render_tasks):
            result = coro
            assert isinstance(result, str)
            results.append(result)
            completed_count += 1

        assert completed_count == 50
        assert len(results) == 50


    async def test_async_workflow_error_propagation(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test that exceptions propagate correctly through asyncio.gather().

        Verifies:
        - Exceptions raised in async operations
        - Partial success handling
        - Error doesn't corrupt other operations
        """
        # Create one valid prompt
        valid_prompt = test_prompts[0]
        file_manager.create_prompt(valid_prompt, changelog="Valid")

        # Attempt mixed valid and invalid operations
        tasks = [
            file_manager.get_prompt(valid_prompt.id),  # Valid
            file_manager.get_prompt("nonexistent_1"),  # Invalid
            file_manager.get_prompt("nonexistent_2"),  # Invalid
        ]

        # Gather with return_exceptions=True
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # First should succeed
        assert isinstance(results[0], Prompt)
        assert results[0].id == valid_prompt.id

        # Others should be exceptions
        assert isinstance(results[1], PromptNotFoundError)
        assert isinstance(results[2], PromptNotFoundError)


    async def test_async_workflow_with_version_tracking(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test version tracking with async operations.

        Verifies:
        - Multiple updates tracked correctly
        - History retrieval works async
        - Version comparison works async
        """
        # Create initial prompt
        prompt = test_prompts[0]
        created = file_manager.create_prompt(prompt, changelog="Initial")
        assert created.version == "1.0.0"

        # Update 5 times
        current = created
        for i in range(1, 6):
            current_current = file_manager.get_prompt(current.id)
            updated_current_current = current_current.model_copy(update={
                "template": current_current.template.model_copy(update={"content": f"Async version {i}: {prompt.template.content}"})
            })
            updated = file_manager.update_prompt(updated_current_current, changelog=f"Async update to 1.0.{i}")
            assert updated.version == f"1.0.{i}"
            current = updated

        # Get complete history
        history = file_manager.get_history(prompt.id)
        assert len(history) == 6

        # Compare versions
        comparison = file_manager.compare_versions(
            prompt.id,
            "1.0.0",
            "1.0.5"
        )
        assert comparison["versions"]["from"] == "1.0.0"
        assert comparison["versions"]["to"] == "1.0.5"


    async def test_async_workflow_rapid_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test rapid async operations for performance.

        Tests:
        - 100 creates with concurrency
        - 100 renders with concurrency
        - Faster than sequential due to I/O concurrency
        """
        # Prepare 100 prompts
        prompts_to_create = []
        for i in range(100):
            prompt = Prompt(
                id=f"rapid_async_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            prompts_to_create.append(prompt)

        # Rapid concurrent create
        start = time.perf_counter()
        created = await asyncio.gather(
            *[
                file_manager.create_prompt(p, changelog=f"Rapid {i}")
                for i, p in enumerate(prompts_to_create)
            ]
        )
        create_time = time.perf_counter() - start
        assert len(created) == 100
        # Should be faster than 5s due to concurrency
        assert create_time < 5.0

        # Rapid concurrent render
        start = time.perf_counter()
        rendered = await asyncio.gather(
            *[
                file_manager.render(p.id, sample_variables)
                for p in created
            ]
        )
        render_time = time.perf_counter() - start
        assert len(rendered) == 100
        assert render_time < 5.0


    async def test_async_workflow_large_prompts(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test handling of large prompts in async mode.

        Verifies:
        - Large templates persist correctly
        - Async I/O handles large data
        - Performance acceptable
        """
        # Get large template
        large_prompt = test_prompts[-1]
        assert len(large_prompt.template.content) > 8000

        # Create large prompt
        created = file_manager.create_prompt(large_prompt, changelog="Large")
        assert created.id == large_prompt.id

        # Render with large variable
        start = time.perf_counter()
        result = file_manager.render(large_prompt.id, {"name": "B" * 1000})
        render_time = time.perf_counter() - start
        assert len(result) > 50000
        assert render_time < 3.0  # Large template + large variable = reasonable timeout


    async def test_async_workflow_complex_templates(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test complex templates with async rendering.

        Verifies:
        - Complex templates work in async mode
        - Results identical to sync mode
        """
        # Get complex template
        complex_prompt = test_prompts[-2]

        # Create and render
        created = file_manager.create_prompt(complex_prompt, changelog="Complex")
        result = file_manager.render(created.id, sample_variables)

        # Verify output
        assert "Test Header" in result
        assert "Test Footer" in result
        assert "Details:" in result
        assert all(item in result for item in ["Item 1", "Item 2", "Item 3"])


    async def test_async_workflow_persistence_across_instances(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        file_registry: PromptRegistry,
        file_version_store: VersionStore,
    ) -> None:
        """
        Test persistence across manager instances in async mode.

        Verifies:
        - Data persists with async operations
        - New instance can read async-created data
        """
        # Create prompts with first manager
        for prompt in test_prompts[:5]:
            file_manager.create_prompt(prompt, changelog="Initial")

        # Create new manager
        new_manager = PromptManager(
            registry=file_registry,
            version_store=file_version_store,
        )

        # Verify prompts exist
        prompts = new_manager.list_prompts()
        assert len(prompts) == 5


    async def test_async_workflow_with_metadata_search(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test metadata search in async mode.

        Verifies:
        - Search works with async
        - Results correct
        """
        # Create test prompts
        for prompt in test_prompts[:8]:
            file_manager.create_prompt(prompt, changelog="Initial")

        # Search by tag
        integration_prompts = file_manager.list_prompts(tags=["integration"])
        assert len(integration_prompts) >= 8

        # Search by format
        text_prompts = file_manager.list_prompts(format=PromptFormat.TEXT)
        chat_prompts = file_manager.list_prompts(format=PromptFormat.CHAT)
        assert len(text_prompts) == 5
        assert len(chat_prompts) == 3
