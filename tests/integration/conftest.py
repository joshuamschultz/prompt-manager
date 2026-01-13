"""Shared fixtures for integration tests."""

from pathlib import Path
from typing import Any

import pytest

from prompt_manager import PromptManager
from prompt_manager.core.models import (
    ChatPromptTemplate,
    Message,
    Prompt,
    PromptFormat,
    PromptMetadata,
    PromptStatus,
    PromptTemplate,
    Role,
)
from prompt_manager.core.registry import PromptRegistry
from prompt_manager.storage.file import FileSystemStorage
from prompt_manager.versioning.store import VersionStore


@pytest.fixture
def integration_tmp_path(tmp_path: Path) -> Path:
    """Temporary directory for integration tests."""
    integration_dir = tmp_path / "integration"
    integration_dir.mkdir(exist_ok=True)
    return integration_dir


@pytest.fixture
def file_storage(integration_tmp_path: Path) -> FileSystemStorage:
    """FileSystemStorage for integration tests."""
    storage_path = integration_tmp_path / "prompts"
    return FileSystemStorage(storage_path)


@pytest.fixture
def file_registry(file_storage: FileSystemStorage) -> PromptRegistry:
    """PromptRegistry with FileSystemStorage."""
    return PromptRegistry(storage=file_storage)


@pytest.fixture
def file_version_store(integration_tmp_path: Path) -> VersionStore:
    """VersionStore with file-based storage."""
    version_path = integration_tmp_path / "versions"
    return VersionStore(storage_path=version_path)


@pytest.fixture
def file_manager(
    file_registry: PromptRegistry,
    file_version_store: VersionStore,
) -> PromptManager:
    """PromptManager with FileSystemStorage (real persistence)."""
    return PromptManager(
        registry=file_registry,
        version_store=file_version_store,
    )


@pytest.fixture
def test_prompts() -> list[Prompt]:
    """Collection of test prompts for integration testing."""
    prompts = []

    # Simple text prompts
    for i in range(5):
        prompts.append(
            Prompt(
                id=f"text_prompt_{i}",
                version="1.0.0",
                format=PromptFormat.TEXT,
                status=PromptStatus.ACTIVE,
                template=PromptTemplate(
                    content=f"Prompt {i}: Hello {{{{name}}}}!",
                    variables=["name"],
                ),
                metadata=PromptMetadata(
                    author="Integration Test",
                    description=f"Test prompt {i}",
                    tags=["integration", "test", f"batch_{i // 2}"],
                ),
            )
        )

    # Chat prompts
    for i in range(3):
        prompts.append(
            Prompt(
                id=f"chat_prompt_{i}",
                version="1.0.0",
                format=PromptFormat.CHAT,
                status=PromptStatus.ACTIVE,
                chat_template=ChatPromptTemplate(
                    messages=[
                        Message(
                            role=Role.SYSTEM,
                            content=f"You are assistant {i}.",
                        ),
                        Message(
                            role=Role.USER,
                            content="{{user_query}}",
                        ),
                    ],
                    variables=["user_query"],
                ),
                metadata=PromptMetadata(
                    author="Integration Test",
                    description=f"Chat prompt {i}",
                    tags=["integration", "chat"],
                ),
            )
        )

    # Complex template
    prompts.append(
        Prompt(
            id="complex_template",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content="""Header: {{header}}
{{#if include_details}}
Details:
{{#each items}}
- {{this}}
{{/each}}
{{/if}}
Footer: {{footer}}""",
                variables=["header", "include_details", "items", "footer"],
            ),
            metadata=PromptMetadata(
                author="Integration Test",
                description="Complex template with conditionals",
                tags=["integration", "complex"],
            ),
        )
    )

    # Large template (10KB+)
    large_content = "Large template:\n" + ("{{name}}\n" * 1000)
    prompts.append(
        Prompt(
            id="large_template",
            version="1.0.0",
            format=PromptFormat.TEXT,
            status=PromptStatus.ACTIVE,
            template=PromptTemplate(
                content=large_content,
                variables=["name"],
            ),
            metadata=PromptMetadata(
                author="Integration Test",
                description="Large template for stress testing",
                tags=["integration", "large"],
            ),
        )
    )

    return prompts


@pytest.fixture
def sample_variables() -> dict[str, Any]:
    """Sample variables for rendering."""
    return {
        "name": "Alice",
        "user_query": "How can I help you?",
        "header": "Test Header",
        "footer": "Test Footer",
        "include_details": True,
        "items": ["Item 1", "Item 2", "Item 3"],
    }
