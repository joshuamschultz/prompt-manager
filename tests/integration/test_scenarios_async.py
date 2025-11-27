"""End-to-end user scenarios for asynchronous usage.

Tests real-world async usage patterns including FastAPI, aiohttp,
and concurrent operations.
"""

import asyncio
import time

import pytest

from prompt_manager import PromptManager
from prompt_manager.core.models import (
    Prompt,
    PromptFormat,
    PromptStatus,
)
from prompt_manager.exceptions import PromptNotFoundError


class TestAsyncUserScenarios:
    """Test real-world asynchronous usage patterns."""

    @pytest.mark.asyncio
    async def test_fastapi_integration_simulation(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Simulate FastAPI request handler with running event loop.

        Scenario:
        - Running event loop (like FastAPI)
        - Use async interface with await
        - Perform CRUD in handler context
        - Verify works correctly
        """
        # This test runs in pytest-asyncio which creates event loop
        # Simulates FastAPI handler

        async def fastapi_handler_create():
            """Simulate POST /prompts endpoint."""
            prompt = test_prompts[0]
            created = await file_manager.create_prompt(prompt, changelog="API create")
            return created

        async def fastapi_handler_get(prompt_id: str):
            """Simulate GET /prompts/{id} endpoint."""
            return await file_manager.get_prompt(prompt_id)

        async def fastapi_handler_render(prompt_id: str, variables: dict):
            """Simulate POST /prompts/{id}/render endpoint."""
            return await file_manager.render(prompt_id, variables)

        async def fastapi_handler_list():
            """Simulate GET /prompts endpoint."""
            return await file_manager.list_prompts()

        # Simulate request flow
        created = await fastapi_handler_create()
        assert created.id == test_prompts[0].id

        retrieved = await fastapi_handler_get(created.id)
        assert retrieved.id == created.id

        result = await fastapi_handler_render(created.id, sample_variables)
        assert isinstance(result, str)

        prompts = await fastapi_handler_list()
        assert len(prompts) == 1

    @pytest.mark.asyncio
    async def test_aiohttp_integration_simulation(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Simulate aiohttp handler with running event loop.

        Scenario:
        - Running event loop (like aiohttp)
        - Use async interface
        - Verify no conflicts with aiohttp's loop
        """
        # Simulate aiohttp handler
        async def aiohttp_handler(request_data: dict):
            """Simulate aiohttp request handler."""
            action = request_data["action"]

            if action == "create":
                prompt = test_prompts[0]
                return await file_manager.create_prompt(prompt, changelog="aiohttp create")
            elif action == "render":
                return await file_manager.render(
                    request_data["prompt_id"],
                    request_data["variables"]
                )
            elif action == "list":
                return await file_manager.list_prompts()

        # Simulate multiple requests
        created = await aiohttp_handler({"action": "create"})
        assert created.id == test_prompts[0].id

        result = await aiohttp_handler({
            "action": "render",
            "prompt_id": created.id,
            "variables": sample_variables
        })
        assert isinstance(result, str)

        prompts = await aiohttp_handler({"action": "list"})
        assert len(prompts) == 1

    @pytest.mark.asyncio
    async def test_concurrent_operations_with_gather(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test concurrent operations with asyncio.gather().

        Tests:
        - 50 concurrent creates
        - 50 concurrent renders
        - 50 concurrent updates
        - All successful, no race conditions
        """
        # Prepare 50 prompts
        prompts_to_create = []
        for i in range(50):
            prompt = Prompt(
                id=f"concurrent_test_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            prompts_to_create.append(prompt)

        # 50 concurrent creates
        start = time.perf_counter()
        created = await asyncio.gather(
            *[
                file_manager.create_prompt(p, changelog=f"Create {i}")
                for i, p in enumerate(prompts_to_create)
            ]
        )
        create_time = time.perf_counter() - start
        assert len(created) == 50
        print(f"\n50 concurrent creates: {create_time:.2f}s")

        # 50 concurrent renders
        start = time.perf_counter()
        rendered = await asyncio.gather(
            *[
                file_manager.render(p.id, sample_variables)
                for p in created
            ]
        )
        render_time = time.perf_counter() - start
        assert len(rendered) == 50
        assert all(isinstance(r, str) for r in rendered)
        print(f"50 concurrent renders: {render_time:.2f}s")

        # 50 concurrent updates
        # Helper to update a prompt
        async def update_prompt_helper(prompt: Prompt, i: int):
            current_p = await file_manager.get_prompt(prompt.id)
            updated_current_p = current_p.model_copy(update={
                "template": current_p.template.model_copy(update={"content": f"Updated {i}"})
            })
            return await file_manager.update_prompt(updated_current_p, changelog=f"Update {i}")

        start = time.perf_counter()
        updated = await asyncio.gather(
            *[update_prompt_helper(p, i) for i, p in enumerate(created)]
        )
        update_time = time.perf_counter() - start
        assert len(updated) == 50
        assert all(u.version == "1.0.1" for u in updated)
        print(f"50 concurrent updates: {update_time:.2f}s")

        # Verify all operations successful
        all_prompts = await file_manager.list_prompts()
        assert len(all_prompts) == 50

    @pytest.mark.asyncio
    async def test_streaming_with_as_completed(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test streaming results with asyncio.as_completed().

        Tests:
        - Create 100 prompts
        - Render all with as_completed()
        - Process results as they arrive
        - Order doesn't matter
        - All complete
        """
        # Create 100 prompts
        prompts_to_create = []
        for i in range(100):
            prompt = Prompt(
                id=f"stream_test_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            prompts_to_create.append(prompt)

        created = await asyncio.gather(
            *[
                file_manager.create_prompt(p, changelog=f"Create {i}")
                for i, p in enumerate(prompts_to_create)
            ]
        )
        assert len(created) == 100

        # Render with as_completed
        render_tasks = [
            file_manager.render(p.id, sample_variables)
            for p in created
        ]

        results = []
        start = time.perf_counter()
        for coro in asyncio.as_completed(render_tasks):
            result = await coro
            assert isinstance(result, str)
            results.append(result)

        elapsed = time.perf_counter() - start
        print(f"\n100 renders with as_completed: {elapsed:.2f}s")

        assert len(results) == 100

    @pytest.mark.asyncio
    async def test_async_error_handling(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test error handling in async context.

        Tests:
        - Exceptions propagate correctly
        - Stack traces preserved
        - Error messages helpful
        - Manager remains functional
        """
        # Create a prompt
        prompt = test_prompts[0]
        created = await file_manager.create_prompt(prompt, changelog="Initial")

        # Trigger PromptNotFoundError
        with pytest.raises(PromptNotFoundError) as exc_info:
            await file_manager.get_prompt("nonexistent_prompt")

        # Verify error message
        assert "nonexistent_prompt" in str(exc_info.value)

        # Verify manager still works after error
        retrieved = await file_manager.get_prompt(created.id)
        assert retrieved.id == created.id

        # Multiple errors don't corrupt state
        for i in range(5):
            with pytest.raises(PromptNotFoundError):
                await file_manager.get_prompt(f"nonexistent_{i}")

        # Manager still functional
        another = await file_manager.create_prompt(test_prompts[1], changelog="After errors")
        assert another.id == test_prompts[1].id

    @pytest.mark.asyncio
    async def test_async_batch_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test batch operations in async mode.

        Tests:
        - Concurrent batch creates
        - Concurrent batch updates
        - Concurrent batch deletes
        - Verify all successful
        """
        # Batch create 100 prompts concurrently
        prompts_to_create = []
        for i in range(100):
            prompt = Prompt(
                id=f"batch_async_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            prompts_to_create.append(prompt)

        created = await asyncio.gather(
            *[
                file_manager.create_prompt(p, changelog=f"Batch {i}")
                for i, p in enumerate(prompts_to_create)
            ]
        )
        assert len(created) == 100

        # Helper to update a prompt
        async def update_prompt_helper(prompt: Prompt, i: int):
            current_p = await file_manager.get_prompt(prompt.id)
            updated_current_p = current_p.model_copy(update={
                "template": current_p.template.model_copy(update={"content": f"Batch update {i}"})
            })
            return await file_manager.update_prompt(updated_current_p, changelog=f"Update {i}")

        # Batch update first 50 concurrently
        updated = await asyncio.gather(
            *[update_prompt_helper(p, i) for i, p in enumerate(created[:50])]
        )
        assert len(updated) == 50
        assert all(u.version == "1.0.1" for u in updated)

        # Batch delete first 25 concurrently
        await asyncio.gather(
            *[await file_manager._registry.delete(p.id) for p in created[:25]]
        )

        # Verify counts
        remaining = await file_manager.list_prompts()
        assert len(remaining) == 75

    @pytest.mark.asyncio
    async def test_async_search_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test search operations in async mode.

        Tests:
        - Concurrent creates of diverse prompts
        - Search by various criteria
        - Combine searches
        """
        # Create diverse prompts
        await asyncio.gather(
            *[
                file_manager.create_prompt(p, changelog=f"Create {i}")
                for i, p in enumerate(test_prompts[:10])
            ]
        )

        # Search by tag
        integration_prompts = await file_manager.list_prompts(tags=["integration"])
        assert len(integration_prompts) >= 10

        # Search by format
        text_prompts = await file_manager.list_prompts(format=PromptFormat.TEXT)
        chat_prompts = await file_manager.list_prompts(format=PromptFormat.CHAT)
        assert len(text_prompts) >= 5
        assert len(chat_prompts) >= 3

        # Combined search
        complex_prompts = await file_manager.list_prompts(tags=["integration", "complex"])
        assert len(complex_prompts) >= 1

    @pytest.mark.asyncio
    async def test_async_version_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test version operations in async mode.

        Tests:
        - Sequential updates
        - Get history
        - Compare versions
        - All async
        """
        prompt = test_prompts[0]

        # Create and update multiple times
        created = await file_manager.create_prompt(prompt, changelog="v1.0.0")
        assert created.version == "1.0.0"

        # 10 updates
        current = created
        for i in range(1, 11):
            current_current = await file_manager.get_prompt(current.id)
            updated_current_current = current_current.model_copy(update={
                "template": current_current.template.model_copy(update={"content": f"Version {i}: {prompt.template.content}"})
            })
            updated = await file_manager.update_prompt(updated_current_current, changelog=f"Update to v1.0.{i}")
            assert updated.version == f"1.0.{i}"
            current = updated

        # Get full history
        history = await file_manager.get_history(prompt.id)
        assert len(history) == 11

        # Compare first and last
        comparison = await file_manager.compare_versions(
            prompt.id,
            "1.0.0",
            "1.0.10"
        )
        assert comparison["versions"]["from"] == "1.0.0"
        assert comparison["versions"]["to"] == "1.0.10"

    @pytest.mark.asyncio
    async def test_async_large_prompt_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test large prompt operations in async mode.

        Tests:
        - Create large prompts
        - Render with large variables
        - Concurrent large operations
        """
        # Get large template
        large_prompt = test_prompts[-1]
        assert len(large_prompt.template.content) > 8000

        # Create large prompt
        created = await file_manager.create_prompt(large_prompt, changelog="Large")
        assert created.id == large_prompt.id

        # Render with large variable
        large_var = "C" * 10000
        result = await file_manager.render(large_prompt.id, {"name": large_var})
        assert len(result) > 50000

        # Multiple concurrent renders of large prompt
        results = await asyncio.gather(
            *[
                file_manager.render(large_prompt.id, {"name": f"D{i}" * 1000})
                for i in range(10)
            ]
        )
        assert len(results) == 10
        assert all(len(r) > 50000 for r in results)

    @pytest.mark.asyncio
    async def test_async_mixed_operation_patterns(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test various mixed async operation patterns.

        Tests:
        - Create some, then render all
        - Update some, then delete some
        - Interleaved operations
        - Complex workflows
        """
        # Pattern 1: Create batch, render all
        prompts_batch1 = []
        for i in range(20):
            prompt = Prompt(
                id=f"pattern1_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            prompts_batch1.append(prompt)

        created1 = await asyncio.gather(
            *[file_manager.create_prompt(p, changelog=f"P1 {i}") for i, p in enumerate(prompts_batch1)]
        )

        rendered1 = await asyncio.gather(
            *[file_manager.render(p.id, sample_variables) for p in created1]
        )
        assert len(rendered1) == 20

        # Helper to update a prompt
        async def update_prompt_helper2(prompt: Prompt, i: int):
            current_p = await file_manager.get_prompt(prompt.id)
            updated_current_p = current_p.model_copy(update={
                "template": current_p.template.model_copy(update={"content": f"Updated {i}"})
            })
            return await file_manager.update_prompt(updated_current_p, changelog=f"Update {i}")

        # Pattern 2: Update some, delete others
        await asyncio.gather(
            *[update_prompt_helper2(p, i) for i, p in enumerate(created1[:10])]
        )

        await asyncio.gather(
            *[await file_manager._registry.delete(p.id) for p in created1[10:15]]
        )

        # Verify state
        remaining = await file_manager.list_prompts()
        assert len(remaining) == 15

    @pytest.mark.asyncio
    async def test_async_real_world_api_simulation(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Simulate real-world API usage pattern.

        Scenario:
        - Multiple concurrent API requests
        - Each performs various operations
        - Verify all succeed
        - No conflicts
        """
        async def api_request_1():
            """Simulate user 1 creating and rendering."""
            prompt = Prompt(
                id="user1_prompt",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            created = await file_manager.create_prompt(prompt, changelog="User 1 create")
            result = await file_manager.render(created.id, sample_variables)
            return created, result

        async def api_request_2():
            """Simulate user 2 creating and updating."""
            prompt = Prompt(
                id="user2_prompt",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[1].template,
                metadata=test_prompts[1].metadata,
            )
            created = await file_manager.create_prompt(prompt, changelog="User 2 create")
            current_created = await file_manager.get_prompt(created.id)
            updated_current_created = current_created.model_copy(update={
                "template": current_created.template.model_copy(update={"content": f"User 2 update"})
            })
            updated = await file_manager.update_prompt(updated_current_created, changelog="Update")
            return created, updated

        async def api_request_3():
            """Simulate user 3 listing and searching."""
            prompts = await file_manager.list_prompts()
            search_results = await file_manager.list_prompts(tags=["integration"])
            return prompts, search_results

        # Execute all API requests concurrently
        results = await asyncio.gather(
            api_request_1(),
            api_request_2(),
            api_request_3(),
        )

        # Verify all succeeded
        assert len(results) == 3

        # Request 1: created and rendered
        created1, rendered1 = results[0]
        assert created1.id == "user1_prompt"
        assert isinstance(rendered1, str)

        # Request 2: created and updated
        created2, updated2 = results[1]
        assert created2.id == "user2_prompt"
        assert updated2.version == "1.0.1"

        # Request 3: listed and searched
        prompts_list, search_results = results[2]
        # Should see at least the 2 prompts created by requests 1 & 2
        assert len(prompts_list) >= 2
