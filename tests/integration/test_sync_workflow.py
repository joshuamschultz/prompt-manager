"""Integration tests for complete synchronous CRUD workflows.

Tests validate end-to-end operations using sync interface with real persistence.
"""

import time
from pathlib import Path

import pytest

from prompt_manager import PromptManager
from prompt_manager.core.models import (
    Prompt,
    PromptFormat,
    PromptStatus,
)
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.exceptions import PromptNotFoundError
from prompt_manager.versioning.store import VersionStore


class TestSyncWorkflow:
    """Test complete CRUD workflow in sync mode with real persistence."""

    def test_complete_sync_crud_workflow(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
        integration_tmp_path: Path,
    ) -> None:
        """
        Test complete CRUD workflow with 10+ prompts synchronously.

        Steps:
        1. Create 10 prompts
        2. Render each with variables
        3. Update 5 prompts
        4. Get version history for updated prompts
        5. Delete 3 prompts
        6. List remaining prompts
        7. Verify FileSystemStorage persisted correctly
        8. Verify VersionStore has complete history
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

        # Render text prompts only (first 5 are text)
        rendered_results = []
        for prompt in created_prompts[:5]:
            result = file_manager.render(prompt.id, sample_variables)
            assert isinstance(result, str)
            assert len(result) > 0
            rendered_results.append(result)

        # Update 5 prompts - get, modify, update
        updated_prompts = []
        for i, prompt in enumerate(created_prompts[:5]):
            current = file_manager.get_prompt(prompt.id)
            updated_current = current.model_copy(update={
                "template": current.template.model_copy(update={"content": f"Updated: {current.template.content}"})
            })
            updated = file_manager.update_prompt(updated_current, changelog=f"Update {i}")
            updated_prompts.append(updated)
            assert updated.version == "1.0.1"

        # Get version history
        for prompt in updated_prompts:
            history = file_manager.get_history(prompt.id)
            assert len(history) == 2  # v1.0.0 and v1.0.1
            assert history[-1].version == "1.0.0"  # oldest version
            assert history[0].version == "1.0.1"  # latest version

        # Verify version files exist
        prompt_dir = integration_tmp_path / "prompts"
        for prompt in updated_prompts:
            v1_file = prompt_dir / prompt.id / "_versions" / "1.0.0.yaml"
            v2_file = prompt_dir / prompt.id / "_versions" / "1.0.1.yaml"
            assert v1_file.exists(), "Version 1.0.0 file should exist"
            assert v2_file.exists(), "Version 1.0.1 file should exist"

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

    def test_sync_workflow_with_version_tracking(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test version tracking through multiple updates.

        Steps:
        1. Create prompt (v1.0.0)
        2. Update 5 times (v1.0.1 - v1.0.5)
        3. Get complete history
        4. Compare versions
        5. Verify all versions persisted
        """
        # Create initial prompt
        prompt = test_prompts[0]
        created = file_manager.create_prompt(prompt, changelog="Initial version")
        assert created.version == "1.0.0"

        # Update 5 times
        current = created
        for i in range(1, 6):
            to_update = file_manager.get_prompt(current.id)
            updated_to_update = to_update.model_copy(update={
                "template": to_update.template.model_copy(update={"content": f"Version {i}: {prompt.template.content}"})
            })
            updated = file_manager.update_prompt(updated_to_update, changelog=f"Update to version 1.0.{i}")
            assert updated.version == f"1.0.{i}"
            current = updated

        # Get complete history
        history = file_manager.get_history(prompt.id)
        assert len(history) == 6  # v1.0.0 through v1.0.5

        # Verify version sequence
        for i, version in enumerate(reversed(history)):
            assert version.version == f"1.0.{i}"

        # Compare versions
        v0 = file_manager.compare_versions(prompt.id, "1.0.0", "1.0.1")
        assert v0["versions"]["from"] == "1.0.0"
        assert v0["versions"]["to"] == "1.0.1"
        assert "checksums_differ" in v0

    def test_sync_workflow_rapid_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test rapid successive operations for stress testing.

        Tests:
        - Rapid create (100 prompts in <5s)
        - Rapid render (100 renders in <5s)
        - Rapid list (100 lists in <2s)
        """
        # Rapid create
        start = time.perf_counter()
        created_ids = []
        for i in range(100):
            prompt = Prompt(
                id=f"rapid_test_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            created = file_manager.create_prompt(prompt, changelog=f"Rapid {i}")
            created_ids.append(created.id)
        create_time = time.perf_counter() - start
        assert create_time < 5.0, f"100 creates should complete in <5s, took {create_time:.2f}s"
        assert len(created_ids) == 100

        # Rapid render
        start = time.perf_counter()
        for prompt_id in created_ids:
            result = file_manager.render(prompt_id, sample_variables)
            assert isinstance(result, str)
        render_time = time.perf_counter() - start
        assert render_time < 5.0, f"100 renders should complete in <5s, took {render_time:.2f}s"

        # Rapid list
        start = time.perf_counter()
        for _ in range(100):
            prompts = file_manager.list_prompts()
            assert len(prompts) >= 100
        list_time = time.perf_counter() - start
        assert list_time < 2.0, f"100 lists should complete in <2s, took {list_time:.2f}s"

    def test_sync_workflow_large_prompts(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test handling of large prompts (10KB+ templates).

        Verifies:
        - Large templates persist correctly
        - Large renders complete successfully
        - Updates handle large content
        """
        # Get large template
        large_prompt = test_prompts[-1]  # large_template
        assert len(large_prompt.template.content) > 8000

        # Create large prompt
        created = file_manager.create_prompt(large_prompt, changelog="Large prompt")
        assert created.id == large_prompt.id

        # Render with variables
        start = time.perf_counter()
        result = file_manager.render(large_prompt.id, {"name": "A" * 1000})
        render_time = time.perf_counter() - start
        assert len(result) > 50000
        assert render_time < 3.0, f"Large render should complete in <3s, took {render_time*1000:.0f}ms"

        # Update to even larger content
        to_update = file_manager.get_prompt(large_prompt.id)
        updated_to_update = to_update.model_copy(update={
            "template": to_update.template.model_copy(update={"content": large_prompt.template.content * 2})
        })
        updated = file_manager.update_prompt(updated_to_update, changelog="Made even larger")
        assert len(updated.template.content) > 16000  # Doubled ~9KB = ~18KB

    def test_sync_workflow_complex_templates(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Test complex templates with conditionals and iterations.

        Tests templates with:
        - Conditionals (#if)
        - Array iterations (#each)
        - Variable substitution
        """
        # Get complex template
        complex_prompt = test_prompts[-2]  # complex_template
        assert "{{#if" in complex_prompt.template.content
        assert "{{#each" in complex_prompt.template.content

        # Create and render
        created = file_manager.create_prompt(complex_prompt, changelog="Complex template")
        result = file_manager.render(created.id, sample_variables)

        # Verify output contains expected content
        assert "Test Header" in result
        assert "Test Footer" in result
        assert "Details:" in result
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result

        # Test with include_details=False
        result_no_details = file_manager.render(
            created.id,
            {**sample_variables, "include_details": False}
        )
        assert "Details:" not in result_no_details
        assert "Item 1" not in result_no_details

    def test_sync_workflow_persistence_across_instances(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        file_registry: PromptRegistry,
        file_version_store: VersionStore,
    ) -> None:
        """
        Test that data persists across manager instances.

        Verifies:
        - Created prompts survive manager recreation
        - Version history persists
        - Storage state is consistent
        """
        # Create prompts with first manager
        for prompt in test_prompts[:5]:
            file_manager.create_prompt(prompt, changelog="Initial")

        # Create new manager instance with same storage
        new_manager = PromptManager(
            registry=file_registry,
            version_store=file_version_store,
        )

        # Verify prompts exist
        prompts = new_manager.list_prompts()
        assert len(prompts) == 5

        # Verify can retrieve each prompt
        for prompt in test_prompts[:5]:
            retrieved = new_manager.get_prompt(prompt.id)
            assert retrieved.id == prompt.id

    def test_sync_workflow_error_recovery(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test that manager remains functional after errors.

        Tests:
        - PromptNotFoundError recovery
        - Continued operations after error
        - Manager state integrity
        """
        # Create a prompt
        prompt = test_prompts[0]
        created = file_manager.create_prompt(prompt, changelog="Initial")

        # Trigger PromptNotFoundError
        with pytest.raises(PromptNotFoundError):
            file_manager.get_prompt("nonexistent_prompt")

        # Verify manager still works
        retrieved = file_manager.get_prompt(created.id)
        assert retrieved.id == created.id

        # Create another prompt
        another = file_manager.create_prompt(test_prompts[1], changelog="After error")
        assert another.id == test_prompts[1].id

        # List should show both
        prompts = file_manager.list_prompts()
        assert len(prompts) == 2

    def test_sync_workflow_with_metadata_search(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test workflow with metadata-based search.

        Verifies:
        - Search by tags
        - Search by format
        - Search returns correct prompts
        """
        # Create test prompts (include complex_template at index 8)
        for prompt in test_prompts[:9]:  # Include text, chat, and complex prompts
            file_manager.create_prompt(prompt, changelog="Initial")

        # Search by tag
        integration_prompts = file_manager.list_prompts(tags=["integration"])
        assert len(integration_prompts) >= 9

        # Search by format
        text_prompts = file_manager.list_prompts(format=PromptFormat.TEXT)
        chat_prompts = file_manager.list_prompts(format=PromptFormat.CHAT)
        assert len(text_prompts) == 6  # 5 simple + 1 complex
        assert len(chat_prompts) == 3

        # Search by multiple tags
        complex_prompts = file_manager.list_prompts(tags=["integration", "complex"])
        assert len(complex_prompts) >= 1
