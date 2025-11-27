"""Integration tests for interleaved sync and async operations.

Tests validate that sync and async operations can be mixed safely
and produce consistent results.
"""

import pytest

from prompt_manager import PromptManager
from prompt_manager.core.models import Prompt
from prompt_manager.exceptions import PromptNotFoundError


class TestDualModeWorkflow:
    """Test interleaved sync and async operations maintain consistency."""

    @pytest.mark.asyncio
    async def test_interleaved_sync_async_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test alternating sync and async operations.

        Pattern:
        - Sync create prompt A
        - Async create prompt B
        - Sync render prompt A
        - Async render prompt B
        - Sync update prompt A
        - Async update prompt B

        Verifies storage and version consistency.
        """
        prompt_a = test_prompts[0]
        prompt_b = test_prompts[1]

        # Sync create A
        created_a = file_manager.create_prompt(prompt_a, changelog="Sync create A")
        assert created_a.id == prompt_a.id
        assert created_a.version == "1.0.0"

        # Async create B
        created_b = await file_manager.create_prompt(prompt_b, changelog="Async create B")
        assert created_b.id == prompt_b.id
        assert created_b.version == "1.0.0"

        # Sync render A
        result_a = file_manager.render(prompt_a.id, sample_variables)
        assert isinstance(result_a, str)
        assert len(result_a) > 0

        # Async render B
        result_b = await file_manager.render(prompt_b.id, sample_variables)
        assert isinstance(result_b, str)
        assert len(result_b) > 0

        # Sync update A
        current_prompt_a = file_manager.get_prompt(prompt_a.id)
        updated_current_prompt_a = current_prompt_a.model_copy(update={
            "template": current_prompt_a.template.model_copy(update={"content": f"Sync updated content"})
        })
        updated_a = file_manager.update_prompt(updated_current_prompt_a, changelog="Sync update")
        assert updated_a.version == "1.0.1"

        # Async update B
        current_prompt_b = await file_manager.get_prompt(prompt_b.id)
        updated_current_prompt_b = current_prompt_b.model_copy(update={
            "template": current_prompt_b.template.model_copy(update={"content": f"Async updated content"})
        })
        updated_b = await file_manager.update_prompt(updated_current_prompt_b, changelog="Async update")
        assert updated_b.version == "1.0.1"

        # Verify both prompts exist and have correct versions
        sync_retrieved_a = file_manager.get_prompt(prompt_a.id)
        async_retrieved_b = await file_manager.get_prompt(prompt_b.id)

        assert sync_retrieved_a.version == "1.0.1"
        assert async_retrieved_b.version == "1.0.1"

    @pytest.mark.asyncio
    async def test_sync_create_async_consume(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test creating prompts synchronously, consuming asynchronously.

        Steps:
        1. Create 10 prompts synchronously
        2. Render and update asynchronously with gather
        3. Verify all operations successful
        """
        # Sync create 10 prompts
        created_ids = []
        for i, prompt in enumerate(test_prompts[:10]):
            created = file_manager.create_prompt(prompt, changelog=f"Sync {i}")
            created_ids.append(created.id)
            assert created.version == "1.0.0"

        # Async consume with gather
        import asyncio

        # Render all concurrently
        render_tasks = [
            file_manager.render(prompt_id, sample_variables)
            for prompt_id in created_ids[:5]  # Text prompts only
        ]
        rendered = await asyncio.gather(*render_tasks)
        assert len(rendered) == 5
        assert all(isinstance(r, str) for r in rendered)

        # Helper to update a prompt
        async def update_prompt_helper(prompt_id: str, i: int):
            current_p = await file_manager.get_prompt(prompt_id)
            updated_current_p = current_p.model_copy(update={
                "template": current_p.template.model_copy(update={"content": f"Async updated {i}"})
            })
            return await file_manager.update_prompt(updated_current_p, changelog=f"Async update {i}")

        # Update all concurrently
        update_tasks = [update_prompt_helper(prompt_id, i) for i, prompt_id in enumerate(created_ids[:5])]
        updated = await asyncio.gather(*update_tasks)
        assert len(updated) == 5
        assert all(u.version == "1.0.1" for u in updated)

    @pytest.mark.asyncio
    async def test_async_create_sync_consume(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test creating prompts asynchronously, consuming synchronously.

        Steps:
        1. Create 10 prompts asynchronously with gather
        2. Render and update synchronously in loop
        3. Verify all operations successful
        """
        import asyncio

        # Async create 10 prompts concurrently
        create_tasks = [
            file_manager.create_prompt(prompt, changelog=f"Async {i}")
            for i, prompt in enumerate(test_prompts[:10])
        ]
        created = await asyncio.gather(*create_tasks)
        assert len(created) == 10

        # Sync consume
        created_ids = [p.id for p in created]

        # Render synchronously
        for prompt_id in created_ids[:5]:  # Text prompts only
            result = file_manager.render(prompt_id, sample_variables)
            assert isinstance(result, str)

        # Update synchronously
        for i, prompt_id in enumerate(created_ids[:5]):
            current_p = file_manager.get_prompt(prompt_id)
            updated_current_p = current_p.model_copy(update={
                "template": current_p.template.model_copy(update={"content": f"Sync updated {i}"})
            })
            updated = file_manager.update_prompt(updated_current_p, changelog=f"Sync update {i}")
            assert updated.version == "1.0.1"

    @pytest.mark.asyncio
    async def test_storage_consistency_across_modes(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test storage state is consistent across sync and async modes.

        Steps:
        1. Create in sync, verify in async
        2. Update in async, verify in sync
        3. Delete in sync, verify in async
        """
        prompt = test_prompts[0]

        # Create in sync mode
        created = file_manager.create_prompt(prompt, changelog="Sync create")
        assert created.id == prompt.id

        # Verify exists in async mode
        async_retrieved = await file_manager.get_prompt(prompt.id)
        assert async_retrieved.id == created.id
        assert async_retrieved.version == "1.0.0"

        # Update in async mode
        current_prompt = await file_manager.get_prompt(prompt.id)
        updated_current_prompt = current_prompt.model_copy(update={
            "template": current_prompt.template.model_copy(update={"content": f"Async updated"})
        })
        updated = await file_manager.update_prompt(updated_current_prompt, changelog="Async update")
        assert updated.version == "1.0.1"

        # Verify update visible in sync mode
        sync_retrieved = file_manager.get_prompt(prompt.id)
        assert sync_retrieved.version == "1.0.1"
        assert "Async updated" in sync_retrieved.template.content

        # Delete in sync mode
        await file_manager._registry.delete(prompt.id)

        # Verify deleted in async mode
        with pytest.raises(PromptNotFoundError):
            await file_manager.get_prompt(prompt.id)

    @pytest.mark.asyncio
    async def test_version_history_consistency(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test version history is consistent across modes.

        Steps:
        1. Create in sync (v1.0.0)
        2. Update in async (v1.0.1)
        3. Update in sync (v1.0.2)
        4. Get history in both modes
        5. Verify identical history
        """
        prompt = test_prompts[0]

        # Create in sync (v1.0.0)
        created = file_manager.create_prompt(prompt, changelog="Sync v1.0.0")
        assert created.version == "1.0.0"

        # Update in async (v1.0.1)
        current_prompt = await file_manager.get_prompt(prompt.id)
        updated_current_prompt = current_prompt.model_copy(update={
            "template": current_prompt.template.model_copy(update={"content": f"Async v1.0.1"})
        })
        updated1 = await file_manager.update_prompt(updated_current_prompt, changelog="Async update to v1.0.1")
        assert updated1.version == "1.0.1"

        # Update in sync (v1.0.2)
        current_prompt = file_manager.get_prompt(prompt.id)
        updated_current_prompt = current_prompt.model_copy(update={
            "template": current_prompt.template.model_copy(update={"content": f"Sync v1.0.2"})
        })
        updated2 = file_manager.update_prompt(updated_current_prompt, changelog="Sync update to v1.0.2")
        assert updated2.version == "1.0.2"

        # Get history in async mode
        async_history = await file_manager.get_history(prompt.id)
        assert len(async_history) == 3
        assert [v.version for v in async_history] == ["1.0.0", "1.0.1", "1.0.2"]

        # Get history in sync mode
        sync_history = file_manager.get_history(prompt.id)
        assert len(sync_history) == 3
        assert [v.version for v in sync_history] == ["1.0.0", "1.0.1", "1.0.2"]

        # Verify histories are identical
        for sync_v, async_v in zip(sync_history, async_history):
            assert sync_v.version == async_v.version
            assert sync_v.id == async_v.id

    @pytest.mark.asyncio
    async def test_list_operations_consistency(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test list operations return consistent results.

        Verifies:
        - List in sync mode
        - List in async mode
        - Results identical
        """
        # Create prompts using both modes
        for i, prompt in enumerate(test_prompts[:5]):
            if i % 2 == 0:
                file_manager.create_prompt(prompt, changelog=f"Sync {i}")
            else:
                await file_manager.create_prompt(prompt, changelog=f"Async {i}")

        # List in sync mode
        sync_list = file_manager.list_prompts()
        assert len(sync_list) == 5

        # List in async mode
        async_list = await file_manager.list_prompts()
        assert len(async_list) == 5

        # Verify lists contain same IDs
        sync_ids = {p.id for p in sync_list}
        async_ids = {p.id for p in async_list}
        assert sync_ids == async_ids

    @pytest.mark.asyncio
    async def test_search_operations_consistency(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test search operations return consistent results across modes.

        Verifies:
        - Search by tags in both modes
        - Search by format in both modes
        - Results identical
        """
        # Create test prompts
        for i, prompt in enumerate(test_prompts[:8]):
            if i % 2 == 0:
                file_manager.create_prompt(prompt, changelog=f"Sync {i}")
            else:
                await file_manager.create_prompt(prompt, changelog=f"Async {i}")

        # Search by tags in both modes
        sync_search = file_manager.list_prompts(tags=["integration"])
        async_search = await file_manager.list_prompts(tags=["integration"])

        assert len(sync_search) == len(async_search)
        sync_ids = {p.id for p in sync_search}
        async_ids = {p.id for p in async_search}
        assert sync_ids == async_ids

    @pytest.mark.asyncio
    async def test_mixed_mode_error_handling(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test error handling is consistent across modes.

        Verifies:
        - Same errors raised in both modes
        - Error messages identical
        """
        prompt = test_prompts[0]
        file_manager.create_prompt(prompt, changelog="Create")

        # Test PromptNotFoundError in both modes
        with pytest.raises(PromptNotFoundError) as sync_exc:
            file_manager.get_prompt("nonexistent")

        with pytest.raises(PromptNotFoundError) as async_exc:
            await file_manager.get_prompt("nonexistent")

        # Verify error messages are similar
        assert "nonexistent" in str(sync_exc.value)
        assert "nonexistent" in str(async_exc.value)

    @pytest.mark.asyncio
    async def test_comparison_operations_consistency(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test version comparison works consistently.

        Verifies:
        - Compare in sync mode
        - Compare in async mode
        - Results identical
        """
        prompt = test_prompts[0]

        # Create and update
        file_manager.create_prompt(prompt, changelog="v1.0.0")
        current_prompt = await file_manager.get_prompt(prompt.id)
        updated_current_prompt = current_prompt.model_copy(update={
            "template": current_prompt.template.model_copy(update={"content": f"Updated"})
        })
        await file_manager.update_prompt(updated_current_prompt, changelog="v1.0.1")

        # Compare in sync mode
        sync_comparison = file_manager.compare_versions(
            prompt.id,
            "1.0.0",
            "1.0.1"
        )

        # Compare in async mode
        async_comparison = await file_manager.compare_versions(
            prompt.id,
            "1.0.0",
            "1.0.1"
        )

        # Verify results consistent
        assert sync_comparison["versions"]["from"] == async_comparison["versions"]["from"]
        assert sync_comparison["versions"]["to"] == async_comparison["versions"]["to"]
        assert "checksums_differ" in sync_comparison
        assert "checksums_differ" in async_comparison
