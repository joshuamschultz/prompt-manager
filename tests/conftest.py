"""Pytest configuration and fixtures for prompt-manager tests."""

from pathlib import Path
from typing import Any

import pytest

from prompt_manager.core.manager import PromptManager
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
from prompt_manager.observability.logging import LoggingObserver
from prompt_manager.observability.metrics import MetricsCollector
from prompt_manager.storage.memory import InMemoryStorage
from prompt_manager.versioning.store import VersionStore


@pytest.fixture
def storage() -> InMemoryStorage:
    """Create in-memory storage for testing."""
    return InMemoryStorage()


@pytest.fixture
def registry(storage: InMemoryStorage) -> PromptRegistry:
    """Create prompt registry for testing."""
    return PromptRegistry(storage=storage)


@pytest.fixture
def version_store(tmp_path: Path) -> VersionStore:
    """Create version store with temporary storage."""
    return VersionStore(storage_path=tmp_path / "versions")


@pytest.fixture
def metrics_collector() -> MetricsCollector:
    """Create metrics collector for testing."""
    return MetricsCollector()


@pytest.fixture
def logging_observer() -> LoggingObserver:
    """Create logging observer for testing."""
    return LoggingObserver()


@pytest.fixture
def manager(
    registry: PromptRegistry,
    version_store: VersionStore,
    metrics_collector: MetricsCollector,
) -> PromptManager:
    """Create prompt manager with all components."""
    return PromptManager(
        registry=registry,
        version_store=version_store,
        metrics=metrics_collector,
    )


@pytest.fixture
def simple_prompt() -> Prompt:
    """Create a simple text prompt for testing."""
    return Prompt(
        id="test_greeting",
        version="1.0.0",
        format=PromptFormat.TEXT,
        status=PromptStatus.ACTIVE,
        template=PromptTemplate(
            content="Hello {{name}}! Welcome to {{service}}.",
            variables=["name", "service"],
        ),
        metadata=PromptMetadata(
            author="Test Author",
            description="Simple greeting prompt",
            tags=["test", "greeting"],
            category="testing",
        ),
    )


@pytest.fixture
def chat_prompt() -> Prompt:
    """Create a chat prompt for testing."""
    return Prompt(
        id="test_chat",
        version="1.0.0",
        format=PromptFormat.CHAT,
        status=PromptStatus.ACTIVE,
        chat_template=ChatPromptTemplate(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="You are a helpful assistant for {{company}}.",
                ),
                Message(
                    role=Role.USER,
                    content="{{user_query}}",
                ),
            ],
            variables=["company", "user_query"],
        ),
        metadata=PromptMetadata(
            author="Test Author",
            description="Test chat prompt",
            tags=["test", "chat"],
        ),
    )


@pytest.fixture
def sample_variables() -> dict[str, Any]:
    """Sample variables for rendering."""
    return {
        "name": "Alice",
        "service": "Prompt Manager",
        "company": "Acme Corp",
        "user_query": "How can I help you?",
    }


@pytest.fixture
def yaml_content() -> str:
    """Sample YAML content for testing."""
    return """
version: "1.0.0"
metadata:
  description: "Test prompts"
  author: "Test Suite"
prompts:
  - id: yaml_test
    version: "1.0.0"
    format: text
    status: active
    template:
      content: "Test {{variable}}"
      variables:
        - variable
    metadata:
      author: Test
      tags:
        - yaml
        - test
"""


@pytest.fixture
def tmp_yaml_file(tmp_path: Path, yaml_content: str) -> Path:
    """Create temporary YAML file for testing."""
    yaml_file = tmp_path / "test_prompts.yaml"
    yaml_file.write_text(yaml_content)
    return yaml_file
