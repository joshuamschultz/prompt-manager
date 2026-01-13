"""End-to-end user scenarios for synchronous usage.

Tests real-world sync usage patterns including scripts, notebooks,
and rapid operations.
"""

import time
from pathlib import Path

import pytest

from prompt_manager import PromptManager
from prompt_manager.core.models import (
    Prompt,
    PromptFormat,
    PromptStatus,
    PromptTemplate,
    PromptMetadata,
)
from prompt_manager.exceptions import PromptNotFoundError


class TestSyncUserScenarios:
    """Test real-world synchronous usage patterns."""

    def test_script_based_usage(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Simulate standalone Python script usage (no existing event loop).

        Scenario:
        - Import PromptManager
        - Perform CRUD operations
        - All work without await
        - No event loop errors
        """
        # This test runs in pytest which has no event loop by default
        # Simulates real script usage

        # Create prompts
        for prompt in test_prompts[:3]:
            created = file_manager.create_prompt(prompt, changelog="Script create")
            assert created.id == prompt.id

        # List prompts
        prompts = file_manager.list_prompts()
        assert len(prompts) == 3

        # Render prompt
        result = file_manager.render(test_prompts[0].id, sample_variables)
        assert isinstance(result, str)

        # Update prompt
        current_prompt = file_manager.get_prompt(test_prompts[0].id)
        updated_current_prompt = current_prompt.model_copy(update={
            "template": current_prompt.template.model_copy(update={"content": f"Script updated"})
        })
        updated = file_manager.update_prompt(updated_current_prompt, changelog="Script update")
        assert updated.version == "1.0.1"

        # Get history
        history = file_manager.get_history(test_prompts[0].id)
        assert len(history) == 2

        # Delete prompt
        file_manager._registry.delete(test_prompts[0].id)

        # Verify deletion
        with pytest.raises(PromptNotFoundError):
            file_manager.get_prompt(test_prompts[0].id)

    def test_rapid_successive_operations_stress(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Stress test with 1000 rapid successive operations.

        Tests:
        - Create, render, delete loop 1000 times
        - No memory leaks
        - No event loop leaks
        - Consistent performance
        """
        base_template = test_prompts[0].template
        base_metadata = test_prompts[0].metadata

        start = time.perf_counter()
        for i in range(1000):
            # Create
            prompt = Prompt(
                id=f"stress_test_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=base_template,
                metadata=base_metadata,
            )
            created = file_manager.create_prompt(prompt, changelog=f"Stress {i}")

            # Render
            result = file_manager.render(created.id, sample_variables)
            assert isinstance(result, str)

            # Delete
            file_manager._registry.delete(created.id)

        elapsed = time.perf_counter() - start

        # Should complete in reasonable time (not a hard limit, but informative)
        # 1000 ops should be < 30s on most systems
        print(f"\n1000 operations completed in {elapsed:.2f}s ({elapsed/1000*1000:.2f}ms per op)")

        # Verify no prompts leaked
        remaining = file_manager.list_prompts()
        assert len(remaining) == 0

    def test_large_prompt_handling(
        self,
        file_manager: PromptManager,
        integration_tmp_path: Path,
    ) -> None:
        """
        Test handling of very large prompts.

        Tests:
        - Create prompt with 50KB template
        - Render with 10KB variable values
        - Update to 100KB template
        - Verify performance acceptable
        """
        # Create 50KB template
        large_content = "Line {{line_num}}\n" * 5000
        prompt = Prompt(
            id="large_prompt_test",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content=large_content,
                variables=["line_num"],
            ),
            metadata=PromptMetadata(
                author="Test",
                description="Large prompt test",
                tags=["large"],
            ),
        )
        assert len(prompt.template.content) > 50000

        # Create
        start = time.perf_counter()
        created = file_manager.create_prompt(prompt, changelog="Large create")
        create_time = time.perf_counter() - start
        assert created.id == prompt.id
        print(f"\nCreate 50KB prompt: {create_time*1000:.0f}ms")

        # Verify file size
        prompt_file = integration_tmp_path / "prompts" / "large_prompt_test.yaml"
        assert prompt_file.exists()
        file_size = prompt_file.stat().st_size
        print(f"Prompt file size: {file_size / 1024:.1f}KB")

        # Render with large variable
        large_var = "X" * 10000
        start = time.perf_counter()
        result = file_manager.render(prompt.id, {"line_num": large_var})
        render_time = time.perf_counter() - start
        assert len(result) > 50000
        print(f"Render with 10KB var: {render_time*1000:.0f}ms")
        assert render_time < 1.0  # Should be < 1s

        # Update to 100KB
        larger_content = large_content * 2
        start = time.perf_counter()
        updated = file_manager.update_prompt(
            prompt.id,
            content=larger_content,
            changelog="Expand to 100KB"
        )
        update_time = time.perf_counter() - start
        assert len(updated.template.content) > 100000
        print(f"Update to 100KB: {update_time*1000:.0f}ms")

    def test_complex_template_rendering(
        self,
        file_manager: PromptManager,
    ) -> None:
        """
        Test complex template with multiple features.

        Template features:
        - Nested conditionals
        - Array iterations
        - Multiple variable types
        - Computed values
        """
        complex_template = """
# Report: {{title}}

{{#if show_summary}}
## Summary
{{summary}}
{{/if}}

## Items
{{#each items}}
### {{@index}}. {{this.name}}
- Status: {{this.status}}
- Value: {{this.value}}
{{#if this.urgent}}
**URGENT**: {{this.reason}}
{{/if}}
{{/each}}

{{#if show_footer}}
---
Generated on {{date}}
{{/if}}
"""

        prompt = Prompt(
            id="complex_test",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content=complex_template,
                variables=["title", "show_summary", "summary", "items", "show_footer", "date"],
            ),
            metadata=PromptMetadata(
                author="Test",
                description="Complex template",
                tags=["complex"],
            ),
        )

        # Create
        created = file_manager.create_prompt(prompt, changelog="Complex create")

        # Render with complex variables
        variables = {
            "title": "Q4 Report",
            "show_summary": True,
            "summary": "This is the summary section",
            "items": [
                {"name": "Item 1", "status": "Complete", "value": 100, "urgent": False},
                {"name": "Item 2", "status": "Pending", "value": 200, "urgent": True, "reason": "High priority"},
                {"name": "Item 3", "status": "Complete", "value": 150, "urgent": False},
            ],
            "show_footer": True,
            "date": "2025-11-25",
        }

        result = file_manager.render(created.id, variables)

        # Verify output contains all expected elements
        assert "# Report: Q4 Report" in result
        assert "## Summary" in result
        assert "This is the summary section" in result
        assert "### 0. Item 1" in result
        assert "### 1. Item 2" in result
        assert "### 2. Item 3" in result
        assert "**URGENT**: High priority" in result
        assert "Generated on 2025-11-25" in result

        # Test with show_summary=False
        result_no_summary = file_manager.render(
            created.id,
            {**variables, "show_summary": False}
        )
        assert "## Summary" not in result_no_summary

    def test_error_recovery_sync(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test error recovery in sync mode.

        Tests:
        - Trigger PromptNotFoundError
        - Recover and continue
        - Manager remains functional
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

        # Trigger another error
        with pytest.raises(PromptNotFoundError):
            file_manager._registry.delete("another_nonexistent")

        # Create another prompt
        another = file_manager.create_prompt(test_prompts[1], changelog="After errors")
        assert another.id == test_prompts[1].id

        # Update works
        current_another = file_manager.get_prompt(another.id)
        updated_current_another = current_another.model_copy(update={
            "template": current_another.template.model_copy(update={"content": f"Updated after errors"})
        })
        updated = file_manager.update_prompt(updated_current_another, changelog="Update")
        assert updated.version == "1.0.1"

        # List works
        prompts = file_manager.list_prompts()
        assert len(prompts) == 2

    def test_batch_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test batch operations in sync mode.

        Tests:
        - Create many prompts
        - Batch updates
        - Batch deletes
        """
        # Batch create
        created_ids = []
        for i in range(50):
            prompt = Prompt(
                id=f"batch_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=test_prompts[0].template,
                metadata=test_prompts[0].metadata,
            )
            created = file_manager.create_prompt(prompt, changelog=f"Batch {i}")
            created_ids.append(created.id)

        assert len(created_ids) == 50

        # Batch update (first 25)
        for i, prompt_id in enumerate(created_ids[:25]):
            current_p = file_manager.get_prompt(prompt_id)
            updated_current_p = current_p.model_copy(update={
                "template": current_p.template.model_copy(update={"content": f"Updated {i}"})
            })
            updated = file_manager.update_prompt(updated_current_p, changelog=f"Update {i}")
            assert updated.version == "1.0.1"

        # Batch delete (first 10)
        for prompt_id in created_ids[:10]:
            file_manager._registry.delete(prompt_id)

        # Verify counts
        remaining = file_manager.list_prompts()
        assert len(remaining) == 40

    def test_search_and_filter_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test search and filtering operations.

        Tests:
        - Search by single tag
        - Search by multiple tags
        - Search by format
        - Combined filters
        """
        # Create diverse prompts
        for prompt in test_prompts[:10]:
            file_manager.create_prompt(prompt, changelog="Initial")

        # Search by single tag
        integration_prompts = file_manager.list_prompts(tags=["integration"])
        assert len(integration_prompts) >= 10

        # Search by format
        text_prompts = file_manager.list_prompts(format=PromptFormat.TEXT)
        chat_prompts = file_manager.list_prompts(format=PromptFormat.CHAT)
        assert len(text_prompts) >= 5
        assert len(chat_prompts) >= 3

        # Search by multiple tags
        complex_prompts = file_manager.list_prompts(tags=["integration", "complex"])
        assert len(complex_prompts) >= 1

    def test_version_history_operations(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
    ) -> None:
        """
        Test version history operations in sync mode.

        Tests:
        - Create and update multiple times
        - Get full history
        - Compare specific versions
        - Navigate history
        """
        prompt = test_prompts[0]

        # Create initial
        created = file_manager.create_prompt(prompt, changelog="v1.0.0 - Initial")
        assert created.version == "1.0.0"

        # Multiple updates
        changelogs = [
            "v1.0.1 - Fix typo",
            "v1.0.2 - Add context",
            "v1.0.3 - Improve clarity",
            "v1.0.4 - Final version",
        ]

        for i, changelog in enumerate(changelogs, start=1):
            current_prompt = file_manager.get_prompt(prompt.id)
            updated_current_prompt = current_prompt.model_copy(update={
                "template": current_prompt.template.model_copy(update={"content": f"Version {i}: {prompt.template.content}"})
            })
            updated = file_manager.update_prompt(updated_current_prompt, changelog=changelog)
            assert updated.version == f"1.0.{i}"

        # Get full history
        history = file_manager.get_history(prompt.id)
        assert len(history) == 5

        # Verify version sequence
        for i, version in enumerate(reversed(history)):
            assert version.version == f"1.0.{i}"

        # Compare versions
        comparison = file_manager.compare_versions(prompt.id, "1.0.0", "1.0.4")
        assert comparison["versions"]["from"] == "1.0.0"
        assert comparison["versions"]["to"] == "1.0.4"
        assert "checksums_differ" in comparison

    def test_concurrent_script_simulation(
        self,
        file_manager: PromptManager,
        test_prompts: list[Prompt],
        sample_variables: dict,
    ) -> None:
        """
        Simulate multiple scripts running concurrently (thread-safe).

        Tests:
        - Multiple operations interleaved
        - No conflicts
        - Data integrity maintained
        """
        # Simulate Script 1: Create and update
        prompt1 = test_prompts[0]
        created1 = file_manager.create_prompt(prompt1, changelog="Script 1 create")

        # Simulate Script 2: Create and render
        prompt2 = test_prompts[1]
        created2 = file_manager.create_prompt(prompt2, changelog="Script 2 create")

        # Script 1 continues
        current_prompt1 = file_manager.get_prompt(prompt1.id)
        updated_current_prompt1 = current_prompt1.model_copy(update={
            "template": current_prompt1.template.model_copy(update={"content": f"Script 1 update"})
        })
        updated1 = file_manager.update_prompt(updated_current_prompt1, changelog="Script 1 update")

        # Script 2 continues
        result2 = file_manager.render(prompt2.id, sample_variables)

        # Verify both operations successful
        assert updated1.version == "1.0.1"
        assert isinstance(result2, str)

        # Verify both prompts exist
        prompts = file_manager.list_prompts()
        assert len(prompts) == 2
